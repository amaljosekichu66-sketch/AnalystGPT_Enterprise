"""
Cleaning policy proposals and their approval (P2-04, Sprint 15 Phase 2).

The Upload page let a user pick a cleaning policy, but nothing read the
choice: the pipeline always ran the default (DROP_ROWS), and there was no way
to approve, modify or reject a policy.

Workflow
--------
1. The dataset's owner PROPOSES a policy for one dataset version.
2. While PROPOSED, the proposer or a reviewer may MODIFY it (it stays
   PROPOSED; the change is recorded).
3. A reviewer APPROVES or REJECTS it. Reviewers are administrators, and the
   proposer themself unless `GOVERNANCE_REQUIRE_SEPARATE_APPROVER` is set
   (then only an administrator approves: datasets are private to their
   owner, so another analyst cannot see the proposal).
4. `POST /api/pipeline` with `cleaning_policy_proposal_id` runs an APPROVED
   proposal for that dataset only. The applied configuration records the
   proposal id and the approver, so the choice is in the run's lineage.

Running without a proposal applies the default policy, which needs no
approval, exactly as before.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.core import config as core_config
from src.core.exceptions import AnalystGPTError
from src.database.connection_factory import ConnectionFactory
from src.database.schema_manager import SchemaManager
from src.governance.models import CleaningConfig, MissingValuePolicy
from src.identity.audit import get_audit_service
from src.identity.context import UserContext
from src.identity.models import AuditEventType
from src.identity.permissions import Permission


class ProposalStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PolicyProposalNotFoundError(AnalystGPTError):
    """Unknown proposal, or one the caller may not see."""


class PolicyProposalStateError(AnalystGPTError):
    """The proposal is not in a state that allows this action."""


class PolicyReviewForbiddenError(AnalystGPTError):
    """The caller may not review this proposal."""


_COLUMNS = (
    "proposal_id, dataset_version_id, user_id, missing_value_policy, null_threshold, fill_value, status, "
    "created_at, updated_at, modified_by, reviewed_by, review_note, reviewed_at"
)


class PolicyApprovalService:
    def __init__(self) -> None:
        self._schema_ready = False

    # ------------------------------------------------------------------ storage

    def _connect(self):
        conn = ConnectionFactory.create_connection()
        conn.connect()
        if not self._schema_ready:
            SchemaManager(conn).initialize_schema()
            self._schema_ready = True
        return conn

    @staticmethod
    def _sql(conn, query: str) -> str:
        return query.replace("?", "%s") if conn.database_type() == "postgresql" else query

    def _fetch(self, query: str, params: tuple) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            cursor = conn.get_connection().cursor()
            cursor.execute(self._sql(conn, query), params)
            rows = cursor.fetchall()
            names = [d[0] for d in cursor.description] if cursor.description else []
            cursor.close()
            return [dict(row) if hasattr(row, "keys") else dict(zip(names, row)) for row in rows]
        finally:
            conn.disconnect()

    def _write(self, query: str, params: tuple) -> int:
        conn = self._connect()
        try:
            cursor = conn.get_connection().cursor()
            cursor.execute(self._sql(conn, query), params)
            count = cursor.rowcount
            conn.commit()
            cursor.close()
            return count
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.disconnect()

    def _get(self, proposal_id: str) -> dict[str, Any] | None:
        rows = self._fetch(f"SELECT {_COLUMNS} FROM cleaning_policy_proposals WHERE proposal_id = ?;", (proposal_id,))
        return rows[0] if rows else None

    # ------------------------------------------------------------------ access

    @staticmethod
    def _is_admin(context: UserContext) -> bool:
        return context.has_permission(Permission.USER_MANAGE)

    def _visible(self, proposal_id: str, context: UserContext) -> dict[str, Any]:
        row = self._get(proposal_id)
        if row is None or not (self._is_admin(context) or row["user_id"] == context.user_id):
            raise PolicyProposalNotFoundError("Cleaning policy proposal not found.")
        return row

    def _require_reviewer(self, row: dict[str, Any], context: UserContext) -> None:
        if self._is_admin(context):
            return
        if core_config.GOVERNANCE_REQUIRE_SEPARATE_APPROVER:
            raise PolicyReviewForbiddenError("A different reviewer (an administrator) must approve this policy.")
        if row["user_id"] != context.user_id:
            raise PolicyReviewForbiddenError("You may not review this policy.")

    @staticmethod
    def _require_status(row: dict[str, Any], *allowed: ProposalStatus) -> None:
        if row["status"] not in {s.value for s in allowed}:
            raise PolicyProposalStateError(f"The proposal is {row['status']}.")

    # ------------------------------------------------------------------ actions

    def propose(
        self,
        dataset_version_id: str,
        policy: MissingValuePolicy,
        context: UserContext,
        null_threshold: float | None = None,
        fill_value: str | None = None,
    ) -> dict[str, Any]:
        """Record a proposal. The caller must already have resolved (owned) the dataset."""
        proposal_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        self._write(
            "INSERT INTO cleaning_policy_proposals (proposal_id, dataset_version_id, user_id, missing_value_policy, "
            "null_threshold, fill_value, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (
                proposal_id,
                dataset_version_id,
                context.user_id,
                policy.value,
                null_threshold,
                fill_value,
                ProposalStatus.PROPOSED.value,
                now,
                now,
            ),
        )
        self._audit(AuditEventType.POLICY_PROPOSED, "POLICY_PROPOSE", context, proposal_id, {"policy": policy.value})
        return self._get(proposal_id) or {}

    def list_for(self, context: UserContext, dataset_version_id: str | None = None) -> list[dict[str, Any]]:
        conditions, params = [], []
        if not self._is_admin(context):
            conditions.append("user_id = ?")
            params.append(context.user_id)
        if dataset_version_id:
            conditions.append("dataset_version_id = ?")
            params.append(dataset_version_id)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        return self._fetch(
            f"SELECT {_COLUMNS} FROM cleaning_policy_proposals {where} ORDER BY created_at DESC;", tuple(params)
        )

    def get(self, proposal_id: str, context: UserContext) -> dict[str, Any]:
        return self._visible(proposal_id, context)

    def modify(
        self,
        proposal_id: str,
        policy: MissingValuePolicy,
        context: UserContext,
        null_threshold: float | None = None,
        fill_value: str | None = None,
    ) -> dict[str, Any]:
        row = self._visible(proposal_id, context)
        self._require_status(row, ProposalStatus.PROPOSED)
        now = datetime.now(UTC).isoformat()
        self._write(
            "UPDATE cleaning_policy_proposals SET missing_value_policy = ?, null_threshold = ?, fill_value = ?, "
            "modified_by = ?, updated_at = ? WHERE proposal_id = ? AND status = ?;",
            (
                policy.value,
                null_threshold,
                fill_value,
                context.user_id,
                now,
                proposal_id,
                ProposalStatus.PROPOSED.value,
            ),
        )
        self._audit(AuditEventType.POLICY_PROPOSED, "POLICY_MODIFY", context, proposal_id, {"policy": policy.value})
        return self._get(proposal_id) or {}

    def approve(self, proposal_id: str, context: UserContext, note: str | None = None) -> dict[str, Any]:
        return self._review(proposal_id, context, ProposalStatus.APPROVED, note)

    def reject(self, proposal_id: str, context: UserContext, note: str | None = None) -> dict[str, Any]:
        return self._review(proposal_id, context, ProposalStatus.REJECTED, note)

    def _review(
        self, proposal_id: str, context: UserContext, outcome: ProposalStatus, note: str | None
    ) -> dict[str, Any]:
        row = self._visible(proposal_id, context)
        self._require_reviewer(row, context)
        self._require_status(row, ProposalStatus.PROPOSED)
        now = datetime.now(UTC).isoformat()
        changed = self._write(
            "UPDATE cleaning_policy_proposals SET status = ?, reviewed_by = ?, review_note = ?, reviewed_at = ?, "
            "updated_at = ? WHERE proposal_id = ? AND status = ?;",
            (outcome.value, context.user_id, note, now, now, proposal_id, ProposalStatus.PROPOSED.value),
        )
        if not changed:
            raise PolicyProposalStateError("The proposal was reviewed concurrently.")
        event = AuditEventType.POLICY_APPROVED if outcome == ProposalStatus.APPROVED else AuditEventType.POLICY_REJECTED
        self._audit(event, f"POLICY_{outcome.value}", context, proposal_id, {"policy": row["missing_value_policy"]})
        return self._get(proposal_id) or {}

    def approved_config(self, proposal_id: str, dataset_version_id: str, context: UserContext) -> CleaningConfig:
        """
        The CleaningConfig of an APPROVED proposal for this dataset, for the pipeline.

        Raises `PolicyProposalNotFoundError` for an unknown, foreign or
        other-dataset proposal and `PolicyProposalStateError` if not approved.
        """
        row = self._visible(proposal_id, context)
        if row["dataset_version_id"] != dataset_version_id:
            raise PolicyProposalNotFoundError("Cleaning policy proposal not found for this dataset.")
        self._require_status(row, ProposalStatus.APPROVED)
        return CleaningConfig(
            config_id=str(uuid.uuid4()),
            missing_value_policy=MissingValuePolicy(row["missing_value_policy"]),
            null_threshold=row.get("null_threshold"),
            fill_value=row.get("fill_value"),
            user_id=row["user_id"],
            proposal_id=row["proposal_id"],
            approved_by=row.get("reviewed_by"),
        )

    @staticmethod
    def _audit(
        event_type: AuditEventType, action: str, context: UserContext, proposal_id: str, details: dict[str, Any]
    ) -> None:
        get_audit_service().record_event(
            event_type=event_type,
            action=action,
            actor_id=context.user_id,
            actor_username=context.username,
            target_resource="CLEANING_POLICY",
            outcome="SUCCESS",
            details={"proposal_id": proposal_id, **details},
        )
