"""
In-memory user repository for testing and standalone operations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock

from src.identity.exceptions import UserAlreadyExistsError, UserNotFoundError
from src.identity.models import User, UserCreate, UserUpdate


class InMemoryUserRepository:
    """
    Thread-safe in-memory implementation of IUserRepository.
    """

    def __init__(self) -> None:
        self._users: dict[int, User] = {}
        self._by_username: dict[str, int] = {}
        self._by_email: dict[str, int] = {}
        self._next_id: int = 1
        self._lock = Lock()

    def get_by_id(self, user_id: int) -> User | None:
        """Retrieve user by ID."""
        with self._lock:
            return self._users.get(user_id)

    def get_by_username(self, username: str) -> User | None:
        """Retrieve user by username (case-insensitive search)."""
        with self._lock:
            user_id = self._by_username.get(username.strip().lower())
            if user_id is None:
                return None
            return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        """Retrieve user by email (case-insensitive search)."""
        with self._lock:
            user_id = self._by_email.get(email.strip().lower())
            if user_id is None:
                return None
            return self._users.get(user_id)

    def create(self, user_create: UserCreate, hashed_password: str) -> User:
        """Create and store a new user."""
        username_key = user_create.username.strip().lower()
        email_key = user_create.email.strip().lower()

        with self._lock:
            if username_key in self._by_username:
                raise UserAlreadyExistsError(f"User with username '{user_create.username}' already exists.")
            if email_key in self._by_email:
                raise UserAlreadyExistsError(f"User with email '{user_create.email}' already exists.")

            user_id = self._next_id
            self._next_id += 1

            now = datetime.now(UTC)
            user = User(
                id=user_id,
                username=user_create.username,
                email=user_create.email,
                hashed_password=hashed_password,
                role=user_create.role,
                created_at=now,
                updated_at=now,
            )

            self._users[user_id] = user
            self._by_username[username_key] = user_id
            self._by_email[email_key] = user_id

            return user

    def update(
        self,
        user_id: int,
        user_update: UserUpdate,
        hashed_password: str | None = None,
    ) -> User:
        """Update an existing user."""
        with self._lock:
            current_user = self._users.get(user_id)
            if current_user is None:
                raise UserNotFoundError(f"User with id {user_id} does not exist.")

            # Check email conflict
            if user_update.email is not None:
                new_email_key = user_update.email.strip().lower()
                existing_user_id = self._by_email.get(new_email_key)
                if existing_user_id is not None and existing_user_id != user_id:
                    raise UserAlreadyExistsError(f"Email '{user_update.email}' is already in use by another user.")
                # Remove old email index
                self._by_email.pop(current_user.email.strip().lower(), None)
                self._by_email[new_email_key] = user_id

            updated_user = User(
                id=user_id,
                username=current_user.username,
                email=user_update.email if user_update.email is not None else current_user.email,
                hashed_password=(hashed_password if hashed_password is not None else current_user.hashed_password),
                role=user_update.role if user_update.role is not None else current_user.role,
                status=user_update.status if user_update.status is not None else current_user.status,
                created_at=current_user.created_at,
                updated_at=datetime.now(UTC),
            )

            self._users[user_id] = updated_user
            return updated_user

    def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        with self._lock:
            user = self._users.pop(user_id, None)
            if user is None:
                return False
            self._by_username.pop(user.username.strip().lower(), None)
            self._by_email.pop(user.email.strip().lower(), None)
            return True

    def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """List all users with pagination."""
        with self._lock:
            all_users = list(self._users.values())
            return all_users[offset : offset + limit]

    def count(self) -> int:
        """Return total user count."""
        with self._lock:
            return len(self._users)
