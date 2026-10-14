# ADR-034 — Cleaning Policy Proposal and Approval

**Status:** ✅ **Accepted** — implemented on `pre-sprint-15-hardening`, released in v14.1.0

**Date:** 2026-10-14 (decision taken 2026-10-03)

**Sprint:** Pre-Sprint-15 hardening (pulled forward from Sprint 15 Phase 2)

**Decision Makers:** Lead Software Architect, Data Governance Lead

---

# Context

ADR-026 made cleaning governed: an immutable source version, a recorded configuration and
lineage. Choosing the policy was never connected, though (P2-04):

- the Upload page stored the user's choice in Streamlit session state, and nothing read it;
- `PipelineRequest` accepted only `dataset_version_id`;
- the pipeline always ran the default `DROP_ROWS`;
- no API could approve, modify or reject a policy.

# Decision

A cleaning policy is a **proposal** that must be **approved** before a pipeline will run it.

| Route | Who | Effect |
|---|---|---|
| `POST /api/governance/policies` | owner of the dataset version | creates a `PROPOSED` proposal (policy and parameters) |
| `GET /api/governance/policies[?dataset_version_id=]` | owner, or ADMIN for all | lists proposals |
| `PATCH /api/governance/policies/{id}` | proposer, while `PROPOSED` | modifies it |
| `POST /api/governance/policies/{id}/approve` | reviewer | `PROPOSED` → `APPROVED`; records reviewer, time and note |
| `POST /api/governance/policies/{id}/reject` | reviewer | `PROPOSED` → `REJECTED` |

**Reviewers.** A reviewer is an ADMIN, or the proposer when `GOVERNANCE_REQUIRE_SEPARATE_APPROVER`
is off (the default for single-analyst deployments). Turn it on to require four-eyes approval.

**Errors.**

| Status | When |
|---|---|
| 404 | unknown id, or another user's proposal |
| 409 | wrong state |
| 403 | the caller may not review |

**Running a proposal.** `POST /api/pipeline` accepts `cleaning_policy_proposal_id`. Only an
`APPROVED` proposal for that same dataset version is accepted, and nothing runs otherwise. A
proposal that is not yet approved, or was rejected, gets a 409. A proposal for a different
dataset, or one the caller cannot see, gets a 404. The resulting `cleaning_configs` row records `proposal_id` and `approved_by`, and
the lineage endpoint returns both.

**Without a proposal,** the pipeline still runs the documented default (`DROP_ROWS`), recorded
in lineage with `proposal_id = null`, so existing clients keep working.

# Consequences

- **Positive:** The policy a user picks is the policy that runs, and lineage proves who approved
  it. The same API serves the Streamlit UI and a future React UI.
- **Negative:** An extra step before a non-default run. The Upload page lists the dataset's
  proposals with Approve and Reject buttons for anyone allowed to review, and only offers
  approved proposals as run options.

# Verification

- `tests/api/test_policy_approval.py`: applied and recorded in lineage; refused until approved;
  modify then reject; reviewer rules; isolation.
- `tests/frontend/test_apptest_smoke.py`: the policy is chosen in the real UI against a live API
  and lands in lineage.
- `tests/integration/test_pipeline.py`: the full user journey.

# Related ADRs

- ADR-026 — Data Cleaning Governance and Lineage
- ADR-029 — Managed Dataset Upload API
