"""
Integration test suite for Administrative User Management API endpoints.

Tests:
- GET /api/admin/users (listing & pagination)
- GET /api/admin/users/{user_id} (retrieval)
- PATCH /api/admin/users/{user_id} (role/status management)
- DELETE /api/admin/users/{user_id} (user removal)
- Last active admin protection against self-lockout / deletion
- RBAC enforcement (non-admin access denied with 403)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies.auth_dependencies import set_user_service_instance
from src.api.server import app
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import (
    UserCreate,
    UserLogin,
    UserRole,
    UserStatus,
)
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import UserService


class TestAdminUserRoutes:
    """
    Test suite for /api/admin/users endpoints.
    """

    @pytest.fixture(autouse=True)
    def setup_admin_context(self) -> None:
        self.user_repo = InMemoryUserRepository()
        self.hasher = PBKDF2PasswordHasher(iterations=10_000)
        self.token_service = TokenService(secret_key="test-secret-key-32-bytes-long!!")
        self.revocation = TokenRevocationService()
        self.user_service = UserService(self.user_repo, self.hasher, self.token_service, self.revocation)
        set_user_service_instance(self.user_service)

        # Register Primary Admin
        self.admin = self.user_service.register_user(
            UserCreate(
                username="admin_lead",
                email="admin@enterprise.com",
                password="AdminPassword123!",
                role=UserRole.ADMIN,
            )
        )

        # Register Analyst
        self.analyst = self.user_service.register_user(
            UserCreate(
                username="analyst_jane",
                email="jane@enterprise.com",
                password="AnalystPassword123!",
                role=UserRole.ANALYST,
            )
        )

        _, self.admin_token, _ = self.user_service.login(UserLogin(username="admin_lead", password="AdminPassword123!"))
        _, self.analyst_token, _ = self.user_service.login(
            UserLogin(username="analyst_jane", password="AnalystPassword123!")
        )

        self.client = TestClient(app)

    def test_admin_list_users_paginated(self) -> None:
        """Admin can list all registered users with pagination."""
        res = self.client.get(
            "/api/admin/users",
            params={"limit": 10, "offset": 0},
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["username"] == "admin_lead"
        assert data["items"][1]["username"] == "analyst_jane"
        # Ensure password hashes are NOT leaked
        assert "hashed_password" not in data["items"][0]

    def test_admin_get_user_by_id(self) -> None:
        """Admin can fetch safe profile of any user."""
        res = self.client.get(
            f"/api/admin/users/{self.analyst.id}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == self.analyst.id
        assert data["username"] == "analyst_jane"
        assert data["role"] == "ANALYST"
        assert "hashed_password" not in data

    def test_admin_get_nonexistent_user_returns_404(self) -> None:
        """Admin fetching nonexistent user receives 404 Not Found."""
        res = self.client.get(
            "/api/admin/users/99999",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        assert res.status_code == 404

    def test_admin_update_user_role_and_status(self) -> None:
        """Admin can promote an analyst to ADMIN and change status."""
        res = self.client.patch(
            f"/api/admin/users/{self.analyst.id}",
            json={"role": "ADMIN", "status": "ACTIVE"},
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "ADMIN"
        assert data["status"] == "ACTIVE"

    def test_last_active_admin_demotion_safeguard(self) -> None:
        """Attempting to demote the only active admin is blocked with 400 Bad Request."""
        res = self.client.patch(
            f"/api/admin/users/{self.admin.id}",
            json={"role": "ANALYST"},
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        assert res.status_code == 400
        assert "Cannot demote, deactivate, or suspend the last active administrator" in res.json()["error"]

    def test_last_active_admin_deactivation_safeguard(self) -> None:
        """Attempting to suspend/deactivate the only active admin is blocked with 400 Bad Request."""
        res = self.client.patch(
            f"/api/admin/users/{self.admin.id}",
            json={"status": "SUSPENDED"},
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        assert res.status_code == 400
        assert "Cannot demote, deactivate, or suspend the last active administrator" in res.json()["error"]

    def test_last_active_admin_deletion_safeguard(self) -> None:
        """Attempting to delete the only active admin is blocked with 400 Bad Request."""
        res = self.client.delete(
            f"/api/admin/users/{self.admin.id}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        assert res.status_code == 400
        assert "Cannot delete the last active administrator" in res.json()["error"]

    def test_multi_admin_allows_demotion_of_secondary_admin(self) -> None:
        """When multiple active admins exist, demoting one of them is permitted."""
        admin2 = self.user_service.register_user(
            UserCreate(
                username="admin_two",
                email="admin2@enterprise.com",
                password="Password123!",
                role=UserRole.ADMIN,
            )
        )

        res = self.client.patch(
            f"/api/admin/users/{admin2.id}",
            json={"role": "ANALYST"},
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        assert res.status_code == 200
        assert res.json()["role"] == "ANALYST"

    def test_admin_delete_user_success(self) -> None:
        """Admin can delete a normal user account."""
        res = self.client.delete(
            f"/api/admin/users/{self.analyst.id}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Verify user is gone
        get_res = self.client.get(
            f"/api/admin/users/{self.analyst.id}",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        assert get_res.status_code == 404

    def test_non_admin_cannot_access_admin_endpoints(self) -> None:
        """Analyst role receives 403 Forbidden on all admin endpoints."""
        res_list = self.client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        assert res_list.status_code == 403

        res_patch = self.client.patch(
            f"/api/admin/users/{self.analyst.id}",
            json={"role": "ADMIN"},
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        assert res_patch.status_code == 403

        res_delete = self.client.delete(
            f"/api/admin/users/{self.admin.id}",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        assert res_delete.status_code == 403
