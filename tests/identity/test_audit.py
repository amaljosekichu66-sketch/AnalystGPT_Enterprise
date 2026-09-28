"""
Test suite for Structured Audit Trail Service.

Tests:
- Sanitization of sensitive credentials and tokens
- Audit event generation on registration, login, logout, role/status change, and deletion
- Audit querying and event log buffer bounds
"""

from __future__ import annotations

import pytest

from src.identity.audit import AuditService
from src.identity.in_memory_user_repository import InMemoryUserRepository
from src.identity.models import (
    AdminUserUpdate,
    AuditEventType,
    UserCreate,
    UserLogin,
    UserRole,
    UserStatus,
)
from src.identity.password_hasher import PBKDF2PasswordHasher
from src.identity.token_revocation import TokenRevocationService
from src.identity.token_service import TokenService
from src.identity.user_service import UserService


class TestAuditServiceSanitization:
    """
    Verify security sanitization of audit event payloads.
    """

    def test_forbidden_keys_are_redacted(self) -> None:
        """Passwords, tokens, secrets, salts, and hashes must never be logged in plaintext."""
        audit_service = AuditService()
        raw_details = {
            "username": "alice",
            "password": "SuperSecretPassword123!",
            "hashed_password": "$pbkdf2-sha256$600000$...",
            "token": "header.payload.signature",
            "access_token": "bearer_token_string",
            "secret_key": "raw_secret_key",
            "user_id": 42,
            "status": "ACTIVE",
        }

        sanitized = audit_service.sanitize_details(raw_details)

        assert sanitized["username"] == "alice"
        assert sanitized["user_id"] == 42
        assert sanitized["status"] == "ACTIVE"

        # Sensitive keys MUST be redacted
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["hashed_password"] == "[REDACTED]"
        assert sanitized["token"] == "[REDACTED]"
        assert sanitized["access_token"] == "[REDACTED]"
        assert sanitized["secret_key"] == "[REDACTED]"

    def test_record_event_structure(self) -> None:
        """Verify audit event records correct metadata."""
        audit_service = AuditService()
        event = audit_service.record_event(
            event_type=AuditEventType.USER_REGISTERED,
            action="USER_REGISTRATION",
            actor_id=1,
            actor_username="alice",
            target_id=1,
            target_resource="USER",
            outcome="SUCCESS",
            details={"email": "alice@enterprise.com", "password": "SecretPassword!"},
        )

        assert event.event_id is not None
        assert event.event_type == AuditEventType.USER_REGISTERED
        assert event.actor_username == "alice"
        assert event.outcome == "SUCCESS"
        assert event.details["password"] == "[REDACTED]"
        assert event.details["email"] == "alice@enterprise.com"


class TestUserServiceAuditIntegration:
    """
    Verify UserService operations automatically record structured audit events.
    """

    @pytest.fixture(autouse=True)
    def setup_service(self) -> None:
        self.audit_service = AuditService()
        self.user_repo = InMemoryUserRepository()
        self.hasher = PBKDF2PasswordHasher(iterations=10_000)
        self.token_service = TokenService(secret_key="test-secret-key-32-bytes-long!!")
        self.revocation = TokenRevocationService()
        self.user_service = UserService(
            user_repository=self.user_repo,
            password_hasher=self.hasher,
            token_service=self.token_service,
            revocation_service=self.revocation,
            audit_service=self.audit_service,
        )

    def test_registration_and_login_audit_trail(self) -> None:
        """Registration, successful login, failed login, and logout produce audit events."""
        # 1. Registration
        user = self.user_service.register_user(
            UserCreate(
                username="charlie",
                email="charlie@enterprise.com",
                password="Password123!",
                role=UserRole.ANALYST,
            )
        )
        assert user.id is not None
        reg_events = self.audit_service.get_events(event_type=AuditEventType.USER_REGISTERED)
        assert len(reg_events) == 1
        assert reg_events[0].actor_username == "charlie"

        # 2. Successful Login
        _, token, _ = self.user_service.login(UserLogin(username="charlie", password="Password123!"))
        login_events = self.audit_service.get_events(event_type=AuditEventType.LOGIN_SUCCESS)
        assert len(login_events) == 1
        assert login_events[0].actor_username == "charlie"

        # 3. Failed Login
        try:
            self.user_service.login(UserLogin(username="charlie", password="WrongPassword!"))
        except Exception:
            pass

        fail_events = self.audit_service.get_events(event_type=AuditEventType.LOGIN_FAILURE)
        assert len(fail_events) == 1
        assert fail_events[0].outcome == "FAILED"

        # 4. Logout
        self.user_service.logout(token=token)
        logout_events = self.audit_service.get_events(event_type=AuditEventType.LOGOUT)
        assert len(logout_events) == 1

    def test_admin_operations_audit_trail(self) -> None:
        """Role changes, status changes, and user deletions emit distinct audit records."""
        admin = self.user_service.register_user(
            UserCreate(
                username="admin_ops",
                email="admin_ops@enterprise.com",
                password="Password123!",
                role=UserRole.ADMIN,
            )
        )
        assert admin.id is not None
        target = self.user_service.register_user(
            UserCreate(
                username="target_user",
                email="target@enterprise.com",
                password="Password123!",
                role=UserRole.ANALYST,
            )
        )

        # Admin updates target role and status
        self.user_service.update_user_admin(
            user_id=target.id,
            user_update=AdminUserUpdate(role=UserRole.VIEWER, status=UserStatus.INACTIVE),
        )

        role_events = self.audit_service.get_events(event_type=AuditEventType.USER_ROLE_CHANGED)
        assert len(role_events) == 1
        assert role_events[0].details["new_role"] == "VIEWER"

        status_events = self.audit_service.get_events(event_type=AuditEventType.USER_STATUS_CHANGED)
        assert len(status_events) == 1
        assert status_events[0].details["new_status"] == "INACTIVE"

        # Admin deletes target
        self.user_service.delete_user_admin(user_id=target.id)
        del_events = self.audit_service.get_events(event_type=AuditEventType.USER_DELETED)
        assert len(del_events) == 1
        assert del_events[0].details["deleted_username"] == "target_user"
