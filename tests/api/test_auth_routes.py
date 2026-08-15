"""
API integration test suite for authentication endpoints (/api/auth/*).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.auth_dependencies import set_user_service_instance
from src.api.server import app
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import UserRole, UserStatus, UserUpdate
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import UserService


@pytest.fixture
def auth_client():
    """Create a FastAPI test client configured with an isolated in-memory UserService."""
    repo = InMemoryUserRepository()
    hasher = PBKDF2PasswordHasher()
    token_svc = TokenService(secret_key="test-api-auth-secret-key-12345")
    revocation_svc = TokenRevocationService()
    svc = UserService(
        user_repository=repo,
        password_hasher=hasher,
        token_service=token_svc,
        revocation_service=revocation_svc,
    )

    set_user_service_instance(svc)
    client = TestClient(app)

    yield client, svc

    set_user_service_instance(None)


class TestAuthRoutes:
    """Test suite for /api/auth routes."""

    # ==========================================================
    # Registration
    # ==========================================================

    def test_register_endpoint_success(self, auth_client) -> None:
        client, _ = auth_client
        payload = {
            "username": "new_analyst",
            "email": "new_analyst@enterprise.com",
            "password": "SecurePassword123!",
            "role": "ANALYST",
        }

        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "new_analyst"
        assert data["email"] == "new_analyst@enterprise.com"
        assert data["role"] == "ANALYST"
        assert data["status"] == "ACTIVE"
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_username_returns_409(self, auth_client) -> None:
        client, _ = auth_client
        payload = {
            "username": "dup_username",
            "email": "first@enterprise.com",
            "password": "SecurePassword123!",
        }
        client.post("/api/auth/register", json=payload)

        dup_payload = {
            "username": "dup_username",
            "email": "second@enterprise.com",
            "password": "SecurePassword123!",
        }
        response = client.post("/api/auth/register", json=dup_payload)
        assert response.status_code == 409

    def test_register_duplicate_email_returns_409(self, auth_client) -> None:
        client, _ = auth_client
        payload = {
            "username": "first_user",
            "email": "same_email@enterprise.com",
            "password": "SecurePassword123!",
        }
        client.post("/api/auth/register", json=payload)

        dup_payload = {
            "username": "second_user",
            "email": "same_email@enterprise.com",
            "password": "SecurePassword123!",
        }
        response = client.post("/api/auth/register", json=dup_payload)
        assert response.status_code == 409

    def test_register_invalid_password_returns_422(self, auth_client) -> None:
        client, _ = auth_client
        payload = {
            "username": "short_pass_user",
            "email": "short@enterprise.com",
            "password": "short",
        }
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 422

    # ==========================================================
    # Login
    # ==========================================================

    def test_login_endpoint_success(self, auth_client) -> None:
        client, _ = auth_client
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "username": "login_user",
                "email": "login@enterprise.com",
                "password": "LoginPassword123!",
            },
        )

        response = client.post(
            "/api/auth/login",
            json={
                "username": "login_user",
                "password": "LoginPassword123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert data["user"]["username"] == "login_user"

    def test_login_wrong_password_returns_401(self, auth_client) -> None:
        client, _ = auth_client
        client.post(
            "/api/auth/register",
            json={
                "username": "login_user_2",
                "email": "login2@enterprise.com",
                "password": "CorrectPassword123!",
            },
        )

        response = client.post(
            "/api/auth/login",
            json={
                "username": "login_user_2",
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user_returns_401(self, auth_client) -> None:
        client, _ = auth_client
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent_ghost",
                "password": "AnyPassword123!",
            },
        )
        assert response.status_code == 401

    def test_login_suspended_user_returns_403(self, auth_client) -> None:
        client, svc = auth_client
        reg_resp = client.post(
            "/api/auth/register",
            json={
                "username": "suspended_user",
                "email": "suspended@enterprise.com",
                "password": "Password123!",
            },
        )
        user_id = reg_resp.json()["id"]

        # Suspend the user
        svc._user_repository.update(user_id, UserUpdate(status=UserStatus.SUSPENDED))

        response = client.post(
            "/api/auth/login",
            json={
                "username": "suspended_user",
                "password": "Password123!",
            },
        )
        assert response.status_code == 403

    # ==========================================================
    # Current User Profile (/api/auth/me)
    # ==========================================================

    def test_get_me_authenticated_success(self, auth_client) -> None:
        client, _ = auth_client
        client.post(
            "/api/auth/register",
            json={
                "username": "profile_user",
                "email": "profile@enterprise.com",
                "password": "Password123!",
            },
        )
        login_resp = client.post(
            "/api/auth/login",
            json={
                "username": "profile_user",
                "password": "Password123!",
            },
        )
        token = login_resp.json()["access_token"]

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "profile_user"
        assert data["email"] == "profile@enterprise.com"

    def test_get_me_unauthenticated_returns_401(self, auth_client) -> None:
        client, _ = auth_client
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token_returns_401(self, auth_client) -> None:
        client, _ = auth_client
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.malformed.token"},
        )
        assert response.status_code == 401

    # ==========================================================
    # Logout & Token Invalidation
    # ==========================================================

    def test_logout_and_subsequent_request_invalidation(self, auth_client) -> None:
        client, _ = auth_client
        client.post(
            "/api/auth/register",
            json={
                "username": "logout_api_user",
                "email": "logout_api@enterprise.com",
                "password": "Password123!",
            },
        )
        login_resp = client.post(
            "/api/auth/login",
            json={
                "username": "logout_api_user",
                "password": "Password123!",
            },
        )
        token = login_resp.json()["access_token"]

        # Valid before logout
        me_resp_1 = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp_1.status_code == 200

        # Perform logout
        logout_resp = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_resp.status_code == 200
        assert logout_resp.json()["success"] is True

        # Invalid after logout
        me_resp_2 = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp_2.status_code == 401
