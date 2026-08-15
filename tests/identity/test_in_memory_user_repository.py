"""
Tests for InMemoryUserRepository implementation.
"""

from __future__ import annotations

import pytest

from src.identity.exceptions import UserAlreadyExistsError, UserNotFoundError
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import UserCreate, UserRole, UserStatus, UserUpdate


class TestInMemoryUserRepository:
    """Test in-memory user repository operations."""

    def test_create_and_get_user(self) -> None:
        repo = InMemoryUserRepository()
        create_data = UserCreate(
            username="analyst_test",
            email="test@enterprise.com",
            password="dummy_password",
            role=UserRole.ANALYST,
        )

        user = repo.create(create_data, hashed_password="$pbkdf2$dummyhash")
        assert user.id == 1
        assert user.username == "analyst_test"
        assert user.email == "test@enterprise.com"

        # Lookup by id
        fetched_id = repo.get_by_id(1)
        assert fetched_id == user

        # Lookup by username
        fetched_username = repo.get_by_username("analyst_test")
        assert fetched_username == user

        # Lookup by email
        fetched_email = repo.get_by_email("test@enterprise.com")
        assert fetched_email == user

    def test_duplicate_username_prevented(self) -> None:
        repo = InMemoryUserRepository()
        create_data = UserCreate(
            username="unique_user",
            email="user1@test.com",
            password="dummy_password",
        )
        repo.create(create_data, "$hash")

        duplicate_username = UserCreate(
            username="unique_user",
            email="user2@test.com",
            password="dummy_password",
        )
        with pytest.raises(UserAlreadyExistsError, match="username 'unique_user' already exists"):
            repo.create(duplicate_username, "$hash")

    def test_duplicate_email_prevented(self) -> None:
        repo = InMemoryUserRepository()
        create_data = UserCreate(
            username="user_one",
            email="shared@test.com",
            password="dummy_password",
        )
        repo.create(create_data, "$hash")

        duplicate_email = UserCreate(
            username="user_two",
            email="shared@test.com",
            password="dummy_password",
        )
        with pytest.raises(UserAlreadyExistsError, match="email 'shared@test.com' already exists"):
            repo.create(duplicate_email, "$hash")

    def test_update_user(self) -> None:
        repo = InMemoryUserRepository()
        create_data = UserCreate(
            username="mutable_user",
            email="mutable@test.com",
            password="password",
        )
        user = repo.create(create_data, "$oldhash")

        update_data = UserUpdate(
            email="updated@test.com",
            role=UserRole.ADMIN,
            status=UserStatus.SUSPENDED,
        )
        updated = repo.update(user.id, update_data, hashed_password="$newhash")

        assert updated.email == "updated@test.com"
        assert updated.role == UserRole.ADMIN
        assert updated.status == UserStatus.SUSPENDED
        assert updated.hashed_password == "$newhash"

    def test_update_nonexistent_user_raises_error(self) -> None:
        repo = InMemoryUserRepository()
        with pytest.raises(UserNotFoundError, match="does not exist"):
            repo.update(999, UserUpdate(role=UserRole.ADMIN))

    def test_delete_user(self) -> None:
        repo = InMemoryUserRepository()
        user = repo.create(
            UserCreate(username="to_delete", email="del@test.com", password="SecurePassword123!"),
            "$hash",
        )
        assert repo.count() == 1
        assert repo.delete(user.id) is True
        assert repo.count() == 0
        assert repo.get_by_id(user.id) is None
        assert repo.get_by_username("to_delete") is None
        assert repo.delete(user.id) is False

    def test_list_all_with_pagination(self) -> None:
        repo = InMemoryUserRepository()
        for i in range(5):
            repo.create(
                UserCreate(username=f"user_{i}", email=f"user_{i}@test.com", password="SecurePassword123!"),
                "$hash",
            )

        assert repo.count() == 5
        page1 = repo.list_all(limit=2, offset=0)
        assert len(page1) == 2
        assert page1[0].username == "user_0"
        assert page1[1].username == "user_1"

        page2 = repo.list_all(limit=2, offset=2)
        assert len(page2) == 2
        assert page2[0].username == "user_2"
        assert page2[1].username == "user_3"
