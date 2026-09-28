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
from src.identity.context import UserContext
from src.identity.models import (
    LogoutResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
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
)
async def register(
    user_create: UserCreate,
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Register a new user with secure password hashing and role assignment.
    """
    user = user_service.register_user(user_create)
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
)
async def login(
    user_login: UserLogin,
    user_service: UserService = Depends(get_user_service),
) -> TokenResponse:
    """
    Validate user credentials, enforce account status, and return a signed Bearer token.
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
async def logout(
    authorization: str | None = Header(None, alias="Authorization"),
    user_service: UserService = Depends(get_user_service),
) -> LogoutResponse:
    """
    Revoke the provided Bearer token and invalidate active server-side session state.
    """
    token: str | None = None
    if authorization and authorization.strip().lower().startswith("bearer "):
        token = authorization.strip()[7:].strip()

    user_service.logout(token)
    return LogoutResponse(
        success=True,
        message="Logged out successfully.",
    )
