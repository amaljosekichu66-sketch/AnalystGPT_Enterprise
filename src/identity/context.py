"""
Request and security context for AnalystGPT Enterprise.

Responsibilities
----------------
- Maintain the current authenticated user context across API/Application layers.
- Provide contextual access to user identity, roles, and permissions.
- Support thread-safe context variables for asynchronous request processing.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

from src.identity.models import User, UserRole, UserStatus
from src.identity.permissions import Permission, has_permission

# ==========================================================
# User Context
# ==========================================================


@dataclass(frozen=True)
class UserContext:
    """
    Contextual snapshot of the currently executing identity.
    """

    user_id: int | None
    username: str
    email: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    is_authenticated: bool = True

    @property
    def is_active(self) -> bool:
        """Return True if the user account is active."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_admin(self) -> bool:
        """Return True if user has the ADMIN role."""
        return self.role == UserRole.ADMIN

    @property
    def is_analyst(self) -> bool:
        """Return True if user has the ANALYST role."""
        return self.role == UserRole.ANALYST

    @property
    def is_viewer(self) -> bool:
        """Return True if user has the VIEWER role."""
        return self.role == UserRole.VIEWER

    def has_permission(self, permission: Permission) -> bool:
        """Return True if the user's role grants the given permission."""
        if not self.is_authenticated or not self.is_active:
            return False
        return has_permission(self.role, permission)

    @classmethod
    def from_user(cls, user: User) -> UserContext:
        """
        Create a UserContext from an authenticated domain User entity.
        """
        return cls(
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            status=user.status,
            is_authenticated=True,
        )

    @classmethod
    def anonymous(cls) -> UserContext:
        """
        Create an unauthenticated / anonymous user context.
        """
        return cls(
            user_id=None,
            username="anonymous",
            email="anonymous@analystgpt.local",
            role=UserRole.VIEWER,
            status=UserStatus.INACTIVE,
            is_authenticated=False,
        )

    @classmethod
    def system(cls) -> UserContext:
        """
        Create a trusted internal system/CLI user context with ADMIN privileges.
        """
        return cls(
            user_id=0,
            username="system",
            email="system@analystgpt.local",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_authenticated=True,
        )


# ==========================================================
# Context Variable Management
# ==========================================================

_current_context: ContextVar[UserContext] = ContextVar(
    "current_user_context",
    default=UserContext.anonymous(),
)


def get_current_user_context() -> UserContext:
    """
    Retrieve the active UserContext for the current execution context.
    """
    return _current_context.get()


def set_current_user_context(context: UserContext) -> None:
    """
    Set the active UserContext for the current execution context.
    """
    _current_context.set(context)
