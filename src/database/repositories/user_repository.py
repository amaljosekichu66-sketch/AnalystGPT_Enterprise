"""
User repository implementation for SQLite and PostgreSQL.

Implements the IUserRepository interface using BaseRepository database abstraction.
"""

from __future__ import annotations

from datetime import UTC, datetime

from src.database.database_connection import DatabaseConnection
from src.database.repositories.base_repository import BaseRepository
from src.identity.exceptions import UserAlreadyExistsError, UserNotFoundError
from src.identity.models import User, UserCreate, UserRole, UserStatus, UserUpdate

_DUPLICATE_ACCOUNT_MESSAGE = "An account with this username or email address already exists."


class UserRepository(BaseRepository):
    """
    Database repository for User entity operations.
    """

    TABLE_NAME = "users"

    def __init__(self, connection: DatabaseConnection) -> None:
        super().__init__(connection)

    # ==========================================================
    # Helpers
    # ==========================================================

    def _row_to_user(self, row: dict) -> User:
        """Convert a database row dictionary to an immutable User entity."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                created_at = datetime.now(UTC)

        updated_at = row["updated_at"]
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except Exception:
                updated_at = datetime.now(UTC)

        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            hashed_password=row["hashed_password"],
            role=UserRole.from_string(row["role"]),
            status=UserStatus.from_string(row["status"]),
            created_at=created_at,
            updated_at=updated_at,
            token_version=int(row.get("token_version") or 0),
        )

    # ==========================================================
    # Public API
    # ==========================================================

    def get_by_id(self, user_id: int) -> User | None:  # type: ignore[override]
        """Retrieve user by primary ID."""
        query = f"""
        SELECT *
        FROM {self.TABLE_NAME}
        WHERE id = ?;
        """
        row = self.fetch_one(query, (user_id,))
        if row is None:
            return None
        return self._row_to_user(row)

    def get_by_username(self, username: str) -> User | None:
        """Retrieve user by unique username (case-insensitive)."""
        query = f"""
        SELECT *
        FROM {self.TABLE_NAME}
        WHERE LOWER(username) = LOWER(?);
        """
        row = self.fetch_one(query, (username.strip(),))
        if row is None:
            return None
        return self._row_to_user(row)

    def get_by_email(self, email: str) -> User | None:
        """Retrieve user by unique email address (case-insensitive)."""
        query = f"""
        SELECT *
        FROM {self.TABLE_NAME}
        WHERE LOWER(email) = LOWER(?);
        """
        row = self.fetch_one(query, (email.strip(),))
        if row is None:
            return None
        return self._row_to_user(row)

    def create(self, user_create: UserCreate, hashed_password: str) -> User:
        """Create and persist a new user entity."""
        # Generic on purpose (L3): the message must not say which field clashed.
        if self.get_by_username(user_create.username) is not None or self.get_by_email(user_create.email) is not None:
            raise UserAlreadyExistsError(_DUPLICATE_ACCOUNT_MESSAGE)

        now = datetime.now(UTC).isoformat()

        query = f"""
        INSERT INTO {self.TABLE_NAME}(
            username,
            email,
            hashed_password,
            role,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """

        try:
            user_id = self.insert_and_return_id(
                query,
                (
                    user_create.username.strip(),
                    user_create.email.strip().lower(),
                    hashed_password,
                    user_create.role.value,
                    UserStatus.ACTIVE.value,
                    now,
                    now,
                ),
            )
        except Exception as exc:
            # A concurrent registration that passed the checks above is caught
            # by the case-insensitive unique indexes (L6).
            if type(exc).__name__ in {"IntegrityError", "UniqueViolation"}:
                raise UserAlreadyExistsError(_DUPLICATE_ACCOUNT_MESSAGE) from exc
            raise

        created_user = self.get_by_id(user_id)
        if created_user is None:
            raise RuntimeError("Failed to retrieve created user from database.")
        return created_user

    def update(
        self,
        user_id: int,
        user_update: UserUpdate,
        hashed_password: str | None = None,
    ) -> User:
        """Update an existing user entity."""
        existing = self.get_by_id(user_id)
        if existing is None:
            raise UserNotFoundError(f"User with id {user_id} does not exist.")

        if user_update.email is not None:
            email_user = self.get_by_email(user_update.email)
            if email_user is not None and email_user.id != user_id:
                raise UserAlreadyExistsError(f"Email '{user_update.email}' is already in use by another user.")

        new_email = user_update.email.strip().lower() if user_update.email is not None else existing.email
        new_role = user_update.role.value if user_update.role is not None else existing.role.value
        new_status = user_update.status.value if user_update.status is not None else existing.status.value
        new_hash = hashed_password if hashed_password is not None else existing.hashed_password
        now = datetime.now(UTC).isoformat()

        query = f"""
        UPDATE {self.TABLE_NAME}
        SET email = ?,
            role = ?,
            status = ?,
            hashed_password = ?,
            updated_at = ?
        WHERE id = ?;
        """

        self.execute(
            query,
            (
                new_email,
                new_role,
                new_status,
                new_hash,
                now,
                user_id,
            ),
        )

        updated_user = self.get_by_id(user_id)
        if updated_user is None:
            raise RuntimeError("Failed to retrieve updated user from database.")
        return updated_user

    def bump_token_version(self, user_id: int) -> None:
        """Invalidate every outstanding token of the user (I2)."""
        self.execute(
            f"UPDATE {self.TABLE_NAME} SET token_version = token_version + 1 WHERE id = ?;",
            (user_id,),
        )

    def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        existing = self.get_by_id(user_id)
        if existing is None:
            return False

        query = f"""
        DELETE FROM {self.TABLE_NAME}
        WHERE id = ?;
        """
        self.execute(query, (user_id,))
        return True

    def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """List all users with pagination."""
        query = f"""
        SELECT *
        FROM {self.TABLE_NAME}
        ORDER BY id ASC
        LIMIT ? OFFSET ?;
        """
        rows = self.fetch_all(query, (limit, offset))
        return [self._row_to_user(row) for row in rows]

    def count_active_admins(self) -> int:
        """Count ACTIVE users with the ADMIN role (all of them, not one page)."""
        row = self.fetch_one(
            f"SELECT COUNT(*) as total FROM {self.TABLE_NAME} WHERE role = ? AND status = ?;",
            (UserRole.ADMIN.value, UserStatus.ACTIVE.value),
        )
        return 0 if row is None else int(row.get("total", 0))

    def count(self) -> int:
        """Return total user count."""
        query = f"""
        SELECT COUNT(*) as total
        FROM {self.TABLE_NAME};
        """
        row = self.fetch_one(query)
        if row is None:
            return 0
        return int(row.get("total", 0))
