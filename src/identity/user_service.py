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

from src.core import config
from src.core.logger import logger
from src.identity.audit import AuditService, get_audit_service
from src.identity.context import UserContext
from src.identity.exceptions import (
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
from src.identity.models import (
    AdminUserUpdate,
    AuditEventType,
    User,
    UserCreate,
    UserLogin,
    UserRole,
    UserStatus,
    UserUpdate,
)
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService

# Constant dummy hash used to neutralize timing attacks on nonexistent user logins
_DUMMY_HASH = "$pbkdf2-sha256$600000$ZHVtbXlzYWx0MTIzNDU2Nw$ZHVtbXloYXNoMTIzNDU2Nzg5MDEyMzQ1Njc4OTA="


class UserService:
    """
    Core application service coordinating user authentication and identity workflows.
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher | None = None,
        token_service: ITokenService | None = None,
        revocation_service: ITokenRevocationService | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher if password_hasher is not None else PBKDF2PasswordHasher()
        self._token_service = token_service if token_service is not None else TokenService()
        self._revocation_service = revocation_service if revocation_service is not None else TokenRevocationService()
        self._audit_service = audit_service if audit_service is not None else get_audit_service()

    # ==========================================================
    # User Registration
    # ==========================================================

    def register_user(self, user_create: UserCreate) -> User:
        """
        Register a new user account with securely hashed credentials.

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
            user_create.email,
            user_create.role.value,
        )

        if self._user_repository.get_by_username(user_create.username) is not None:
            raise UserAlreadyExistsError(f"Username '{user_create.username}' is already registered.")

        if self._user_repository.get_by_email(user_create.email) is not None:
            raise UserAlreadyExistsError(f"Email address '{user_create.email}' is already registered.")

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
                "email": created_user.email,
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
    ) -> User:
        """
        Authenticate user credentials and enforce account lifecycle status.

        Parameters
        ----------
        username_or_email:
            Supplied username or email address.
        password:
            Plaintext password.

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
        user: User | None = None

        if "@" in clean_identifier:
            user = self._user_repository.get_by_email(clean_identifier)
        else:
            user = self._user_repository.get_by_username(clean_identifier)

        if user is None:
            # Perform dummy verification to neutralize timing attack enumeration
            self._password_hasher.verify(password, _DUMMY_HASH)
            logger.warning(
                "Authentication failed: User identifier '%s' not found.",
                clean_identifier,
            )
            self._audit_service.record_event(
                event_type=AuditEventType.LOGIN_FAILURE,
                action="USER_LOGIN",
                actor_username=clean_identifier,
                target_resource="AUTH",
                outcome="FAILED",
                details={"reason": "USER_NOT_FOUND"},
            )
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
            raise UserDisabledError(f"User account is {user.status.value.lower()}.")

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

    def login(self, user_login: UserLogin) -> tuple[User, str, int]:
        """
        Execute login workflow and issue a cryptographically signed access token.

        Parameters
        ----------
        user_login:
            Validated login credentials.

        Returns
        -------
        tuple[User, str, int]
            (Authenticated User, Signed Access Token, Expires in Seconds)
        """
        user = self.authenticate_user(
            username_or_email=user_login.username,
            password=user_login.password,
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
        if self._revocation_service.is_revoked(token):
            raise InvalidTokenError("Authentication token has been revoked.")

        claims = self._token_service.verify_access_token(token)

        try:
            user_id = int(claims["sub"])
        except (KeyError, ValueError) as exc:
            raise InvalidTokenError("Token subject claim is invalid.") from exc

        user = self._user_repository.get_by_id(user_id)
        if user is None:
            raise InvalidTokenError("User associated with token does not exist.")

        if not user.is_active:
            raise UserDisabledError(f"User account is {user.status.value.lower()}.")

        return user

    # ==========================================================
    # Logout
    # ==========================================================

    def logout(self, token: str | None = None, actor_context: UserContext | None = None) -> bool:
        """
        Invalidate the given access token in the revocation registry.
        """
        if token:
            self._revocation_service.revoke_token(token)
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
        Helper method counting total active administrators.
        """
        all_users = self._user_repository.list_all(limit=10000, offset=0)
        return sum(1 for u in all_users if u.is_admin and u.is_active)

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

        if is_currently_active_admin and (demoting_role or disabling_status):
            active_admin_count = self._count_active_admins()
            if active_admin_count <= 1:
                logger.warning(
                    "Admin operation blocked: Cannot demote or disable last active admin '%s' (ID=%d).",
                    target_user.username,
                    target_user.id,
                )
                raise AdminOperationError("Cannot demote, deactivate, or suspend the last active administrator.")

        # Execute repository update
        repo_update = UserUpdate(
            email=user_update.email,
            role=user_update.role,
            status=user_update.status,
            password=None,
        )
        updated_user = self._user_repository.update(user_id=user_id, user_update=repo_update)

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

    def delete_user_admin(
        self,
        user_id: int,
        actor_context: UserContext | None = None,
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

        if target_user.is_admin and target_user.is_active:
            active_admin_count = self._count_active_admins()
            if active_admin_count <= 1:
                logger.warning(
                    "Admin operation blocked: Cannot delete last active admin '%s' (ID=%d).",
                    target_user.username,
                    target_user.id,
                )
                raise AdminOperationError("Cannot delete the last active administrator.")

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
