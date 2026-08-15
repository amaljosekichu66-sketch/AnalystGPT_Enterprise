"""
Structured Audit Trail Service for AnalystGPT Enterprise.

Responsibilities
----------------
- Record auditable security, identity, and lifecycle events.
- Strictly sanitize all event payloads to prevent credential/token leakage.
- Provide structured logging and test-accessible event storage.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from src.core.logger import logger
from src.identity.models import AuditEvent, AuditEventType

# Keys strictly forbidden in audit details to prevent credential/token leakage
_FORBIDDEN_DETAIL_KEYS = frozenset(
    {
        "password",
        "hashed_password",
        "hash",
        "salt",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "secret_key",
        "authorization",
        "cookie",
        "session",
    }
)


class AuditService:
    """
    Structured security and application audit trail service.
    """

    def __init__(self, max_in_memory_events: int = 1000) -> None:
        self._max_in_memory_events = max_in_memory_events
        self._events: list[AuditEvent] = []

    def sanitize_details(self, details: dict[str, Any] | None) -> dict[str, str | int | bool | None]:
        """
        Sanitize event details to guarantee no secrets/credentials enter logs.
        """
        if not details:
            return {}

        sanitized: dict[str, str | int | bool | None] = {}
        for key, value in details.items():
            normalized_key = key.strip().lower()
            if (
                normalized_key in _FORBIDDEN_DETAIL_KEYS
                or "password" in normalized_key
                or "token" in normalized_key
                or "secret" in normalized_key
            ):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, (str, int, bool)) or value is None:
                sanitized[key] = value
            else:
                sanitized[key] = str(value)

        return sanitized

    def record_event(
        self,
        event_type: AuditEventType,
        action: str,
        actor_id: int | None = None,
        actor_username: str | None = None,
        target_id: int | None = None,
        target_resource: str | None = None,
        outcome: str = "SUCCESS",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """
        Record and emit a structured audit event.
        """
        sanitized_details = self.sanitize_details(details)

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(UTC),
            actor_id=actor_id,
            actor_username=actor_username,
            target_id=target_id,
            target_resource=target_resource,
            action=action,
            outcome=outcome,
            details=sanitized_details,
        )

        # Store in bounded in-memory buffer (useful for testing/audit queries)
        self._events.append(event)
        if len(self._events) > self._max_in_memory_events:
            self._events.pop(0)

        logger.info(
            "AUDIT_EVENT | Type=%s | Action=%s | Actor=%s (ID=%s) | Target=%s (ID=%s) | Outcome=%s | Details=%s",
            event.event_type.value,
            event.action,
            event.actor_username or "ANONYMOUS",
            event.actor_id,
            event.target_resource or "N/A",
            event.target_id,
            event.outcome,
            event.details,
        )

        return event

    def get_events(
        self,
        event_type: AuditEventType | None = None,
        actor_id: int | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """
        Retrieve recent audit events from buffer with filtering.
        """
        matched = self._events
        if event_type is not None:
            matched = [e for e in matched if e.event_type == event_type]
        if actor_id is not None:
            matched = [e for e in matched if e.actor_id == actor_id]

        return matched[-limit:]

    def clear(self) -> None:
        """
        Clear in-memory event buffer.
        """
        self._events.clear()


# Global audit service singleton
_audit_service = AuditService()


def get_audit_service() -> AuditService:
    """
    Provide the global AuditService instance.
    """
    return _audit_service
