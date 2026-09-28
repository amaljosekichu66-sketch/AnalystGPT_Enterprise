"""
Execution result for the AI Insight Engine.

Represents the outcome of AI generation together with
execution metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.ai.ai_report import AIReport


@dataclass(
    frozen=True,
    slots=True,
)
class AIResult:
    """
    Immutable execution result returned by the
    AI Insight Engine.
    """

    # ==========================================================
    # Status
    # ==========================================================

    success: bool

    # ==========================================================
    # Business Output
    # ==========================================================

    ai_report: AIReport | None = None

    # ==========================================================
    # Execution Metadata
    # ==========================================================

    execution_time: float = 0.0

    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # ==========================================================
    # Error
    # ==========================================================

    error: Exception | None = None

    # ==========================================================
    # Serialization
    # ==========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "success": self.success,
            "execution_time": self.execution_time,
            "generated_at": (self.generated_at.isoformat()),
            "ai_report": (self.ai_report.to_dict() if self.ai_report else None),
            "error": (str(self.error) if self.error else None),
        }
