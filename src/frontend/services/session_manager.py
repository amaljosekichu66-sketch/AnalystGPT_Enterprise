"""
Session manager for AnalystGPT Enterprise.

Centralises Streamlit session-state access and provides
safe getters and setters.

Sprint 10 — Enterprise Frontend
Sprint 13 — Enterprise Identity, Authentication & Multi-User Platform
Sprint 14 — Remediation: AI Insights & Reporting Reliability
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

# ==========================================================
# Keys
# ==========================================================

DATAFRAME_KEY = "dataframe"
UPLOADED_FILE_KEY = "uploaded_file"
DATASET_VERSION_ID_KEY = "dataset_version_id"
PIPELINE_RESULT_KEY = "pipeline_result"
AI_JOB_ID_KEY = "ai_job_id"
AI_REPORT_KEY = "ai_report"
#: GET /api/datasets/{id}/analysis for the active dataset (P2-05).
ANALYSIS_KEY = "dataset_analysis"
#: sha256 of the uploaded file's bytes, so a rerun does not upload it again (P2-07).
UPLOAD_HASH_KEY = "uploaded_file_sha256"

# Sprint 13 Authentication session keys
AUTH_TOKEN_KEY = "auth_token"
AUTH_USER_KEY = "auth_user"
AUTH_STATUS_KEY = "auth_authenticated"


# ==========================================================
# Authentication Getters and Setters (Sprint 13)
# ==========================================================


def get_auth_token() -> str | None:
    return st.session_state.get(AUTH_TOKEN_KEY)


def get_current_user() -> dict[str, Any] | None:
    return st.session_state.get(AUTH_USER_KEY)


def set_auth_user(user: dict[str, Any] | None) -> None:
    if user is None:
        st.session_state.pop(AUTH_USER_KEY, None)
    else:
        st.session_state[AUTH_USER_KEY] = user


def is_authenticated() -> bool:
    status = st.session_state.get(AUTH_STATUS_KEY)
    return bool((status is True or status == "AUTHENTICATED") and get_auth_token())


def set_authenticated_session(token: str, user_data: dict[str, Any]) -> None:
    st.session_state[AUTH_TOKEN_KEY] = token
    st.session_state[AUTH_USER_KEY] = user_data
    st.session_state[AUTH_STATUS_KEY] = "AUTHENTICATED"


def get_user_role() -> str | None:
    user = get_current_user()
    if user and isinstance(user, dict):
        return user.get("role")
    return None


def is_admin() -> bool:
    role = get_user_role()
    return role == "ADMIN"


def clear_authenticated_session() -> None:
    clear_dataset()
    for key in (AUTH_TOKEN_KEY, AUTH_USER_KEY, AUTH_STATUS_KEY, AI_JOB_ID_KEY, AI_REPORT_KEY):
        st.session_state.pop(key, None)
    st.session_state["current_page"] = "Dashboard"


# ==========================================================
# Setters
# ==========================================================


def store_dataset(
    uploaded_file,
    dataframe: pd.DataFrame,
    dataset_version_id: str | None = None,
) -> None:
    for cache_key in (
        "dashboard_cache",
        "dashboard_dataset",
        "reports_cache",
        "reports_dataset",
        "exported_text_result",
        "exported_pdf_result",
        AI_REPORT_KEY,
        AI_JOB_ID_KEY,
        ANALYSIS_KEY,
        PIPELINE_RESULT_KEY,
    ):
        st.session_state.pop(cache_key, None)

    st.session_state[UPLOADED_FILE_KEY] = uploaded_file
    st.session_state[DATAFRAME_KEY] = dataframe
    st.session_state[DATASET_VERSION_ID_KEY] = dataset_version_id


def store_pipeline_result(
    pipeline_result: dict[str, Any],
) -> None:
    """
    Remember the POST /api/pipeline response for the active dataset.

    A plain dict from the API: the frontend no longer imports the backend's
    PipelineResult (P2-05). It carries pipeline_run_id, report_id, ai_job_id.
    """
    for cache_key in (
        "dashboard_cache",
        "dashboard_dataset",
        "reports_cache",
        "reports_dataset",
        "exported_text_result",
        "exported_pdf_result",
    ):
        st.session_state.pop(cache_key, None)

    st.session_state[PIPELINE_RESULT_KEY] = pipeline_result
    st.session_state.pop(AI_REPORT_KEY, None)
    if pipeline_result.get("ai_job_id"):
        st.session_state[AI_JOB_ID_KEY] = pipeline_result["ai_job_id"]
    if pipeline_result.get("ai_report"):
        st.session_state[AI_REPORT_KEY] = pipeline_result["ai_report"]


def set_ai_job_id(job_id: str | None) -> None:
    if job_id is None:
        st.session_state.pop(AI_JOB_ID_KEY, None)
    else:
        st.session_state[AI_JOB_ID_KEY] = job_id


def set_ai_report(report: dict[str, Any] | None) -> None:
    if report is None:
        st.session_state.pop(AI_REPORT_KEY, None)
    else:
        st.session_state[AI_REPORT_KEY] = report


# ==========================================================
# Getters
# ==========================================================


def get_dataframe() -> pd.DataFrame | None:
    return st.session_state.get(DATAFRAME_KEY)


def get_uploaded_file():
    return st.session_state.get(UPLOADED_FILE_KEY)


def get_dataset_version_id() -> str | None:
    return st.session_state.get(DATASET_VERSION_ID_KEY)


def get_dataset():
    return (
        get_uploaded_file(),
        get_dataframe(),
    )


def get_pipeline_result() -> dict[str, Any] | None:
    if not has_pipeline_result():
        return None
    return st.session_state[PIPELINE_RESULT_KEY]


def get_ai_job_id() -> str | None:
    if AI_JOB_ID_KEY in st.session_state and st.session_state[AI_JOB_ID_KEY]:
        return st.session_state[AI_JOB_ID_KEY]
    res = get_pipeline_result()
    return res.get("ai_job_id") if isinstance(res, dict) else None


def get_ai_report() -> dict[str, Any] | None:
    return st.session_state.get(AI_REPORT_KEY)


# ==========================================================
# Status
# ==========================================================


def has_dataset() -> bool:
    return DATAFRAME_KEY in st.session_state


def has_pipeline_result() -> bool:
    return PIPELINE_RESULT_KEY in st.session_state


# ==========================================================
# Clear
# ==========================================================


def clear_dataset() -> None:
    for key in (
        DATAFRAME_KEY,
        UPLOADED_FILE_KEY,
        DATASET_VERSION_ID_KEY,
        PIPELINE_RESULT_KEY,
        AI_JOB_ID_KEY,
        AI_REPORT_KEY,
        "dashboard_cache",
        "dashboard_dataset",
        "reports_cache",
        "reports_dataset",
        "exported_text_result",
        "exported_pdf_result",
        ANALYSIS_KEY,
        UPLOAD_HASH_KEY,
    ):
        st.session_state.pop(key, None)
