"""
Authentication and user identity API endpoints for AnalystGPT Enterprise.

Endpoints
---------
- POST /api/auth/register : Register a new user account (201 Created)
- POST /api/auth/login    : Authenticate and issue signed access token (200 OK)
- GET  /api/auth/me       : Get current authenticated user profile (200 OK)
- POST /api/auth/logout   : Revoke access token / session invalidation (200 OK)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, status

from src.api.dependencies.auth_dependencies import (
    get_current_active_user,
    get_user_service,
)
from src.api.rate_limit import rate_limit
from src.core import config
from src.identity.context import UserContext
from src.identity.exceptions import PermissionDeniedError
from src.identity.models import (
    LogoutResponse,
    TokenResponse,
    UserLogin,
    UserRegistration,
    UserResponse,
)
from src.identity.user_service import UserService

auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@auth_router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    dependencies=[Depends(rate_limit("register", lambda: config.AUTH_REGISTER_RATE_LIMIT))],
)
def register(
    registration: UserRegistration,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Register a new user with secure password hashing.

    The role is assigned server-side and cannot be chosen by the caller; a
    payload carrying `role` (or any other unknown field) is rejected with 422.
    New accounts are VIEWER (M10). With `AUTH_SELF_REGISTRATION_ENABLED=false`
    the endpoint refuses every request with 403.

    A duplicate username or email answers 409 with a message that does not
    say which (SEC-15). The status itself still confirms that one of them is
    taken; that is an accepted risk (L3), bounded by the registration rate
    limit, because users need to know to pick another name.
    """
    if not config.AUTH_SELF_REGISTRATION_ENABLED:
        raise PermissionDeniedError("Self-registration is disabled. Ask an administrator for an account.")
    user = user_service.register_self(registration)
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue access token",
    dependencies=[Depends(rate_limit("login", lambda: config.AUTH_LOGIN_RATE_LIMIT))],
)
def login(
    user_login: UserLogin,
    user_service: UserService = Depends(get_user_service),
) -> TokenResponse:
    """
    Validate user credentials, enforce account status, and return a signed Bearer token.

    Plain `def` on purpose (M2): PBKDF2 at 600k iterations takes ~0.5 s, and
    in an `async def` it ran on the event loop and stalled every other request.
    FastAPI runs sync endpoints in its threadpool.
    """
    user, access_token, expires_in = user_service.login(user_login)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ),
    )


@auth_router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_current_user_profile(
    context: UserContext = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Retrieve safe profile details of the currently authenticated user.
    """
    user = user_service.get_user_by_id(context.user_id)
    if user is None:
        from src.identity.exceptions import UserNotFoundError

        raise UserNotFoundError(f"User with ID {context.user_id} not found.")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@auth_router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Invalidate user session / token",
)
def logout(
    authorization: str | None = Header(None, alias="Authorization"),
    context: UserContext = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
) -> LogoutResponse:
    """
    Revoke the caller's own Bearer token.

    Requires a valid token (401 otherwise). Previously anonymous callers could
    post arbitrary strings here and each one was stored forever (SEC-09).
    """
    token: str | None = None
    if authorization and authorization.strip().lower().startswith("bearer "):
        token = authorization.strip()[7:].strip()

    user_service.logout(token, actor_context=context)
    return LogoutResponse(
        success=True,
        message="Logged out successfully.",
    )
