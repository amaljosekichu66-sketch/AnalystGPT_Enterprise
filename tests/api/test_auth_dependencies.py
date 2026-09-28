"""
Tests for API authentication and authorization dependencies and exception handlers.
"""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient

from src.api.dependencies.auth_dependencies import (
    get_current_active_user,
    get_user_context,
    require_permission,
    require_role,
)
from src.api.exceptions.exception_handlers import register_exception_handlers
from src.identity.context import UserContext
from src.identity.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    UserAlreadyExistsError,
    UserDisabledError,
    UserNotFoundError,
)
from src.identity.models import UserRole
from src.identity.permissions import Permission


@pytest.fixture
def test_app():
    """Create a minimal FastAPI test app with registered exception handlers and routes."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/public")
    async def public_endpoint(context: UserContext = Depends(get_user_context)):
        return {
            "authenticated": context.is_authenticated,
            "username": context.username,
            "role": context.role.value,
        }

    @app.get("/protected")
    async def protected_endpoint(
        context: UserContext = Depends(get_current_active_user),
    ):
        return {
            "user_id": context.user_id,
            "username": context.username,
            "role": context.role.value,
        }

    @app.get("/admin-only")
    async def admin_endpoint(
        context: UserContext = Depends(require_role(UserRole.ADMIN)),
    ):
        return {"admin": True, "username": context.username}

    @app.get("/upload-action")
    async def upload_endpoint(
        context: UserContext = Depends(require_permission(Permission.DATASET_UPLOAD)),
    ):
        return {"action": "upload_allowed", "username": context.username}

    @app.get("/trigger-user-not-found")
    async def trigger_user_not_found():
        raise UserNotFoundError("User 999 does not exist.")

    @app.get("/trigger-user-exists")
    async def trigger_user_exists():
        raise UserAlreadyExistsError("User 'admin' already exists.")

    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


class TestAuthDependencies:
    """Test auth dependencies and exception mapping."""

    def test_public_endpoint_unauthenticated(self, client: TestClient) -> None:
        response = client.get("/public")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["authenticated"] is False
        assert data["username"] == "anonymous"

    def test_public_endpoint_with_headers(self, client: TestClient) -> None:
        headers = {
            "X-User-Id": "123",
            "X-User-Name": "test_analyst",
            "X-User-Role": "ANALYST",
        }
        response = client.get("/public", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["authenticated"] is True
        assert data["username"] == "test_analyst"
        assert data["role"] == "ANALYST"

    def test_protected_endpoint_without_auth_fails_401(self, client: TestClient) -> None:
        response = client.get("/protected")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
        assert "Authentication required" in data["error"]

    def test_protected_endpoint_authenticated_success(self, client: TestClient) -> None:
        headers = {
            "X-User-Id": "42",
            "X-User-Name": "valid_user",
            "X-User-Role": "ANALYST",
        }
        response = client.get("/protected", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == 42
        assert data["username"] == "valid_user"

    def test_admin_endpoint_as_analyst_fails_403(self, client: TestClient) -> None:
        headers = {
            "X-User-Id": "10",
            "X-User-Name": "regular_analyst",
            "X-User-Role": "ANALYST",
        }
        response = client.get("/admin-only", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["success"] is False
        assert "not among allowed roles" in data["error"]

    def test_admin_endpoint_as_admin_succeeds(self, client: TestClient) -> None:
        headers = {
            "X-User-Id": "1",
            "X-User-Name": "super_admin",
            "X-User-Role": "ADMIN",
        }
        response = client.get("/admin-only", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["admin"] is True

    def test_permission_endpoint_as_viewer_fails_403(self, client: TestClient) -> None:
        headers = {
            "X-User-Id": "20",
            "X-User-Name": "viewer_user",
            "X-User-Role": "VIEWER",
        }
        response = client.get("/upload-action", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "dataset:upload" in data["error"]

    def test_permission_endpoint_as_analyst_succeeds(self, client: TestClient) -> None:
        headers = {
            "X-User-Id": "30",
            "X-User-Name": "analyst_user",
            "X-User-Role": "ANALYST",
        }
        response = client.get("/upload-action", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["action"] == "upload_allowed"

    def test_user_not_found_mapped_to_404(self, client: TestClient) -> None:
        response = client.get("/trigger-user-not-found")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
        assert "User 999 does not exist" in data["error"]

    def test_user_already_exists_mapped_to_409(self, client: TestClient) -> None:
        response = client.get("/trigger-user-exists")
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert data["success"] is False
        assert "already exists" in data["error"]
