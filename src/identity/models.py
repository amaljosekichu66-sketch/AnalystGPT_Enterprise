"""
Domain and API models for the Enterprise Identity subsystem.

Responsibilities
----------------
- Define user roles and status enumerations.
- Define internal domain User representation.
- Define Pydantic request/response validation schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# ==========================================================
# Enumerations
# ==========================================================


class UserRole(str, Enum):
    """
    Role-Based Access Control (RBAC) user roles.
    """

    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"

    @classmethod
    def from_string(cls, value: str) -> UserRole:
        """
        Parse role case-insensitively.
        """
        normalized = value.strip().upper()
        for role in cls:
            if role.value == normalized:
                return role
        raise ValueError(f"Unknown user role: {value}")


class UserStatus(str, Enum):
    """
    Lifecycle status of a user account.
    """

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

    @classmethod
    def from_string(cls, value: str) -> UserStatus:
        """
        Parse status case-insensitively.
        """
        normalized = value.strip().upper()
        for status in cls:
            if status.value == normalized:
                return status
        raise ValueError(f"Unknown user status: {value}")


# ==========================================================
# Domain Entity
# ==========================================================


@dataclass(frozen=True)
class User:
    """
    Immutable domain representation of an authenticated user.
    """

    id: int
    username: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.ANALYST
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_active(self) -> bool:
        """Return True if user account is active."""
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


# ==========================================================
# Pydantic Schemas
# ==========================================================

_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserBase(BaseModel):
    """Base schema for user identity fields."""

    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: str = Field(..., pattern=_EMAIL_PATTERN)
    role: UserRole = UserRole.ANALYST


class UserCreate(UserBase):
    """Schema for user account registration/creation."""

    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Schema for administrative or self user profile updates."""

    email: str | None = Field(None, pattern=_EMAIL_PATTERN)
    role: UserRole | None = None
    status: UserStatus | None = None
    password: str | None = Field(None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Safe public user representation omitting hashed credentials."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    """Schema for user login credentials."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Authentication token response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class LogoutResponse(BaseModel):
    """Logout response schema."""

    success: bool = True
    message: str = "Logged out successfully."


class UserDeleteResponse(BaseModel):
    """User deletion response schema."""

    model_config = ConfigDict(frozen=True)

    success: bool = True
    message: str = "User deleted successfully."
    user_id: int


class AdminUserUpdate(BaseModel):
    """Administrative user management update schema preventing overposting."""

    email: str | None = Field(None, pattern=_EMAIL_PATTERN)
    role: UserRole | None = None
    status: UserStatus | None = None


class PaginatedUserResponse(BaseModel):
    """Paginated user listing schema."""

    items: list[UserResponse]
    total: int
    limit: int
    offset: int


class AuditEventType(str, Enum):
    """Types of auditable security and lifecycle events."""

    USER_REGISTERED = "USER_REGISTERED"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    USER_UPDATED = "USER_UPDATED"
    USER_STATUS_CHANGED = "USER_STATUS_CHANGED"
    USER_ROLE_CHANGED = "USER_ROLE_CHANGED"
    USER_DELETED = "USER_DELETED"
    ACCESS_DENIED = "ACCESS_DENIED"
    PIPELINE_EXECUTED = "PIPELINE_EXECUTED"


class AuditEvent(BaseModel):
    """Structured security audit event representation."""

    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    actor_id: int | None = None
    actor_username: str | None = None
    target_id: int | None = None
    target_resource: str | None = None
    action: str
    outcome: str = "SUCCESS"  # SUCCESS / DENIED / FAILED
    details: dict[str, str | int | bool | None] = Field(default_factory=dict)
