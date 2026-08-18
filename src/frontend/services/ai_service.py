"""
AI Frontend Service for AnalystGPT Enterprise.

Provides presentation-layer service methods for AI job state checking,
report retrieval, and retry execution.

Sprint 14 Phase 2 — Asynchronous AI Execution, Persistent Job Lifecycle & Performance
Sprint 14 Remediation — AI Insights + Enterprise Reporting Reliability Remediation.
"""

from __future__ import annotations

from typing import Any

from src.core.logger import logger
from src.frontend.services.api_client import APIClient
from src.frontend.services.session_manager import get_ai_job_id, set_ai_job_id


def get_ai_job_status(job_id: str | None = None) -> dict[str, Any]:
    """
    Retrieve current AI job status and report data from backend API.

    Uses specific job_id if provided or cached in session_state, falling back to latest.
    """
    target_job_id = job_id or get_ai_job_id()
    client = APIClient()
    try:
        if target_job_id:
            data = client.get_ai_job(target_job_id)
        else:
            data = client.get_latest_ai_job()

        eff_job_id = data.get("job_id") or target_job_id
        if eff_job_id:
            set_ai_job_id(eff_job_id)

        ai_report = data.get("ai_report")
        if data.get("status") == "READY" and ai_report:
            from src.frontend.services.session_manager import set_ai_report

            set_ai_report(ai_report)

        return {
            "success": True,
            "job_id": eff_job_id,
            "status": data.get("status", "PENDING"),
            "provider": data.get("provider", "ollama"),
            "model": data.get("model", "gemma3:4b"),
            "attempt_count": data.get("attempt_count", 0),
            "max_attempts": data.get("max_attempts", 3),
            "error": data.get("error"),
            "failure_category": data.get("failure_category"),
            "ai_report": ai_report,
            "created_at": data.get("created_at"),
            "started_at": data.get("started_at"),
            "completed_at": data.get("completed_at"),
            "is_auth_error": False,
        }
    except Exception as exc:
        logger.warning("Unable to fetch AI job status for '%s': %s", target_job_id, exc)
        err_str = str(exc)
        is_auth_err = (
            "401" in err_str
            or "unauthorized" in err_str.lower()
            or "expired" in err_str.lower()
            or "invalid credentials" in err_str.lower()
        )
        status_val = "UNAUTHORIZED" if is_auth_err else "NOT_FOUND"
        return {
            "success": False,
            "job_id": target_job_id,
            "status": status_val,
            "error": err_str,
            "is_auth_error": is_auth_err,
            "ai_report": None,
        }
    finally:
        client.close()


def retry_ai_job(job_id: str) -> dict[str, Any]:
    """
    Request the backend to retry a failed AI job.
    """
    client = APIClient()
    try:
        response = client.retry_ai_job(job_id)
        return {
            "success": response.get("success", True),
            "message": response.get("message", "Retry scheduled successfully."),
            "status": response.get("status", "PENDING"),
            "job_id": job_id,
        }
    except Exception as exc:
        logger.error("Failed to retry AI job '%s': %s", job_id, exc)
        return {
            "success": False,
            "message": f"Retry failed: {exc}",
            "job_id": job_id,
        }
    finally:
        client.close()
