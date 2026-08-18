"""
AI job domain models and lifecycle state definitions for AnalystGPT Enterprise.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.ai.exceptions import AIStateTransitionError


class AIJobStatus(str, Enum):
    """
    Lifecycle status of an AI generation job.
    """

    PENDING = "PENDING"
    GENERATING = "GENERATING"
    READY = "READY"
    FAILED = "FAILED"


class AIFailureCategory(str, Enum):
    """
    Classification of AI generation failures.
    """

    TIMEOUT = "TIMEOUT"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    MODEL_ERROR = "MODEL_ERROR"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    SYSTEM_ERROR = "SYSTEM_ERROR"


# Valid state transitions for the AI job state machine
VALID_TRANSITIONS: dict[AIJobStatus, set[AIJobStatus]] = {
    AIJobStatus.PENDING: {AIJobStatus.GENERATING},
    AIJobStatus.GENERATING: {
        AIJobStatus.READY,
        AIJobStatus.FAILED,
        AIJobStatus.PENDING,
    },
    AIJobStatus.FAILED: {AIJobStatus.PENDING},
    AIJobStatus.READY: set(),  # Terminal state
}


@dataclass
class AIJob:
    """
    Persistent AI generation job domain entity.
    """

    job_id: str
    pipeline_run_id: int
    user_id: int | None = None
    report_id: int | None = None
    status: AIJobStatus = AIJobStatus.PENDING
    provider: str = "ollama"
    model: str = "gemma3:4b"
    attempt_count: int = 0
    max_attempts: int = 3
    error: str | None = None
    failure_category: AIFailureCategory | None = None
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    updated_at: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        now_str = datetime.now(UTC).isoformat()
        if self.created_at is None:
            self.created_at = now_str
        if self.updated_at is None:
            self.updated_at = now_str
        if isinstance(self.status, str) and not isinstance(
            self.status, AIJobStatus
        ):
            self.status = AIJobStatus(self.status)
        if isinstance(self.failure_category, str) and not isinstance(
            self.failure_category, AIFailureCategory
        ):
            self.failure_category = AIFailureCategory(self.failure_category)

    @property
    def is_complete(self) -> bool:
        """Return True if job is in a completed state (READY or FAILED)."""
        return self.status in {AIJobStatus.READY, AIJobStatus.FAILED}

    @property
    def is_terminal(self) -> bool:
        """Return True if job is in a terminal state (READY)."""
        return self.status == AIJobStatus.READY

    def can_transition_to(self, target_status: AIJobStatus) -> bool:
        """
        Check whether the job can transition to the given target status.
        """
        return target_status in VALID_TRANSITIONS.get(self.status, set())

    def transition_to(
        self,
        target_status: AIJobStatus,
        error: str | None = None,
        failure_category: AIFailureCategory | None = None,
    ) -> None:
        """
        Transition the job to a new status if permitted by the state machine.

        Raises
        ------
        AIStateTransitionError
            If the transition is invalid.
        """
        if not self.can_transition_to(target_status):
            raise AIStateTransitionError(
                f"Invalid transition from {self.status.value} to {target_status.value} "
                f"for AI job '{self.job_id}'."
            )

        self.status = target_status
        self.updated_at = datetime.now(UTC).isoformat()

        if target_status == AIJobStatus.GENERATING:
            self.started_at = datetime.now(UTC).isoformat()
        elif target_status == AIJobStatus.READY:
            self.completed_at = datetime.now(UTC).isoformat()
            self.error = None
            self.failure_category = None
        elif target_status == AIJobStatus.FAILED:
            self.completed_at = datetime.now(UTC).isoformat()
            self.error = error
            self.failure_category = failure_category

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the job to a serializable dictionary.
        """
        data = asdict(self)
        data["status"] = self.status.value
        data["failure_category"] = (
            self.failure_category.value if self.failure_category else None
        )
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AIJob:
        """
        Construct an AIJob entity from a dictionary.
        """
        status_val = data.get("status", AIJobStatus.PENDING)
        if isinstance(status_val, str):
            status_val = AIJobStatus(status_val)

        category_val = data.get("failure_category")
        if isinstance(category_val, str):
            category_val = AIFailureCategory(category_val)

        return cls(
            id=data.get("id"),
            job_id=data["job_id"],
            pipeline_run_id=data["pipeline_run_id"],
            user_id=data.get("user_id"),
            report_id=data.get("report_id"),
            status=status_val,
            provider=data.get("provider", "ollama"),
            model=data.get("model", "gemma3:4b"),
            attempt_count=data.get("attempt_count", 0),
            max_attempts=data.get("max_attempts", 3),
            error=data.get("error"),
            failure_category=category_val,
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            updated_at=data.get("updated_at"),
        )
