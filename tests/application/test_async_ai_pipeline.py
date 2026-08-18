"""
Integration tests for asynchronous AI execution and failure isolation in Application.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ai.ai_manager import AIManager
from src.ai.ai_report import AIReport
from src.ai.ai_result import AIResult
from src.ai.models import AIJobStatus
from src.application.app import Application
from src.application.pipeline_result import PipelineResult

SAMPLE_DATASET = Path("sample_data/customer_data.csv")


def test_application_run_asynchronous_decoupling() -> None:
    """
    Verify Application.run() completes deterministically without waiting for AI generation.
    """
    app = Application()

    mock_report = AIReport(
        executive_summary="Async summary",
        recommendations=["Rec 1"],
        explanations=["Expl 1"],
        narrative="Narrative 1",
        model="gemma3:4b",
        provider="ollama",
        execution_time=0.1,
    )

    # Artificially slow mock for AI generation to test non-blocking execution
    def slow_ai_generate(*args, **kwargs):
        time.sleep(2.0)
        return AIResult(success=True, ai_report=mock_report)

    try:
        with patch.object(
            AIManager, "generate_ai_report", side_effect=slow_ai_generate
        ):
            start_time = time.perf_counter()
            result = app.run(str(SAMPLE_DATASET))
            elapsed = time.perf_counter() - start_time

            # Core pipeline must finish in < 1.5s regardless of 2.0s slow AI
            assert (
                elapsed < 1.5
            ), f"Pipeline execution took {elapsed:.4f}s, expected < 1.5s"

            assert isinstance(result, PipelineResult)
            assert result.success is True
            assert result.pipeline_report is not None
            assert result.output_path is not None
            assert Path(result.output_path).exists()
            assert result.ai_job_id is not None
            assert result.ai_job_status in {"PENDING", "GENERATING"}
    finally:
        app.shutdown()


def test_ai_failure_does_not_fail_pipeline() -> None:
    """
    Verify AI failure does NOT cause Application.run() to fail.
    Core architectural invariant: AI failure != pipeline failure.
    """
    app = Application()

    try:
        # Mock total AI provider outage
        with patch.object(
            AIManager,
            "generate_ai_report",
            side_effect=ConnectionError("Ollama service down"),
        ), patch("threading.Timer"):
            result = app.run(str(SAMPLE_DATASET))

            assert result.success is True
            assert result.error is None
            assert result.pipeline_report is not None
            assert result.output_path is not None
    finally:
        app.shutdown()


def test_ai_job_persisted_in_database() -> None:
    """
    Verify that an ai_jobs database record is created with correct metadata upon pipeline run.
    """
    app = Application()

    mock_report = AIReport(
        executive_summary="Async summary",
        recommendations=["Rec 1"],
        explanations=["Expl 1"],
        narrative="Narrative 1",
        model="gemma3:4b",
        provider="ollama",
        execution_time=0.1,
    )

    try:
        with patch.object(
            AIManager,
            "generate_ai_report",
            return_value=AIResult(success=True, ai_report=mock_report),
        ):
            result = app.run(str(SAMPLE_DATASET))

            assert result.ai_job_id is not None
            assert result.ai_job_status in {"PENDING", "GENERATING"}

            # Give worker a moment to process or inspect repository
            time.sleep(0.2)
            job = app.ai_job_service.get_job(result.ai_job_id)
            assert job is not None
            assert job.job_id == result.ai_job_id
            assert job.provider == "ollama"
            assert job.model == "gemma3:4b"
    finally:
        app.shutdown()
