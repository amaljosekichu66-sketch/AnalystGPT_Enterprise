"""
Structured Audit Trail Service for AnalystGPT Enterprise.

Responsibilities
----------------
- Record auditable security, identity, and lifecycle events.
- Strictly sanitize all event payloads to prevent credential/token leakage.
- Provide structured logging and test-accessible event storage.
"""

from __future__ import annotations

import threading
import time
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

    def __init__(self, max_in_memory_events: int = 1000, sink: Any | None = None) -> None:
        self._throttle_last: dict[str, float] = {}
        self._throttle_lock = threading.Lock()
        self._max_in_memory_events = max_in_memory_events
        self._events: list[AuditEvent] = []
        #: Durable store (SEC-25). None = in-memory only (unit tests).
        self._sink = sink

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

        if self._sink is not None:
            try:
                self._sink.write(event)
            except Exception:
                # Never fail the audited operation because the audit store is
                # down - but make the gap loud.
                logger.error("SECURITY_ALERT | AUDIT_PERSIST_FAILED | event_id=%s", event.event_id, exc_info=True)

        if _is_alertable(event):
            logger.warning(
                "SECURITY_ALERT | Type=%s | Action=%s | Actor=%s (ID=%s) | Target=%s (ID=%s) | Outcome=%s | Details=%s",
                event.event_type.value,
                event.action,
                event.actor_username or "ANONYMOUS",
                event.actor_id,
                event.target_resource or "N/A",
                event.target_id,
                event.outcome,
                event.details,
            )

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

    def record_event_throttled(self, throttle_key: str, interval_seconds: float, **event: Any) -> AuditEvent | None:
        """
        Record at most one event per `throttle_key` per `interval_seconds` (L13).

        For events an unauthenticated caller can trigger at will (rejected
        tokens, rate-limit hits): each one is a database write, so recording
        every occurrence would turn the audit trail into a write amplifier.
        """
        now = time.monotonic()
        with self._throttle_lock:
            last = self._throttle_last.get(throttle_key)
            if last is not None and now - last < interval_seconds:
                return None
            self._throttle_last[throttle_key] = now
            if len(self._throttle_last) > 10_000:
                cutoff = now - interval_seconds
                self._throttle_last = {k: v for k, v in self._throttle_last.items() if v >= cutoff}
        return self.record_event(**event)

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


#: Events that warrant attention. They are logged at WARNING with a fixed
#: `SECURITY_ALERT` prefix so a log pipeline can alert on them.
_ALERT_EVENT_TYPES = frozenset(
    {
        AuditEventType.ACCESS_DENIED,
        AuditEventType.USER_ROLE_CHANGED,
        AuditEventType.USER_STATUS_CHANGED,
        AuditEventType.USER_DELETED,
        AuditEventType.ADMIN_CROSS_TENANT_ACCESS,
        AuditEventType.ADMIN_OPERATION_BLOCKED,
        AuditEventType.RATE_LIMITED,
    }
)


def _is_alertable(event: AuditEvent) -> bool:
    if event.event_type in _ALERT_EVENT_TYPES:
        return True
    return event.event_type == AuditEventType.LOGIN_FAILURE and event.outcome == "DENIED"


def _default_sink() -> Any:
    from src.identity.audit_store import DatabaseAuditSink

    return DatabaseAuditSink()


# Global audit service singleton: persisted to `audit_events` (SEC-25).
_audit_service = AuditService(sink=_default_sink())


def get_audit_service() -> AuditService:
    """
    Provide the global AuditService instance.
    """
    return _audit_service
