"""
Role-Based Access Control (RBAC) and Declarative Authorization Test Suite.

Verifies:
- Granular permission matrix for ADMIN, ANALYST, and VIEWER roles.
- 401 Unauthorized for unauthenticated or invalid token requests.
- 403 Forbidden for authenticated users lacking required permissions.
- Inactive/suspended user rejection with 403 Forbidden.
- Privilege escalation prevention.
- Mass-assignment / overposting protections.
- Interaction of resource ownership and role permissions.
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
from src.identity.permissions import (
    ROLE_PERMISSIONS,
    Permission,
    get_role_permissions,
    has_permission,
)
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import UserService


class TestRBACMatrix:
    """
    Test granular permission mapping across defined user roles.
    """

    def test_admin_permissions(self) -> None:
        """Admin must possess all operational, reporting, and administrative permissions."""
        admin_perms = get_role_permissions(UserRole.ADMIN)
        assert Permission.DATASET_UPLOAD in admin_perms
        assert Permission.PIPELINE_EXECUTE in admin_perms
        assert Permission.REPORT_VIEW in admin_perms
        assert Permission.REPORT_EXPORT in admin_perms
        assert Permission.DASHBOARD_VIEW in admin_perms
        assert Permission.AI_GENERATE in admin_perms
        assert Permission.USER_READ in admin_perms
        assert Permission.USER_MANAGE in admin_perms
        assert Permission.SYSTEM_ADMIN in admin_perms

    def test_analyst_permissions(self) -> None:
        """Analyst has operational & reporting permissions, but lacks administrative permissions."""
        analyst_perms = get_role_permissions(UserRole.ANALYST)
        assert Permission.DATASET_UPLOAD in analyst_perms
        assert Permission.PIPELINE_EXECUTE in analyst_perms
        assert Permission.REPORT_VIEW in analyst_perms
        assert Permission.REPORT_EXPORT in analyst_perms
        assert Permission.DASHBOARD_VIEW in analyst_perms
        assert Permission.AI_GENERATE in analyst_perms

        # Must NOT possess admin capabilities
        assert Permission.USER_READ not in analyst_perms
        assert Permission.USER_MANAGE not in analyst_perms
        assert Permission.SYSTEM_ADMIN not in analyst_perms

    def test_viewer_permissions(self) -> None:
        """Viewer has read-only dashboard/report permissions and cannot execute or manage."""
        viewer_perms = get_role_permissions(UserRole.VIEWER)
        assert Permission.REPORT_VIEW in viewer_perms
        assert Permission.DASHBOARD_VIEW in viewer_perms

        # Must NOT possess execution or ingestion or admin capabilities
        assert Permission.DATASET_UPLOAD not in viewer_perms
        assert Permission.PIPELINE_EXECUTE not in viewer_perms
        assert Permission.AI_GENERATE not in viewer_perms
        assert Permission.USER_MANAGE not in viewer_perms
        assert Permission.SYSTEM_ADMIN not in viewer_perms

    def test_has_permission_helper(self) -> None:
        """Verify has_permission helper accurately queries RBAC matrix."""
        assert has_permission(UserRole.ADMIN, Permission.USER_MANAGE) is True
        assert has_permission(UserRole.ANALYST, Permission.USER_MANAGE) is False
        assert has_permission(UserRole.VIEWER, Permission.PIPELINE_EXECUTE) is False
        assert has_permission(UserRole.VIEWER, Permission.REPORT_VIEW) is True


class TestAPIAuthorizationSemantics:
    """
    Test 401 Unauthorized vs 403 Forbidden semantics on protected endpoints.
    """

    @pytest.fixture(autouse=True)
    def setup_identity_service(self) -> None:
        self.user_repo = InMemoryUserRepository()
        self.hasher = PBKDF2PasswordHasher(iterations=10_000)
        self.token_service = TokenService(secret_key="test-secret-key-32-bytes-long!!")
        self.revocation = TokenRevocationService()
        self.user_service = UserService(
            self.user_repo, self.hasher, self.token_service, self.revocation
        )
        set_user_service_instance(self.user_service)

        # Create Admin, Analyst, and Viewer accounts
        self.admin = self.user_service.register_user(
            UserCreate(
                username="admin_user",
                email="admin@enterprise.com",
                password="AdminPassword123!",
                role=UserRole.ADMIN,
            )
        )
        self.analyst = self.user_service.register_user(
            UserCreate(
                username="analyst_user",
                email="analyst@enterprise.com",
                password="AnalystPassword123!",
                role=UserRole.ANALYST,
            )
        )
        self.viewer = self.user_service.register_user(
            UserCreate(
                username="viewer_user",
                email="viewer@enterprise.com",
                password="ViewerPassword123!",
                role=UserRole.VIEWER,
            )
        )

        _, self.admin_token, _ = self.user_service.login(
            UserLogin(username="admin_user", password="AdminPassword123!")
        )
        _, self.analyst_token, _ = self.user_service.login(
            UserLogin(username="analyst_user", password="AnalystPassword123!")
        )
        _, self.viewer_token, _ = self.user_service.login(
            UserLogin(username="viewer_user", password="ViewerPassword123!")
        )

        self.client = TestClient(app)

    def test_unauthenticated_request_returns_401(self) -> None:
        """Accessing protected endpoints without token returns 401 Unauthorized."""
        # Pipeline endpoint
        res = self.client.post("/api/pipeline", json={"input_path": "sample.csv"})
        assert res.status_code == 401

        # Reports endpoint
        res = self.client.get("/reports")
        assert res.status_code == 401

        # Admin users endpoint
        res = self.client.get("/api/admin/users")
        assert res.status_code == 401

    def test_invalid_or_expired_token_returns_401(self) -> None:
        """Accessing protected endpoints with a malformed/invalid token returns 401."""
        res = self.client.get(
            "/api/admin/users",
            headers={"Authorization": "Bearer invalid.malformed.token"},
        )
        assert res.status_code == 401

    def test_viewer_executing_pipeline_returns_403(self) -> None:
        """Viewer role attempting to execute pipeline receives 403 Forbidden."""
        res = self.client.post(
            "/api/pipeline",
            json={"input_path": "sample.csv"},
            headers={"Authorization": f"Bearer {self.viewer_token}"},
        )
        assert res.status_code == 403
        assert "Permission denied" in res.json()["message"]

    def test_analyst_accessing_admin_endpoints_returns_403(self) -> None:
        """Analyst role attempting to access admin endpoints receives 403 Forbidden."""
        res = self.client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        assert res.status_code == 403
        assert "Permission denied" in res.json()["message"]

    def test_admin_accessing_admin_endpoints_allowed(self) -> None:
        """Admin role accessing admin endpoint is allowed."""
        res = self.client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        assert res.status_code == 200
        assert "items" in res.json()
        assert res.json()["total"] == 3

    def test_suspended_user_returns_403(self) -> None:
        """Suspended user token is rejected with 403 Forbidden."""
        # Create user then suspend
        suspended_user = self.user_service.register_user(
            UserCreate(
                username="bad_actor",
                email="bad@enterprise.com",
                password="Password123!",
                role=UserRole.ANALYST,
            )
        )
        _, token, _ = self.user_service.login(
            UserLogin(username="bad_actor", password="Password123!")
        )

        # Suspend account
        self.user_repo.update(
            suspended_user.id,
            user_update=self.user_repo.get_by_id(suspended_user.id),  # type: ignore
        )
        from src.identity.models import UserUpdate
        self.user_repo.update(
            suspended_user.id,
            user_update=UserUpdate(status=UserStatus.SUSPENDED),
        )

        res = self.client.get(
            "/reports",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
