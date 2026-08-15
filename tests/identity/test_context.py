"""
Tests for UserContext and request context variable management.
"""

from __future__ import annotations

from src.identity.context import (
    UserContext,
    get_current_user_context,
    set_current_user_context,
)
from src.identity.models import User, UserRole, UserStatus
from src.identity.permissions import Permission


class TestUserContext:
    """Test UserContext behavior and contextvar helpers."""

    def test_anonymous_context(self) -> None:
        anon = UserContext.anonymous()
        assert anon.is_authenticated is False
        assert anon.user_id is None
        assert anon.username == "anonymous"
        assert anon.role == UserRole.VIEWER
        assert anon.has_permission(Permission.DATASET_UPLOAD) is False
        assert anon.has_permission(Permission.DASHBOARD_VIEW) is False

    def test_system_context(self) -> None:
        sys = UserContext.system()
        assert sys.is_authenticated is True
        assert sys.is_admin is True
        assert sys.user_id == 0
        assert sys.username == "system"
        assert sys.has_permission(Permission.DATASET_UPLOAD) is True
        assert sys.has_permission(Permission.USER_MANAGE) is True

    def test_from_user_factory(self) -> None:
        user = User(
            id=10,
            username="analyst_bob",
            email="bob@enterprise.com",
            hashed_password="$pbkdf2-sha256$mock",
            role=UserRole.ANALYST,
            status=UserStatus.ACTIVE,
        )
        context = UserContext.from_user(user)
        assert context.user_id == 10
        assert context.username == "analyst_bob"
        assert context.email == "bob@enterprise.com"
        assert context.role == UserRole.ANALYST
        assert context.is_authenticated is True
        assert context.is_active is True
        assert context.is_analyst is True
        assert context.has_permission(Permission.PIPELINE_EXECUTE) is True
        assert context.has_permission(Permission.USER_MANAGE) is False

    def test_inactive_user_context_denies_all_permissions(self) -> None:
        context = UserContext(
            user_id=11,
            username="disabled_user",
            email="disabled@enterprise.com",
            role=UserRole.ADMIN,
            status=UserStatus.SUSPENDED,
            is_authenticated=True,
        )
        assert context.is_active is False
        # Even with ADMIN role, suspended status revokes permission evaluation
        assert context.has_permission(Permission.SYSTEM_ADMIN) is False

    def test_contextvar_set_and_get(self) -> None:
        initial = get_current_user_context()
        assert initial.is_authenticated is False

        new_context = UserContext(
            user_id=99,
            username="context_user",
            email="context@test.com",
            role=UserRole.ANALYST,
            status=UserStatus.ACTIVE,
            is_authenticated=True,
        )
        set_current_user_context(new_context)
        retrieved = get_current_user_context()
        assert retrieved.user_id == 99
        assert retrieved.username == "context_user"
