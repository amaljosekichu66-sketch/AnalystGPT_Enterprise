# ADR-029 — Managed Dataset Upload API

**Status:** ✅ **Accepted** — implemented on `pre-sprint-15-hardening`, released in v14.1.0

**Date:** 2026-10-14 (decision taken 2026-09-28, during the pre-Sprint-15 hardening)

**Sprint:** Pre-Sprint-15 hardening (between v14.0.0 and Sprint 15)

**Decision Makers:** Lead Software Architect, Security Reviewer

---

# Context

Up to v14.0.0 the Streamlit frontend saved an uploaded file to a temporary path on its own
machine and sent that **path** to the API (`POST /api/pipeline {"input_path": ...}`,
`GET /api/dashboard?dataset=...`, `GET /api/powerbi/*?dataset=...`). The API opened whatever
path it was given.

The pre-Sprint-15 security audit (SEC-02, SEC-19, SEC-27) showed three consequences:

- **Arbitrary file read.** Any analyst could name any file on the API host. It was copied
  into their artifact store and its rows came back from `/api/governance/preview`.
- **Credential leak on Windows hosts.** A UNC path (`\\host\share\x.csv`) made the server
  connect out.
- **Broken topology.** Under Docker Compose the frontend and API have separate filesystems,
  so the normal upload flow could not work at all.

# Decision

The API owns dataset storage. Clients send **bytes**, never paths.

| Route | Purpose |
|---|---|
| `POST /api/datasets` (multipart) | Validates the upload (size before reading, `Content-Length` required, archive check by content, row/column caps) and stores an immutable source `DatasetVersion`. Returns `dataset_version_id`. |
| `GET /api/datasets/{id}/analysis` | Profile, visualisation plan and policy recommendation. Read-only; personal-data columns flagged and never charted. |
| `DELETE /api/datasets/{id}` | The owner removes a dataset and its files. |
| `POST /api/pipeline {"dataset_version_id": ...}` | Runs the pipeline on a stored version the caller owns. |

Every other route that used to take `dataset=` or `input_path` takes `dataset_version_id`, or
was removed. Request models use `extra="forbid"`, so a client that still sends `input_path`
gets a 422 rather than having the field silently ignored.

The local filesystem entry point remains for trusted callers only: `Application.run(path)`,
used by the CLI (`main.py`, see the README) and in-process tests. No HTTP route reaches it.

# Consequences

- **Positive:** No route can make the server read a path, and the class of bug is closed by
  construction rather than by path filtering. The frontend and API can run on different hosts.
  Upload limits are enforced where the bytes arrive.
- **Negative:** Breaking API change: clients of v14.0.0 that sent paths must upload first.
  This is recorded in the v14.1.0 upgrade notes in `CHANGELOG.md`.
- **Follow-up:** A future object store (S3 or similar) can sit behind `LocalArtifactStore`
  without changing the API.

# Verification

`tests/api/test_dataset_path_security.py` checks that absolute, `../` and UNC paths in every
former path parameter are rejected with no artifact created and no server path in any
response. `tests/api/test_upload_limits*.py` covers the upload limits.

# Related ADRs

- ADR-026 — Data Cleaning Governance and Lineage (source `DatasetVersion`s)
- ADR-028 — Frontend API Contract (the frontend uses only HTTP)
- ADR-034 — Cleaning Policy Proposal and Approval
