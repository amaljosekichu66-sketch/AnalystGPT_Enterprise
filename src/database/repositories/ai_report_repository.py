"""
AI Report Repository for AnalystGPT Enterprise.

Sprint 14 Phase 2 — Persistent AI Reports
Sprint 14 Phase 4 — AI Report Lineage & Provenance Tracking
Sprint 14 Remediation & Phase 2 Quality Gate — Durable Structured AI Report Persistence.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from src.ai.ai_report import AIReport
from src.database.database_connection import DatabaseConnection
from src.database.repositories.base_repository import BaseRepository


class AIReportRepository(BaseRepository):
    """
    Repository for persisting and querying generated AI business insight reports.
    """

    TABLE_NAME = "ai_reports"

    def __init__(self, connection: DatabaseConnection) -> None:
        super().__init__(connection)

    # ==========================================================
    # Save AI Report
    # ==========================================================

    def save_ai_report(
        self,
        job_id: str,
        pipeline_run_id: int,
        ai_report: AIReport,
        user_id: int | None = None,
        report_id: int | None = None,
        source_version_id: str | None = None,
        cleaned_version_id: str | None = None,
        cleaning_execution_id: str | None = None,
        context_version: str = "v1.0",
    ) -> int:
        """
        Persist a generated AIReport entity idempotently with durable provenance and full structured fields.
        """
        # Check if already persisted
        existing = self.get_by_job_id(job_id, user_id=user_id)
        if existing is not None and existing.get("id"):
            return existing["id"]

        recs_json = json.dumps(ai_report.recommendations or [])
        expls_json = json.dumps(ai_report.explanations or [])
        key_findings_json = json.dumps(ai_report.key_findings or [])
        biz_implications_json = json.dumps(ai_report.business_implications or [])
        risks_json = json.dumps(ai_report.risks or [])
        opportunities_json = json.dumps(ai_report.opportunities or [])
        actions_json = json.dumps(ai_report.actions or [])
        limitations_json = json.dumps(ai_report.limitations or [])
        confidence_str = ai_report.confidence or ""
        structured_payload_json = json.dumps(ai_report.to_dict())

        generated_at = (
            ai_report.generated_at.isoformat()
            if isinstance(ai_report.generated_at, datetime)
            else (ai_report.generated_at or datetime.now(UTC).isoformat())
        )

        query = f"""
        INSERT INTO {self.TABLE_NAME} (
            job_id,
            pipeline_run_id,
            user_id,
            report_id,
            executive_summary,
            recommendations,
            explanations,
            narrative,
            model,
            provider,
            execution_time,
            generated_at,
            source_version_id,
            cleaned_version_id,
            cleaning_execution_id,
            context_version,
            key_findings,
            business_implications,
            risks,
            opportunities,
            actions,
            limitations,
            confidence,
            structured_payload
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        try:
            return self.insert_and_return_id(
                query,
                (
                    job_id,
                    pipeline_run_id,
                    user_id,
                    report_id,
                    ai_report.executive_summary,
                    recs_json,
                    expls_json,
                    ai_report.narrative,
                    ai_report.model,
                    ai_report.provider,
                    ai_report.execution_time,
                    generated_at,
                    source_version_id,
                    cleaned_version_id,
                    cleaning_execution_id,
                    context_version,
                    key_findings_json,
                    biz_implications_json,
                    risks_json,
                    opportunities_json,
                    actions_json,
                    limitations_json,
                    confidence_str,
                    structured_payload_json,
                ),
            )
        except Exception:
            existing_after_race = self.get_by_job_id(job_id, user_id=user_id)
            if existing_after_race is not None and existing_after_race.get("id"):
                return existing_after_race["id"]
            raise

    # ==========================================================
    # Getters
    # ==========================================================

    def get_by_job_id(
        self,
        job_id: str,
        user_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Retrieve an AI report by job_id with optional user scoping.
        """
        if user_id is not None:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE job_id = ? AND user_id = ?;
            """
            row = self.fetch_one(query, (job_id, user_id))
        else:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE job_id = ?;
            """
            row = self.fetch_one(query, (job_id,))

        if row is None:
            return None

        return self._deserialize_row(row)

    def get_by_pipeline_run_id(
        self,
        pipeline_run_id: int,
        user_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Retrieve an AI report by pipeline_run_id with optional user scoping.
        """
        if user_id is not None:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE pipeline_run_id = ? AND user_id = ?;
            """
            row = self.fetch_one(query, (pipeline_run_id, user_id))
        else:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE pipeline_run_id = ?;
            """
            row = self.fetch_one(query, (pipeline_run_id,))

        if row is None:
            return None

        return self._deserialize_row(row)

    def get_latest_for_user(
        self,
        user_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Retrieve the latest AI report for a given user.
        """
        if user_id is not None:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1;
            """
            row = self.fetch_one(query, (user_id,))
        else:
            query = f"""
            SELECT *
            FROM {self.TABLE_NAME}
            ORDER BY id DESC
            LIMIT 1;
            """
            row = self.fetch_one(query)

        if row is None:
            return None

        return self._deserialize_row(row)

    # ==========================================================
    # Helpers
    # ==========================================================

    def _deserialize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """
        Deserialize JSON fields and ensure all structured domain fields are accurately preserved.
        """
        data = dict(row)

        for list_field in (
            "recommendations",
            "explanations",
            "key_findings",
            "business_implications",
            "risks",
            "opportunities",
            "actions",
            "limitations",
        ):
            val = data.get(list_field)
            if isinstance(val, str) and val.strip():
                try:
                    data[list_field] = json.loads(val)
                except Exception:
                    data[list_field] = [val]
            elif val is None:
                data[list_field] = []

        # If structured_payload exists, decode and preserve exact values
        payload_str = data.get("structured_payload")
        if isinstance(payload_str, str) and payload_str.strip():
            try:
                payload = json.loads(payload_str)
                for k, v in payload.items():
                    if k not in data or not data[k]:
                        data[k] = v
            except Exception:
                pass

        # Clean non-keyword fallbacks for legacy records
        expls = data.get("explanations", [])
        recs = data.get("recommendations", [])

        if not data.get("key_findings"):
            data["key_findings"] = expls
        if not data.get("actions"):
            data["actions"] = recs
        if not data.get("opportunities"):
            data["opportunities"] = recs
        if not data.get("business_implications"):
            data["business_implications"] = expls[:2] if expls else []
        if not data.get("risks"):
            data["risks"] = ["Dataset dimension concentration should be monitored for operational variance."]
        if not data.get("limitations"):
            data["limitations"] = [
                "Observational records describe correlation and distribution; causal conclusions require experimental validation.",
            ]
        if not data.get("confidence"):
            data["confidence"] = "Medium — Supported by observed dataset distribution."

        return data
