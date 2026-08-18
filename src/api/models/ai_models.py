"""
AI API request and response schemas for AnalystGPT Enterprise.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.api.models.response_models import AIReportResponse


class AIJobResponse(BaseModel):
    """
    Standard response model for an AI generation job.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    job_id: str = Field(
        ...,
        description="Unique identifier of the AI job.",
    )

    pipeline_run_id: int = Field(
        ...,
        description="Associated pipeline execution run ID.",
    )

    status: str = Field(
        ...,
        description="Current lifecycle status: PENDING, GENERATING, READY, FAILED.",
    )

    provider: str = Field(
        ...,
        description="AI LLM provider name (e.g. ollama).",
    )

    model: str = Field(
        ...,
        description="Configured model name (e.g. gemma3:4b).",
    )

    attempt_count: int = Field(
        0,
        description="Number of execution attempts made so far.",
    )

    max_attempts: int = Field(
        3,
        description="Maximum retry attempts allowed.",
    )

    error: str | None = Field(
        None,
        description="Sanitized error description if failed.",
    )

    failure_category: str | None = Field(
        None,
        description="Failure classification category if failed.",
    )

    created_at: str | None = Field(
        None,
        description="Timestamp when the job was created.",
    )

    started_at: str | None = Field(
        None,
        description="Timestamp when the job execution started.",
    )

    completed_at: str | None = Field(
        None,
        description="Timestamp when the job completed (READY or FAILED).",
    )

    ai_report: AIReportResponse | None = Field(
        None,
        description="Generated AI insight report when status is READY.",
    )


class AIJobRetryResponse(BaseModel):
    """
    Response model for an AI job retry operation.
    """

    success: bool = Field(
        ...,
        description="Whether the retry operation was scheduled successfully.",
    )

    message: str = Field(
        ...,
        description="Human-readable status message.",
    )

    job_id: str = Field(
        ...,
        description="Target AI job ID.",
    )

    status: str = Field(
        ...,
        description="Updated status after retry schedule (e.g. PENDING).",
    )
