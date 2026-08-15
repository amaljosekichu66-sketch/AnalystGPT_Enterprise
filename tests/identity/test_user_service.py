"""
Unit tests for UserService in AnalystGPT Enterprise.
"""

from __future__ import annotations

import pytest

from src.identity.exceptions import (
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserDisabledError,
)
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import (
    UserCreate,
    UserLogin,
    UserRole,
    UserStatus,
    UserUpdate,
)
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import UserService


@pytest.fixture
def user_service() -> UserService:
    repo = InMemoryUserRepository()
    hasher = PBKDF2PasswordHasher()
    token_svc = TokenService(secret_key="test-secret-for-user-service-tests")
    revocation_svc = TokenRevocationService()
    return UserService(
        user_repository=repo,
        password_hasher=hasher,
        token_service=token_svc,
        revocation_service=revocation_svc,
    )


class TestUserService:
    """Test suite for domain user service."""

    def test_register_user_success(self, user_service: UserService) -> None:
        user_create = UserCreate(
            username="analyst_jane",
            email="jane@enterprise.com",
            password="SecurePassword123!",
            role=UserRole.ANALYST,
        )

        user = user_service.register_user(user_create)
        assert user.id == 1
        assert user.username == "analyst_jane"
        assert user.email == "jane@enterprise.com"
        assert user.role == UserRole.ANALYST
        assert user.status == UserStatus.ACTIVE
        assert user.hashed_password != "SecurePassword123!"
        assert user.hashed_password.startswith("$pbkdf2-sha256$")

    def test_register_duplicate_username_raises_error(
        self, user_service: UserService
    ) -> None:
        user_service.register_user(
            UserCreate(
                username="duplicate_user",
                email="orig@enterprise.com",
                password="SecurePassword123!",
            )
        )

        with pytest.raises(UserAlreadyExistsError, match="Username 'duplicate_user' is already registered"):
            user_service.register_user(
                UserCreate(
                    username="duplicate_user",
                    email="other@enterprise.com",
                    password="SecurePassword123!",
                )
            )

    def test_register_duplicate_email_raises_error(
        self, user_service: UserService
    ) -> None:
        user_service.register_user(
            UserCreate(
                username="user_one",
                email="same@enterprise.com",
                password="SecurePassword123!",
            )
        )

        with pytest.raises(UserAlreadyExistsError, match="Email address 'same@enterprise.com' is already registered"):
            user_service.register_user(
                UserCreate(
                    username="user_two",
                    email="same@enterprise.com",
                    password="SecurePassword123!",
                )
            )

    def test_authenticate_user_by_username_success(
        self, user_service: UserService
    ) -> None:
        user_service.register_user(
            UserCreate(
                username="auth_tester",
                email="auth@enterprise.com",
                password="MyPassword123!",
            )
        )

        authenticated = user_service.authenticate_user(
            username_or_email="auth_tester",
            password="MyPassword123!",
        )
        assert authenticated.username == "auth_tester"

    def test_authenticate_user_by_email_success(
        self, user_service: UserService
    ) -> None:
        user_service.register_user(
            UserCreate(
                username="email_tester",
                email="email_auth@enterprise.com",
                password="MyPassword123!",
            )
        )

        authenticated = user_service.authenticate_user(
            username_or_email="email_auth@enterprise.com",
            password="MyPassword123!",
        )
        assert authenticated.username == "email_tester"

    def test_authenticate_wrong_password_raises_invalid_credentials(
        self, user_service: UserService
    ) -> None:
        user_service.register_user(
            UserCreate(
                username="wrong_pass_user",
                email="wrong_pass@enterprise.com",
                password="CorrectPassword123!",
            )
        )

        with pytest.raises(InvalidCredentialsError, match="Invalid username or password"):
            user_service.authenticate_user(
                username_or_email="wrong_pass_user",
                password="WrongPassword123!",
            )

    def test_authenticate_nonexistent_user_raises_invalid_credentials(
        self, user_service: UserService
    ) -> None:
        with pytest.raises(InvalidCredentialsError, match="Invalid username or password"):
            user_service.authenticate_user(
                username_or_email="nonexistent_user",
                password="AnyPassword123!",
            )

    def test_authenticate_suspended_or_inactive_user_raises_disabled(
        self, user_service: UserService
    ) -> None:
        user = user_service.register_user(
            UserCreate(
                username="suspended_user",
                email="suspended@enterprise.com",
                password="Password123!",
            )
        )

        # Update status to suspended
        user_service._user_repository.update(
            user.id, UserUpdate(status=UserStatus.SUSPENDED)
        )

        with pytest.raises(UserDisabledError, match="suspended"):
            user_service.authenticate_user("suspended_user", "Password123!")

    def test_login_workflow(self, user_service: UserService) -> None:
        user_service.register_user(
            UserCreate(
                username="login_analyst",
                email="login@enterprise.com",
                password="LoginPassword123!",
                role=UserRole.ADMIN,
            )
        )

        user, token, expires_in = user_service.login(
            UserLogin(username="login_analyst", password="LoginPassword123!")
        )

        assert user.username == "login_analyst"
        assert isinstance(token, str)
        assert expires_in > 0

    def test_get_current_user_from_token(self, user_service: UserService) -> None:
        created = user_service.register_user(
            UserCreate(
                username="token_resolver",
                email="resolver@enterprise.com",
                password="Password123!",
            )
        )

        _, token, _ = user_service.login(
            UserLogin(username="token_resolver", password="Password123!")
        )

        resolved = user_service.get_current_user_from_token(token)
        assert resolved.id == created.id
        assert resolved.username == "token_resolver"

    def test_logout_revokes_token(self, user_service: UserService) -> None:
        user_service.register_user(
            UserCreate(
                username="logout_user",
                email="logout@enterprise.com",
                password="Password123!",
            )
        )

        _, token, _ = user_service.login(
            UserLogin(username="logout_user", password="Password123!")
        )

        # Before logout, token is valid
        resolved = user_service.get_current_user_from_token(token)
        assert resolved.username == "logout_user"

        # Logout
        assert user_service.logout(token) is True

        # After logout, token must be rejected
        with pytest.raises(InvalidTokenError, match="revoked"):
            user_service.get_current_user_from_token(token)
