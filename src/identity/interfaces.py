"""
Core interfaces and protocols for the Enterprise Identity subsystem.

These contracts ensure decoupling between domain logic, persistence engines,
cryptographic hashing providers, and authorization services.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.identity.context import UserContext
from src.identity.models import User, UserCreate, UserRole, UserUpdate
from src.identity.permissions import Permission

# ==========================================================
# Cryptographic Password Hasher Protocol
# ==========================================================


@runtime_checkable
class IPasswordHasher(Protocol):
    """
    Protocol for secure password hashing and verification.
    """

    def hash(self, password: str) -> str:
        """Hash a plaintext password with a unique cryptographic salt."""
        ...

    def verify(self, password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a stored cryptographic hash."""
        ...


# ==========================================================
# User Repository Protocol
# ==========================================================


@runtime_checkable
class IUserRepository(Protocol):
    """
    Protocol for user persistence operations.
    """

    def get_by_id(self, user_id: int) -> User | None:
        """Retrieve a user by primary ID."""
        ...

    def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by unique username."""
        ...

    def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by unique email address."""
        ...

    def create(self, user_create: UserCreate, hashed_password: str) -> User:
        """Create and persist a new user entity."""
        ...

    def update(
        self,
        user_id: int,
        user_update: UserUpdate,
        hashed_password: str | None = None,
    ) -> User:
        """Update an existing user entity."""
        ...

    def delete(self, user_id: int) -> bool:
        """Delete a user entity by ID."""
        ...

    def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """List persisted users with pagination."""
        ...

    def count(self) -> int:
        """Count total persisted users."""
        ...


# ==========================================================
# Authentication Service Protocol
# ==========================================================


@runtime_checkable
class IAuthenticator(Protocol):
    """
    Protocol for authenticating user credentials.
    """

    def authenticate(self, username: str, password: str) -> User:
        """Validate credentials and return authenticated User entity."""
        ...


# ==========================================================
# Authorization Service Protocol
# ==========================================================


@runtime_checkable
class IAuthorizationService(Protocol):
    """
    Protocol for role and permission evaluation.
    """

    def is_authorized(
        self,
        context: UserContext,
        permission: Permission,
    ) -> bool:
        """Check if context is authorized for the given permission."""
        ...

    def require_permission(
        self,
        context: UserContext,
        permission: Permission,
    ) -> None:
        """Enforce permission or raise PermissionDeniedError."""
        ...

    def require_role(
        self,
        context: UserContext,
        *allowed_roles: UserRole,
    ) -> None:
        """Enforce role membership or raise PermissionDeniedError."""
        ...


# ==========================================================
# Token Service Protocol
# ==========================================================


@runtime_checkable
class ITokenService(Protocol):
    """
    Protocol for access token issuance and validation.
    """

    def create_access_token(
        self,
        user: User,
        expires_delta_seconds: int | None = None,
    ) -> str:
        """Generate a cryptographically signed access token."""
        ...

    def verify_access_token(self, token: str) -> dict:
        """Verify token signature, validity, expiration and return decoded claims."""
        ...


# ==========================================================
# Token Revocation Protocol
# ==========================================================


@runtime_checkable
class ITokenRevocationService(Protocol):
    """
    Protocol for tracking revoked access tokens upon logout.
    """

    def revoke_token(self, token: str) -> None:
        """Mark a token as revoked/invalidated."""
        ...

    def is_revoked(self, token: str) -> bool:
        """Check if a token has been revoked."""
        ...
