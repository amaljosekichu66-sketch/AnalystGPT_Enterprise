"""
Tests for identity domain models, enumerations, and validation schemas.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.identity.models import (
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRole,
    UserStatus,
    UserUpdate,
)


class TestUserEnums:
    """Test UserRole and UserStatus enums."""

    def test_user_role_values(self) -> None:
        assert UserRole.ADMIN.value == "ADMIN"
        assert UserRole.ANALYST.value == "ANALYST"
        assert UserRole.VIEWER.value == "VIEWER"

    def test_user_role_from_string(self) -> None:
        assert UserRole.from_string("admin") == UserRole.ADMIN
        assert UserRole.from_string("ANALYST") == UserRole.ANALYST
        assert UserRole.from_string(" viewer ") == UserRole.VIEWER

    def test_user_role_from_string_invalid(self) -> None:
        with pytest.raises(ValueError, match="Unknown user role"):
            UserRole.from_string("SUPERUSER")

    def test_user_status_values(self) -> None:
        assert UserStatus.ACTIVE.value == "ACTIVE"
        assert UserStatus.INACTIVE.value == "INACTIVE"
        assert UserStatus.SUSPENDED.value == "SUSPENDED"

    def test_user_status_from_string(self) -> None:
        assert UserStatus.from_string("active") == UserStatus.ACTIVE
        assert UserStatus.from_string("INACTIVE") == UserStatus.INACTIVE
        assert UserStatus.from_string(" suspended ") == UserStatus.SUSPENDED

    def test_user_status_from_string_invalid(self) -> None:
        with pytest.raises(ValueError, match="Unknown user status"):
            UserStatus.from_string("DELETED")


class TestUserDomainEntity:
    """Test User domain entity dataclass."""

    def test_user_creation_and_properties(self) -> None:
        now = datetime.now(UTC)
        user = User(
            id=1,
            username="analyst_jane",
            email="jane@analystgpt.local",
            hashed_password="$pbkdf2-sha256$mockhash",
            role=UserRole.ANALYST,
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        assert user.id == 1
        assert user.username == "analyst_jane"
        assert user.email == "jane@analystgpt.local"
        assert user.is_active is True
        assert user.is_analyst is True
        assert user.is_admin is False
        assert user.is_viewer is False

    def test_user_admin_properties(self) -> None:
        user = User(
            id=2,
            username="admin_bob",
            email="bob@analystgpt.local",
            hashed_password="$pbkdf2-sha256$mockhash",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
        )
        assert user.is_admin is True
        assert user.is_analyst is False
        assert user.is_viewer is False

    def test_user_viewer_properties(self) -> None:
        user = User(
            id=3,
            username="viewer_claire",
            email="claire@analystgpt.local",
            hashed_password="$pbkdf2-sha256$mockhash",
            role=UserRole.VIEWER,
            status=UserStatus.SUSPENDED,
        )
        assert user.is_viewer is True
        assert user.is_active is False


class TestUserSchemas:
    """Test Pydantic schemas for request validation and response serialization."""

    def test_user_create_valid(self) -> None:
        data = {
            "username": "john_doe",
            "email": "john@enterprise.com",
            "password": "SecurePassword123!",
            "role": "ANALYST",
        }
        schema = UserCreate(**data)
        assert schema.username == "john_doe"
        assert schema.email == "john@enterprise.com"
        assert schema.password == "SecurePassword123!"
        assert schema.role == UserRole.ANALYST

    def test_user_create_invalid_username(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(
                username="ab",  # too short (<3)
                email="valid@enterprise.com",
                password="SecurePassword123!",
            )

    def test_user_create_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(
                username="valid_user",
                email="not-an-email",
                password="SecurePassword123!",
            )

    def test_user_create_short_password(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(
                username="valid_user",
                email="valid@enterprise.com",
                password="short",  # < 8 chars
            )

    def test_user_response_serialization(self) -> None:
        now = datetime.now(UTC)
        user = User(
            id=42,
            username="data_guru",
            email="guru@enterprise.com",
            hashed_password="$pbkdf2-sha256$secret_hash_value",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        response = UserResponse.model_validate(user)
        assert response.id == 42
        assert response.username == "data_guru"
        assert response.email == "guru@enterprise.com"
        assert response.role == UserRole.ADMIN
        assert response.status == UserStatus.ACTIVE
        # Verify hashed_password is NOT exposed in response schema
        assert "hashed_password" not in response.model_dump()

    def test_user_login_schema(self) -> None:
        login = UserLogin(username="analyst1", password="secret_password")
        assert login.username == "analyst1"
        assert login.password == "secret_password"

    def test_user_update_partial(self) -> None:
        update = UserUpdate(role=UserRole.ADMIN, status=UserStatus.SUSPENDED)
        assert update.role == UserRole.ADMIN
        assert update.status == UserStatus.SUSPENDED
        assert update.email is None
        assert update.password is None
