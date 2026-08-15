"""
Tests for database UserRepository using SQLite engine.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from src.database.repositories.user_repository import UserRepository
from src.database.schema_manager import SchemaManager
from src.database.sqlite_connection import SQLiteConnection
from src.identity.exceptions import UserAlreadyExistsError, UserNotFoundError
from src.identity.models import UserCreate, UserRole, UserStatus, UserUpdate


@pytest.fixture
def sqlite_user_repo():
    """Create a temporary SQLite database connection and initialized UserRepository."""
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "test_identity.db"

    conn = SQLiteConnection(str(db_path))
    conn.connect()

    schema_manager = SchemaManager(conn)
    schema_manager.initialize_schema()

    repo = UserRepository(conn)

    yield repo

    conn.disconnect()
    temp_dir.cleanup()


class TestDatabaseUserRepository:
    """Test UserRepository against SQLite database engine."""

    def test_create_and_fetch_user(self, sqlite_user_repo: UserRepository) -> None:
        create_data = UserCreate(
            username="db_analyst",
            email="db_analyst@enterprise.com",
            password="SecurePassword123!",
            role=UserRole.ANALYST,
        )

        user = sqlite_user_repo.create(create_data, hashed_password="$pbkdf2$dbhash")
        assert user.id is not None
        assert user.username == "db_analyst"
        assert user.email == "db_analyst@enterprise.com"
        assert user.role == UserRole.ANALYST
        assert user.status == UserStatus.ACTIVE

        # By ID
        fetched_id = sqlite_user_repo.get_by_id(user.id)
        assert fetched_id is not None
        assert fetched_id.id == user.id
        assert fetched_id.username == "db_analyst"

        # By username
        fetched_username = sqlite_user_repo.get_by_username("DB_ANALYST")
        assert fetched_username is not None
        assert fetched_username.id == user.id

        # By email
        fetched_email = sqlite_user_repo.get_by_email("DB_ANALYST@ENTERPRISE.COM")
        assert fetched_email is not None
        assert fetched_email.id == user.id

    def test_duplicate_username_raises_error(
        self, sqlite_user_repo: UserRepository
    ) -> None:
        create_data = UserCreate(
            username="duplicate_test",
            email="user1@test.com",
            password="SecurePassword123!",
        )
        sqlite_user_repo.create(create_data, "$hash")

        dup = UserCreate(
            username="duplicate_test",
            email="user2@test.com",
            password="SecurePassword123!",
        )
        with pytest.raises(UserAlreadyExistsError):
            sqlite_user_repo.create(dup, "$hash")

    def test_duplicate_email_raises_error(
        self, sqlite_user_repo: UserRepository
    ) -> None:
        create_data = UserCreate(
            username="user_alpha",
            email="same_email@test.com",
            password="SecurePassword123!",
        )
        sqlite_user_repo.create(create_data, "$hash")

        dup = UserCreate(
            username="user_beta",
            email="same_email@test.com",
            password="SecurePassword123!",
        )
        with pytest.raises(UserAlreadyExistsError):
            sqlite_user_repo.create(dup, "$hash")

    def test_update_user(self, sqlite_user_repo: UserRepository) -> None:
        user = sqlite_user_repo.create(
            UserCreate(username="updatable", email="old@test.com", password="SecurePassword123!"),
            "$oldhash",
        )

        updated = sqlite_user_repo.update(
            user.id,
            UserUpdate(email="new@test.com", role=UserRole.ADMIN, status=UserStatus.SUSPENDED),
            hashed_password="$newhash",
        )

        assert updated.email == "new@test.com"
        assert updated.role == UserRole.ADMIN
        assert updated.status == UserStatus.SUSPENDED
        assert updated.hashed_password == "$newhash"

    def test_update_nonexistent_user(self, sqlite_user_repo: UserRepository) -> None:
        with pytest.raises(UserNotFoundError):
            sqlite_user_repo.update(8888, UserUpdate(role=UserRole.ADMIN))

    def test_delete_user(self, sqlite_user_repo: UserRepository) -> None:
        user = sqlite_user_repo.create(
            UserCreate(username="to_delete", email="del@test.com", password="SecurePassword123!"),
            "$hash",
        )
        assert sqlite_user_repo.count() == 1
        assert sqlite_user_repo.delete(user.id) is True
        assert sqlite_user_repo.count() == 0
        assert sqlite_user_repo.get_by_id(user.id) is None
        assert sqlite_user_repo.delete(user.id) is False

    def test_list_all_and_count(self, sqlite_user_repo: UserRepository) -> None:
        for i in range(4):
            sqlite_user_repo.create(
                UserCreate(username=f"db_user_{i}", email=f"user_{i}@test.com", password="SecurePassword123!"),
                "$hash",
            )

        assert sqlite_user_repo.count() == 4
        all_users = sqlite_user_repo.list_all(limit=10, offset=0)
        assert len(all_users) == 4
        assert all_users[0].username == "db_user_0"
