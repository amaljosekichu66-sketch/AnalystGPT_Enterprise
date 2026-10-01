"""
Administrative User Management API routes for AnalystGPT Enterprise.

Responsibilities
----------------
- Expose user administration REST endpoints (list, get, update, delete).
- Enforce strict USER_MANAGE permission.
- Protect against mass-assignment / overposting via dedicated AdminUserUpdate schemas.
- Prevent self-lockout / last active administrator removal.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from starlette.concurrency import run_in_threadpool

from src.api.dependencies.application_dependency import get_application
from src.api.dependencies.auth_dependencies import (
    get_user_service,
    require_permission,
)
from src.application.app import Application
from src.identity.context import UserContext
from src.identity.models import (
    AdminUserUpdate,
    AuditEventType,
    PaginatedUserResponse,
    UserDeleteResponse,
    UserResponse,
)
from src.identity.permissions import Permission
from src.identity.user_service import UserService

admin_router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


@admin_router.get(
    "/users",
    response_model=PaginatedUserResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users (Admin)",
    description="List all registered user accounts with pagination.",
)
def list_users(
    limit: int = Query(100, ge=1, le=1000, description="Maximum users to return."),
    offset: int = Query(0, ge=0, description="Number of users to skip."),
    _context: UserContext = Depends(require_permission(Permission.USER_READ)),
    user_service: UserService = Depends(get_user_service),
) -> PaginatedUserResponse:
    """
    List user accounts with pagination.
    """
    users = user_service.list_users(limit=limit, offset=offset)
    total = user_service.count_users()

    return PaginatedUserResponse(
        items=[
            UserResponse(
                id=u.id,
                username=u.username,
                email=u.email,
                role=u.role,
                status=u.status,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in users
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin_router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user details by ID (Admin)",
    description="Retrieve full safe profile details for a specific user.",
)
def get_user(
    user_id: int,
    _context: UserContext = Depends(require_permission(Permission.USER_READ)),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Get user profile by ID.
    """
    user = user_service.get_user_by_id(user_id)
    if user is None:
        from src.identity.exceptions import UserNotFoundError

        raise UserNotFoundError(f"User with ID {user_id} not found.")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@admin_router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user role, status, or email (Admin)",
    description="Update a user's role, lifecycle status, or email with administrative safeguards.",
)
def update_user(
    user_id: int,
    user_update: AdminUserUpdate,
    context: UserContext = Depends(require_permission(Permission.USER_MANAGE)),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Administer user role, status, or email.
    """
    updated_user = user_service.update_user_admin(
        user_id=user_id,
        user_update=user_update,
        actor_context=context,
    )

    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        role=updated_user.role,
        status=updated_user.status,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
    )


@admin_router.post(
    "/users/{user_id}/unlock",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear a user's login lockout (Admin)",
    description="Clear every failed-login counter for the account, from every client address.",
)
def unlock_user(
    user_id: int,
    context: UserContext = Depends(require_permission(Permission.USER_MANAGE)),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Lift a lockout early. Lockouts also expire on their own.
    """
    user = user_service.unlock_user(user_id=user_id, actor_context=context)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@admin_router.delete(
    "/users/{user_id}",
    response_model=UserDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete user account (Admin)",
    description="Delete a user entity with last active administrator protection.",
)
def delete_user(
    user_id: int,
    context: UserContext = Depends(require_permission(Permission.USER_MANAGE)),
    user_service: UserService = Depends(get_user_service),
    application: Application = Depends(get_application),
) -> UserDeleteResponse:
    """
    Delete a user account AND the data it owns (SEC-20).
    """
    user_service.delete_user_admin(
        user_id=user_id,
        actor_context=context,
        # Data and account in one transaction (P2-14).
        delete_account=lambda target: application.purge_user_data(target.id, target.username, delete_account=True),
    )

    return UserDeleteResponse(
        success=True,
        message=f"User with ID {user_id} deleted successfully.",
        user_id=user_id,
    )


@admin_router.get(
    "/audit-events",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List audit events (Admin)",
    description="Most recent durable audit events, newest first. Requires AUDIT_READ.",
)
async def list_audit_events(
    limit: int = Query(100, ge=1, le=1000),
    event_type: AuditEventType | None = Query(None),
    actor_id: int | None = Query(None),
    _context: UserContext = Depends(require_permission(Permission.AUDIT_READ)),
) -> list[dict[str, Any]]:
    """Read the persisted audit trail."""
    from src.identity.audit_store import DatabaseAuditSink

    return await run_in_threadpool(
        DatabaseAuditSink().recent,
        limit,
        event_type.value if event_type else None,
        actor_id,
    )


@admin_router.get(
    "/audit-events/verify",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Verify the audit hash chain (Admin)",
    description="Recompute the tamper-evident hash chain over the retained audit rows.",
)
def verify_audit_chain(
    _context: UserContext = Depends(require_permission(Permission.AUDIT_READ)),
) -> dict[str, Any]:
    """P2-14: report whether any retained audit row was altered or removed."""
    from src.identity.audit_store import DatabaseAuditSink

    return DatabaseAuditSink().verify_chain()
