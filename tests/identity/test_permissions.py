"""
Tests for role-to-permission mapping and RBAC evaluation helpers.
"""

from __future__ import annotations

from src.identity.models import UserRole
from src.identity.permissions import (
    Permission,
    get_role_permissions,
    has_permission,
)


class TestPermissions:
    """Test RBAC permission matrix and evaluation."""

    def test_admin_has_all_permissions(self) -> None:
        admin_perms = get_role_permissions(UserRole.ADMIN)
        for perm in Permission:
            assert perm in admin_perms
            assert has_permission(UserRole.ADMIN, perm) is True

    def test_analyst_permissions(self) -> None:
        analyst_perms = get_role_permissions(UserRole.ANALYST)

        # Granted permissions
        assert Permission.DATASET_UPLOAD in analyst_perms
        assert Permission.PIPELINE_EXECUTE in analyst_perms
        assert Permission.REPORT_VIEW in analyst_perms
        assert Permission.REPORT_EXPORT in analyst_perms
        assert Permission.AI_GENERATE in analyst_perms
        assert Permission.DASHBOARD_VIEW in analyst_perms

        # Denied administrative permissions
        assert Permission.USER_MANAGE not in analyst_perms
        assert Permission.SYSTEM_ADMIN not in analyst_perms

        assert has_permission(UserRole.ANALYST, Permission.DATASET_UPLOAD) is True
        assert has_permission(UserRole.ANALYST, Permission.USER_MANAGE) is False

    def test_viewer_permissions(self) -> None:
        viewer_perms = get_role_permissions(UserRole.VIEWER)

        # Granted read-only permissions
        assert Permission.REPORT_VIEW in viewer_perms
        assert Permission.DASHBOARD_VIEW in viewer_perms

        # Denied mutation and admin permissions
        assert Permission.DATASET_UPLOAD not in viewer_perms
        assert Permission.PIPELINE_EXECUTE not in viewer_perms
        assert Permission.REPORT_EXPORT not in viewer_perms
        assert Permission.AI_GENERATE not in viewer_perms
        assert Permission.USER_MANAGE not in viewer_perms
        assert Permission.SYSTEM_ADMIN not in viewer_perms

        assert has_permission(UserRole.VIEWER, Permission.DASHBOARD_VIEW) is True
        assert has_permission(UserRole.VIEWER, Permission.DATASET_UPLOAD) is False
