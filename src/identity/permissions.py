"""
Granular permissions and Role-Based Access Control (RBAC) mapping.

Responsibilities
----------------
- Define fine-grained application permissions.
- Map permissions to high-level UserRole entities.
- Provide fast permission evaluation helpers.
"""

from __future__ import annotations

from enum import Enum

from src.identity.models import UserRole

# ==========================================================
# Application Permissions
# ==========================================================


class Permission(str, Enum):
    """
    Fine-grained permissions across application capabilities.
    """

    # Dataset & Ingestion
    DATASET_UPLOAD = "dataset:upload"

    # Pipeline & Processing
    PIPELINE_EXECUTE = "pipeline:execute"

    # Reports & Analytics
    REPORT_VIEW = "report:view"
    REPORT_EXPORT = "report:export"
    DASHBOARD_VIEW = "dashboard:view"

    # AI Insights
    AI_GENERATE = "ai:generate"

    # User & System Administration
    USER_READ = "user:read"
    USER_MANAGE = "user:manage"
    AUDIT_READ = "audit:read"
    SYSTEM_ADMIN = "system:admin"


# ==========================================================
# Role-Permission Mapping Matrix
# ==========================================================

ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.ADMIN: frozenset(
        {
            Permission.DATASET_UPLOAD,
            Permission.PIPELINE_EXECUTE,
            Permission.REPORT_VIEW,
            Permission.REPORT_EXPORT,
            Permission.DASHBOARD_VIEW,
            Permission.AI_GENERATE,
            Permission.USER_READ,
            Permission.USER_MANAGE,
            Permission.AUDIT_READ,
            Permission.SYSTEM_ADMIN,
        }
    ),
    UserRole.ANALYST: frozenset(
        {
            Permission.DATASET_UPLOAD,
            Permission.PIPELINE_EXECUTE,
            Permission.REPORT_VIEW,
            Permission.REPORT_EXPORT,
            Permission.DASHBOARD_VIEW,
            Permission.AI_GENERATE,
        }
    ),
    UserRole.VIEWER: frozenset(
        {
            Permission.REPORT_VIEW,
            Permission.DASHBOARD_VIEW,
        }
    ),
}


# ==========================================================
# Evaluation Functions
# ==========================================================


def get_role_permissions(role: UserRole) -> frozenset[Permission]:
    """
    Return all permissions granted to a given role.
    """
    return ROLE_PERMISSIONS.get(role, frozenset())


def has_permission(role: UserRole, permission: Permission) -> bool:
    """
    Return True if the given role has the specified permission.
    """
    return permission in get_role_permissions(role)
