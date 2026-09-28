"""
FastAPI dependency providers for Enterprise Identity and Access Management.

Responsibilities
----------------
- Extract and populate UserContext from incoming HTTP Authorization headers or tokens.
- Provide dependency hooks for route-level authentication.
- Provide dependency factories for Role-Based Access Control (RBAC).
- Provide dependency factories for fine-grained permission enforcement.
- Provide injectable UserService provider with test override capability.
"""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, Header, Request

from src.core import config
from src.core.logger import logger
from src.identity.context import (
    UserContext,
    get_current_user_context,
    set_current_user_context,
)
from src.identity.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    PermissionDeniedError,
    UserDisabledError,
)
from src.identity.models import UserRole, UserStatus
from src.identity.permissions import Permission
from src.identity.user_service import UserService

# ==========================================================
# UserService Provider & Test Hooks
# ==========================================================

_global_user_service: UserService | None = None


def get_user_service() -> UserService:
    """
    Provide the active UserService instance.
    """
    global _global_user_service
    if _global_user_service is None:
        from src.database.connection_factory import ConnectionFactory
        from src.database.repositories.user_repository import UserRepository
        from src.database.schema_manager import SchemaManager

        connection = ConnectionFactory.create_connection()
        connection.connect()
        schema_mgr = SchemaManager(connection)
        schema_mgr.initialize_schema()

        user_repo = UserRepository(connection)
        _global_user_service = UserService(user_repository=user_repo)

    return _global_user_service


def set_user_service_instance(service: UserService | None) -> None:
    """
    Inject a custom or mock UserService (primarily for automated testing).
    """
    global _global_user_service
    _global_user_service = service


# ==========================================================
# User Context Dependency
# ==========================================================


async def get_user_context(
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    x_user_id: int | None = Header(None, alias="X-User-Id"),
    x_user_name: str | None = Header(None, alias="X-User-Name"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    user_service: UserService = Depends(get_user_service),
) -> UserContext:
    """
    Resolve the UserContext for the current HTTP request.

    Evaluates credentials in order:
    1. 'Authorization: Bearer <token>' header - the only mechanism that
       actually proves identity.
    2. Development identity headers (X-User-Id, X-User-Name, ...), but ONLY
       when `config.AUTH_ALLOW_HEADER_IDENTITY` is enabled.
    3. Anonymous fallback.

    Why the headers are gated
    -------------------------
    `X-User-Id` / `X-User-Role` are unauthenticated request headers: the caller
    chooses what they say. Honouring them unconditionally let anyone assert
    ADMIN and read or modify every user account, because the role check
    downstream is only ever as trustworthy as the identity feeding it.

    They remain available for local development and for the API test-suite,
    which uses them deliberately, but the flag defaults to False and
    `src/core/config.py` refuses to enable it outside development.
    """
    if authorization is not None:
        auth_header = authorization.strip()
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            if not token:
                raise InvalidTokenError("Bearer token missing.")

            user = user_service.get_current_user_from_token(token)
            context = UserContext.from_user(user)
            set_current_user_context(context)
            return context

    header_identity_supplied = x_user_id is not None or x_user_name is not None

    if header_identity_supplied and not config.AUTH_ALLOW_HEADER_IDENTITY:
        # Do not silently downgrade to anonymous: a caller presenting an
        # identity is making a claim, and refusing it explicitly is what makes
        # the bypass visible in logs instead of looking like a stray 401.
        logger.warning(
            "Rejected unauthenticated identity headers (X-User-Id=%s, "
            "X-User-Role=%s). Header identity is disabled; authenticate with "
            "'Authorization: Bearer <token>'.",
            x_user_id,
            x_user_role,
        )
        raise AuthenticationError(
            "Unauthenticated identity headers are not accepted. " "Authenticate with 'Authorization: Bearer <token>'."
        )

    if header_identity_supplied:
        username = x_user_name or f"user_{x_user_id}"
        email = x_user_email or f"{username}@analystgpt.local"

        try:
            role = UserRole.from_string(x_user_role) if x_user_role else UserRole.ANALYST
        except ValueError:
            role = UserRole.ANALYST

        context = UserContext(
            user_id=x_user_id or 1,
            username=username,
            email=email,
            role=role,
            status=UserStatus.ACTIVE,
            is_authenticated=True,
        )
    else:
        context = UserContext.anonymous()

    set_current_user_context(context)
    return context


# ==========================================================
# Authentication Enforcement
# ==========================================================


async def get_current_active_user(
    context: UserContext = Depends(get_user_context),
) -> UserContext:
    """
    Ensure the current request is from an authenticated, active user.

    Raises
    ------
    AuthenticationError
        If the user is not authenticated.
    UserDisabledError
        If the user account is inactive or suspended.
    """
    if not context.is_authenticated:
        raise AuthenticationError("Authentication required to access this resource.")

    if not context.is_active:
        raise UserDisabledError("User account is inactive or suspended.")

    return context


# ==========================================================
# RBAC Role Requirement Factory
# ==========================================================


def require_role(*allowed_roles: UserRole) -> Callable:
    """
    Factory creating a FastAPI dependency that enforces role membership.
    """

    async def role_checker(
        context: UserContext = Depends(get_current_active_user),
    ) -> UserContext:
        if context.role not in allowed_roles:
            from src.identity.audit import get_audit_service
            from src.identity.models import AuditEventType

            allowed_names = ", ".join(r.value for r in allowed_roles)
            get_audit_service().record_event(
                event_type=AuditEventType.ACCESS_DENIED,
                action="ROLE_CHECK",
                actor_id=context.user_id,
                actor_username=context.username,
                target_resource="ROLE_ACCESS",
                outcome="DENIED",
                details={
                    "allowed_roles": allowed_names,
                    "user_role": context.role.value,
                },
            )
            raise PermissionDeniedError(
                f"Access denied. User role '{context.role.value}' is not among allowed roles: [{allowed_names}]."
            )

        return context

    return role_checker


# ==========================================================
# Granular Permission Requirement Factory
# ==========================================================


def require_permission(permission: Permission) -> Callable:
    """
    Factory creating a FastAPI dependency that enforces a fine-grained permission.
    """

    async def permission_checker(
        context: UserContext = Depends(get_current_active_user),
    ) -> UserContext:
        if not context.has_permission(permission):
            from src.identity.audit import get_audit_service
            from src.identity.models import AuditEventType

            get_audit_service().record_event(
                event_type=AuditEventType.ACCESS_DENIED,
                action="PERMISSION_CHECK",
                actor_id=context.user_id,
                actor_username=context.username,
                target_resource=permission.value,
                outcome="DENIED",
                details={
                    "required_permission": permission.value,
                    "user_role": context.role.value,
                },
            )
            raise PermissionDeniedError(
                f"Access denied. Required permission '{permission.value}' is not granted for role '{context.role.value}'."
            )

        return context

    return permission_checker
