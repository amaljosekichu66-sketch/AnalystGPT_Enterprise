"""
Domain user and authentication management service for AnalystGPT Enterprise.

Responsibilities
----------------
- Coordinate user registration and secure credential persistence.
- Execute credential verification and account status enforcement.
- Manage access token issuance, verification, and logout revocation.
- Prevent timing attacks and user enumeration vulnerabilities.
"""

from __future__ import annotations

import hashlib
import secrets
import threading
from collections.abc import Callable

from src.core import config
from src.core.logger import logger
from src.identity.audit import AuditService, get_audit_service
from src.identity.context import UserContext
from src.identity.exceptions import (
    AccountLockedError,
    AdminOperationError,
    AuthenticationError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserDisabledError,
    UserNotFoundError,
)
from src.identity.interfaces import (
    IPasswordHasher,
    ITokenRevocationService,
    ITokenService,
    IUserRepository,
)
from src.identity.login_throttle import LoginThrottle
from src.identity.models import (
    AdminUserUpdate,
    AuditEventType,
    PasswordChange,
    User,
    UserCreate,
    UserLogin,
    UserRegistration,
    UserRole,
    UserStatus,
    UserUpdate,
)
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.password_policy import WeakPasswordError, validate_password_strength
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService

#: Serializes every "is this the last active admin?" check together with the
#: write it guards (SEC-21). Two admins demoting each other concurrently could
#: both pass the check and leave no administrator. The shipped image runs one
#: API process; several processes would need a database-level guard as well.
_ADMIN_GUARD_LOCK = threading.RLock()

#: Returned for any registration conflict; deliberately does not say which field.
DUPLICATE_ACCOUNT_MESSAGE = "An account with this username or email address already exists."

#: Longest identifier echoed into a log line (L2); longer values are cut.
_LOGGED_IDENTIFIER_MAX = 64


def _log_safe(value: str) -> str:
    """Neutralise CR/LF and bound length so a login identifier cannot forge log lines (L2)."""
    cleaned = value.replace("\r", "\\r").replace("\n", "\\n")
    if len(cleaned) > _LOGGED_IDENTIFIER_MAX:
        cleaned = cleaned[:_LOGGED_IDENTIFIER_MAX] + "..."
    return cleaned


def _mask_email(email: str) -> str:
    """Keep the domain and the first character only: 'a***@example.com' (I4)."""
    local, _, domain = email.partition("@")
    return f"{local[:1]}***@{domain}" if domain else "***"


class UserService:
    """
    Core application service coordinating user authentication and identity workflows.
    """

    #: Role assigned to every self-registered account. Not caller-selectable.
    #: Read-only (M10): ANALYST granted upload, pipeline and LLM access to anyone
    #: who could reach the sign-up form. An admin promotes accounts as needed.
    SELF_REGISTRATION_ROLE = UserRole.VIEWER

    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher | None = None,
        token_service: ITokenService | None = None,
        revocation_service: ITokenRevocationService | None = None,
        audit_service: AuditService | None = None,
        login_throttle: LoginThrottle | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher if password_hasher is not None else PBKDF2PasswordHasher()
        self._token_service = token_service if token_service is not None else TokenService()
        self._revocation_service = revocation_service if revocation_service is not None else TokenRevocationService()
        self._audit_service = audit_service if audit_service is not None else get_audit_service()
        self._login_throttle = login_throttle if login_throttle is not None else LoginThrottle()
        # Verified against when the identifier matches no account, so that path
        # costs the same PBKDF2 work as a real password check (M1). It must be a
        # real hash from this hasher: the old constant had an undecodable salt,
        # so verify() returned in microseconds and exposed which accounts exist.
        self._dummy_hash = self._password_hasher.hash(secrets.token_urlsafe(32))

    # ==========================================================
    # User Registration
    # ==========================================================

    def register_self(self, registration: UserRegistration) -> User:
        """
        Register an account through the public, unauthenticated flow.

        The role is always `SELF_REGISTRATION_ROLE`; the registration payload
        has no way to express another one. The password must pass the
        acceptance policy (SEC-08).
        """
        validate_password_strength(registration.password, registration.username, registration.email)
        return self.register_user(
            UserCreate(
                username=registration.username,
                email=registration.email,
                password=registration.password,
                role=self.SELF_REGISTRATION_ROLE,
            )
        )

    def register_user(self, user_create: UserCreate) -> User:
        """
        Register a new user account with securely hashed credentials.

        Trusted entry point: honours `user_create.role` as given. Public
        registration must go through `register_self`.

        Parameters
        ----------
        user_create:
            Validated user registration payload.

        Returns
        -------
        User
            Newly created domain user entity.

        Raises
        ------
        UserAlreadyExistsError
            If username or email is already registered.
        """
        logger.info(
            "Registering user '%s' (%s) with role '%s'...",
            user_create.username,
            _mask_email(user_create.email),
            user_create.role.value,
        )

        # One generic message for both cases (SEC-15): naming which of the two
        # already exists told an anonymous caller whether a given username or
        # email address has an account.
        if (
            self._user_repository.get_by_username(user_create.username) is not None
            or self._user_repository.get_by_email(user_create.email) is not None
        ):
            logger.info("Registration rejected: username or email already in use.")
            raise UserAlreadyExistsError(DUPLICATE_ACCOUNT_MESSAGE)

        hashed_password = self._password_hasher.hash(user_create.password)

        created_user = self._user_repository.create(
            user_create=user_create,
            hashed_password=hashed_password,
        )

        logger.info(
            "User '%s' registered successfully (ID=%d).",
            created_user.username,
            created_user.id,
        )

        self._audit_service.record_event(
            event_type=AuditEventType.USER_REGISTERED,
            action="USER_REGISTRATION",
            actor_id=created_user.id,
            actor_username=created_user.username,
            target_id=created_user.id,
            target_resource="USER",
            outcome="SUCCESS",
            details={
                "username": created_user.username,
                "email": _mask_email(created_user.email),
                "role": created_user.role.value,
            },
        )

        return created_user

    # ==========================================================
    # Authentication & Login
    # ==========================================================

    def authenticate_user(
        self,
        username_or_email: str,
        password: str,
        client: str = "",
    ) -> User:
        """
        Authenticate user credentials and enforce account lifecycle status.

        Parameters
        ----------
        username_or_email:
            Supplied username or email address.
        password:
            Plaintext password.
        client:
            Address the attempt came from; lockouts are per account and source.

        Returns
        -------
        User
            Authenticated active user entity.

        Raises
        ------
        InvalidCredentialsError
            If username/password is invalid (constant-time evaluation).
        UserDisabledError
            If user account is suspended or inactive.
        """
        clean_identifier = username_or_email.strip()

        if "@" in clean_identifier:
            user = self._user_repository.get_by_email(clean_identifier)
        else:
            user = self._user_repository.get_by_username(clean_identifier)

        # Username and email of one account share a counter (M12).
        account = f"user:{user.id}" if user is not None else "id:" + LoginThrottle.normalise(clean_identifier)

        # Locked accounts are refused before the password is checked, so a
        # correct guess during the lockout is indistinguishable from a wrong one.
        retry_after = self._login_throttle.retry_after(account, client)
        if retry_after:
            self._audit_service.record_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                action="USER_LOGIN",
                actor_username=_log_safe(clean_identifier),
                target_resource="AUTH",
                outcome="DENIED",
                details={"reason": "LOCKED_OUT", "retry_after_seconds": retry_after},
            )
            raise AccountLockedError("Too many failed login attempts. Try again later.", retry_after)

        if user is None:
            # Perform dummy verification to neutralize timing attack enumeration
            self._password_hasher.verify(password, self._dummy_hash)
            # The identifier may be a mistyped password: log only a digest.
            logger.warning(
                "Authentication failed: unknown identifier (sha256:%s).",
                hashlib.sha256(clean_identifier.encode("utf-8")).hexdigest()[:12],
            )
            self._audit_service.record_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                action="USER_LOGIN",
                actor_username="sha256:" + hashlib.sha256(clean_identifier.encode("utf-8")).hexdigest()[:12],
                target_resource="AUTH",
                outcome="FAILED",
                details={"reason": "USER_NOT_FOUND"},
            )
            self._register_failed_login(account, client, clean_identifier)
            raise InvalidCredentialsError("Invalid username or password.")

        if not self._password_hasher.verify(password, user.hashed_password):
            logger.warning(
                "Authentication failed: Incorrect password for user '%s'.",
                user.username,
            )
            self._audit_service.record_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                action="USER_LOGIN",
                actor_id=user.id,
                actor_username=user.username,
                target_id=user.id,
                target_resource="AUTH",
                outcome="FAILED",
                details={"reason": "INVALID_PASSWORD"},
            )
            self._register_failed_login(account, client, clean_identifier)
            raise InvalidCredentialsError("Invalid username or password.")

        if not user.is_active:
            logger.warning(
                "Authentication rejected: User account '%s' is %s.",
                user.username,
                user.status.value,
            )
            self._audit_service.record_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                action="USER_LOGIN",
                actor_id=user.id,
                actor_username=user.username,
                target_id=user.id,
                target_resource="AUTH",
                outcome="DENIED",
                details={"reason": f"ACCOUNT_{user.status.value}"},
            )
            # Same 401 as a wrong password (L1): a distinct 403 here confirmed
            # that the password was correct and revealed the account's status.
            raise InvalidCredentialsError("Invalid username or password.")

        self._login_throttle.record_success(account, client)

        logger.info(
            "User '%s' (ID=%d, Role=%s) authenticated successfully.",
            user.username,
            user.id,
            user.role.value,
        )

        self._audit_service.record_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            action="USER_LOGIN",
            actor_id=user.id,
            actor_username=user.username,
            target_id=user.id,
            target_resource="AUTH",
            outcome="SUCCESS",
            details={"role": user.role.value},
        )

        return user

    def _register_failed_login(self, account: str, client: str, identifier: str) -> None:
        lockout = self._login_throttle.record_failure(account, client)
        if lockout:
            logger.warning(
                "SECURITY_ALERT | Login identifier locked for %ds after repeated failures.",
                lockout,
            )
            self._audit_service.record_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                action="ACCOUNT_LOCKOUT",
                actor_username=_log_safe(identifier),
                target_resource="AUTH",
                outcome="DENIED",
                details={"reason": "LOCKOUT_TRIGGERED", "lockout_seconds": lockout},
            )

    def login(self, user_login: UserLogin, client: str = "") -> tuple[User, str, int]:
        """
        Execute login workflow and issue a cryptographically signed access token.

        Parameters
        ----------
        user_login:
            Validated login credentials.
        client:
            Address the attempt came from (see `rate_limit.client_address`).

        Returns
        -------
        tuple[User, str, int]
            (Authenticated User, Signed Access Token, Expires in Seconds)
        """
        user = self.authenticate_user(
            username_or_email=user_login.username,
            password=user_login.password,
            client=client,
        )

        token = self._token_service.create_access_token(user)
        expires_in = config.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60

        return user, token, expires_in

    # ==========================================================
    # Token Resolution & Current User
    # ==========================================================

    def get_current_user_from_token(self, token: str) -> User:
        """
        Validate an access token, enforce revocation, and retrieve active domain User.

        Parameters
        ----------
        token:
            Signed JWT string.

        Returns
        -------
        User
            Active authenticated domain user.

        Raises
        ------
        InvalidTokenError
            If token is invalid, revoked, expired, or user nonexistent.
        UserDisabledError
            If user account is inactive or suspended.
        """
        claims = self._token_service.verify_access_token(token)

        if self._revocation_service.is_revoked(claims["jti"]):
            raise InvalidTokenError("Authentication token has been revoked.")

        try:
            user_id = int(claims["sub"])
        except (KeyError, ValueError) as exc:
            raise InvalidTokenError("Token subject claim is invalid.") from exc

        user = self._user_repository.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError("User associated with token does not exist.")

        if not user.is_active:
            raise UserDisabledError(f"User account is {user.status.value.lower()}.")

        # Tokens issued before a password, role or status change, or before
        # "sign out everywhere", carry an older version (I2).
        if claims.get("ver", 0) != user.token_version:
            raise InvalidTokenError("Authentication token is no longer valid.")

        return user

    # ==========================================================
    # Password change & session invalidation (I2)
    # ==========================================================

    def change_password(self, user_id: int, change: PasswordChange) -> User:
        """
        Change the caller's own password after re-checking the current one.

        Every outstanding token, including the one used for this request, stops
        working; the client signs in again with the new password.
        """
        user = self.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found.")

        if not self._password_hasher.verify(change.current_password, user.hashed_password):
            self._audit_service.record_event(
                event_type=AuditEventType.USER_UPDATED,
                action="PASSWORD_CHANGE",
                actor_id=user.id,
                actor_username=user.username,
                target_id=user.id,
                target_resource="USER",
                outcome="FAILED",
                details={"reason": "CURRENT_PASSWORD_INCORRECT"},
            )
            raise WeakPasswordError("Current password is incorrect.")

        validate_password_strength(change.new_password, user.username, user.email)
        updated = self._user_repository.update(
            user.id,
            UserUpdate(email=None, password=None),
            hashed_password=self._password_hasher.hash(change.new_password),
        )
        self._user_repository.bump_token_version(user.id)

        logger.info("Password changed for user ID=%d; all sessions invalidated.", user.id)
        self._audit_service.record_event(
            event_type=AuditEventType.USER_UPDATED,
            action="PASSWORD_CHANGE",
            actor_id=user.id,
            actor_username=user.username,
            target_id=user.id,
            target_resource="USER",
            outcome="SUCCESS",
        )
        return updated

    def logout_everywhere(self, actor_context: UserContext) -> None:
        """Invalidate every outstanding token of the caller."""
        self._user_repository.bump_token_version(actor_context.user_id)
        self._audit_service.record_event(
            event_type=AuditEventType.LOGOUT,
            action="USER_LOGOUT_ALL",
            actor_id=actor_context.user_id,
            actor_username=actor_context.username,
            target_resource="AUTH",
            outcome="SUCCESS",
        )

    # ==========================================================
    # Logout
    # ==========================================================

    def logout(self, token: str | None = None, actor_context: UserContext | None = None) -> bool:
        """
        Revoke a VALID access token by its `jti` until it expires.

        Invalid, expired or foreign strings raise `InvalidTokenError` and are
        never stored (SEC-09: logout used to accept and keep any string).
        """
        if token:
            claims = self._token_service.verify_access_token(token)
            self._revocation_service.revoke(claims["jti"], int(claims["exp"]))
            logger.info("Access token successfully revoked on logout.")

        self._audit_service.record_event(
            event_type=AuditEventType.LOGOUT,
            action="USER_LOGOUT",
            actor_id=actor_context.user_id if actor_context else None,
            actor_username=actor_context.username if actor_context else None,
            target_resource="AUTH",
            outcome="SUCCESS",
        )
        return True

    # ==========================================================
    # User Lookup & Admin Management
    # ==========================================================

    def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user entity by ID.
        """
        return self._user_repository.get_by_id(user_id)

    def list_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        """
        List all users with pagination for administrative inspection.
        """
        return self._user_repository.list_all(limit=limit, offset=offset)

    def count_users(self) -> int:
        """
        Return the total number of registered users.
        """
        return self._user_repository.count()

    def _count_active_admins(self) -> int:
        """
        Count ALL active administrators (was: only within the first 10,000 users).
        """
        return self._user_repository.count_active_admins()

    def update_user_admin(
        self,
        user_id: int,
        user_update: AdminUserUpdate,
        actor_context: UserContext | None = None,
    ) -> User:
        """
        Administer user status, role, or email with last-admin safeguards.

        Parameters
        ----------
        user_id:
            Target user ID.
        user_update:
            Validated administrative update payload.
        actor_context:
            Security context of the performing administrator.

        Returns
        -------
        User
            Updated domain user entity.

        Raises
        ------
        UserNotFoundError
            If user does not exist.
        AdminOperationError
            If operation violates safety rules (e.g. removing last active admin).
        """
        target_user = self.get_user_by_id(user_id)
        if target_user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found.")

        # Last-admin protection safeguard
        is_currently_active_admin = target_user.is_admin and target_user.is_active
        demoting_role = user_update.role is not None and user_update.role != UserRole.ADMIN
        disabling_status = user_update.status is not None and user_update.status != UserStatus.ACTIVE

        repo_update = UserUpdate(
            email=user_update.email,
            role=user_update.role,
            status=user_update.status,
            password=None,
        )

        with _ADMIN_GUARD_LOCK:
            if is_currently_active_admin and (demoting_role or disabling_status):
                active_admin_count = self._count_active_admins()
                if active_admin_count <= 1:
                    logger.warning(
                        "Admin operation blocked: Cannot demote or disable last active admin '%s' (ID=%d).",
                        target_user.username,
                        target_user.id,
                    )
                    self._audit_blocked_admin_operation(actor_context, target_user, "DEMOTE_OR_DISABLE")
                    raise AdminOperationError("Cannot demote, deactivate, or suspend the last active administrator.")

            updated_user = self._user_repository.update(user_id=user_id, user_update=repo_update)

        # A demoted or suspended user must not keep acting on old tokens (I2).
        role_changed = user_update.role is not None and user_update.role != target_user.role
        status_changed = user_update.status is not None and user_update.status != target_user.status
        if role_changed or status_changed:
            self._user_repository.bump_token_version(user_id)

        # Audit events
        actor_id = actor_context.user_id if actor_context else None
        actor_name = actor_context.username if actor_context else None

        if user_update.role is not None and user_update.role != target_user.role:
            self._audit_service.record_event(
                event_type=AuditEventType.USER_ROLE_CHANGED,
                action="ADMIN_ROLE_CHANGE",
                actor_id=actor_id,
                actor_username=actor_name,
                target_id=target_user.id,
                target_resource="USER",
                outcome="SUCCESS",
                details={
                    "old_role": target_user.role.value,
                    "new_role": updated_user.role.value,
                },
            )

        if user_update.status is not None and user_update.status != target_user.status:
            self._audit_service.record_event(
                event_type=AuditEventType.USER_STATUS_CHANGED,
                action="ADMIN_STATUS_CHANGE",
                actor_id=actor_id,
                actor_username=actor_name,
                target_id=target_user.id,
                target_resource="USER",
                outcome="SUCCESS",
                details={
                    "old_status": target_user.status.value,
                    "new_status": updated_user.status.value,
                },
            )

        self._audit_service.record_event(
            event_type=AuditEventType.USER_UPDATED,
            action="ADMIN_USER_UPDATE",
            actor_id=actor_id,
            actor_username=actor_name,
            target_id=target_user.id,
            target_resource="USER",
            outcome="SUCCESS",
            details={
                "username": updated_user.username,
                "role": updated_user.role.value,
                "status": updated_user.status.value,
            },
        )

        return updated_user

    def _audit_blocked_admin_operation(self, actor_context: UserContext | None, target: User, operation: str) -> None:
        """Record a refused attempt to remove the last active administrator (L13)."""
        self._audit_service.record_event(
            event_type=AuditEventType.ADMIN_OPERATION_BLOCKED,
            action=f"LAST_ADMIN_{operation}",
            actor_id=actor_context.user_id if actor_context else None,
            actor_username=actor_context.username if actor_context else None,
            target_id=target.id,
            target_resource="USER",
            outcome="DENIED",
            details={"reason": "LAST_ACTIVE_ADMIN"},
        )

    def unlock_user(self, user_id: int, actor_context: UserContext | None = None) -> User:
        """
        Clear every login lockout for an account, from every source (M12).

        Raises
        ------
        UserNotFoundError
            If user does not exist.
        """
        target_user = self.get_user_by_id(user_id)
        if target_user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found.")

        self._login_throttle.unlock(f"user:{target_user.id}")

        logger.info("Login lockout cleared for user ID=%d.", target_user.id)
        self._audit_service.record_event(
            event_type=AuditEventType.USER_UPDATED,
            action="ADMIN_UNLOCK_USER",
            actor_id=actor_context.user_id if actor_context else None,
            actor_username=actor_context.username if actor_context else None,
            target_id=target_user.id,
            target_resource="USER",
            outcome="SUCCESS",
            details={"username": target_user.username},
        )
        return target_user

    def delete_user_admin(
        self,
        user_id: int,
        actor_context: UserContext | None = None,
        before_delete: Callable[[User], object] | None = None,
    ) -> bool:
        """
        Delete a user entity with last-admin safeguards.

        Parameters
        ----------
        user_id:
            Target user ID.
        actor_context:
            Security context of the performing administrator.

        Returns
        -------
        bool
            True if deleted.

        Raises
        ------
        UserNotFoundError
            If user does not exist.
        AdminOperationError
            If target is the last active admin.
        """
        target_user = self.get_user_by_id(user_id)
        if target_user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found.")

        with _ADMIN_GUARD_LOCK:
            if target_user.is_admin and target_user.is_active:
                active_admin_count = self._count_active_admins()
                if active_admin_count <= 1:
                    logger.warning(
                        "Admin operation blocked: Cannot delete last active admin '%s' (ID=%d).",
                        target_user.username,
                        target_user.id,
                    )
                    self._audit_blocked_admin_operation(actor_context, target_user, "DELETE")
                    raise AdminOperationError("Cannot delete the last active administrator.")

            # SEC-20: remove the account's data first (callers supply the purge),
            # so nothing is left behind ownerless if the delete succeeds.
            if before_delete is not None:
                before_delete(target_user)

            result = self._user_repository.delete(user_id)

        actor_id = actor_context.user_id if actor_context else None
        actor_name = actor_context.username if actor_context else None

        self._audit_service.record_event(
            event_type=AuditEventType.USER_DELETED,
            action="ADMIN_USER_DELETE",
            actor_id=actor_id,
            actor_username=actor_name,
            target_id=target_user.id,
            target_resource="USER",
            outcome="SUCCESS",
            details={
                "deleted_username": target_user.username,
                "deleted_role": target_user.role.value,
            },
        )

        return result
