"""
Session management for AnalystGPT Enterprise.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.application.pipeline_result import PipelineResult

from typing import Any

# ==========================================================
# Session Keys
# ==========================================================

DATAFRAME_KEY = "dataframe"

UPLOADED_FILE_KEY = "uploaded_file"

DATASET_PATH_KEY = "dataset_path"

PIPELINE_RESULT_KEY = "pipeline_result"

AUTH_TOKEN_KEY = "auth_token"

AUTH_USER_KEY = "auth_user"

AUTH_STATUS_KEY = "auth_status"


# ==========================================================
# Authentication Session State
# ==========================================================

def is_authenticated() -> bool:
    """
    Return True if the current user session is authenticated.
    """
    token = st.session_state.get(AUTH_TOKEN_KEY)
    status = st.session_state.get(AUTH_STATUS_KEY)
    return bool(token and status == "AUTHENTICATED")


def get_auth_token() -> str | None:
    """
    Return the active access token or None.
    """
    return st.session_state.get(AUTH_TOKEN_KEY)


def get_current_user() -> dict[str, Any] | None:
    """
    Return current user identity dictionary.
    """
    return st.session_state.get(AUTH_USER_KEY)


def get_user_role() -> str | None:
    """
    Return the role string of the authenticated user.
    """
    user = get_current_user()
    if not user:
        return None
    role = user.get("role")
    if hasattr(role, "value"):
        return str(role.value)
    return str(role) if role is not None else None


def is_admin() -> bool:
    """
    Return True if the active user possesses the ADMIN role.
    """
    role = get_user_role()
    return role == "ADMIN"


def set_authenticated_session(token: str, user_data: dict[str, Any]) -> None:
    """
    Initialize authenticated session state.
    """
    st.session_state[AUTH_TOKEN_KEY] = token
    st.session_state[AUTH_USER_KEY] = user_data
    st.session_state[AUTH_STATUS_KEY] = "AUTHENTICATED"


def clear_authenticated_session() -> None:
    """
    Purge all authentication credentials, tenant datasets, caches, and results.
    Guarantees cross-tenant data isolation.
    """
    # 1. Clear auth credentials
    for key in (AUTH_TOKEN_KEY, AUTH_USER_KEY, AUTH_STATUS_KEY):
        st.session_state.pop(key, None)

    # 2. Clear dataset and pipeline artifacts
    clear_dataset()

    # 3. Clear frontend caches
    for cache_key in ("dashboard_cache", "dashboard_dataset", "reports_cache"):
        st.session_state.pop(cache_key, None)

    # 4. Reset navigation
    st.session_state["current_page"] = "Dashboard"


# ==========================================================
# Store
# ==========================================================

def store_dataset(
    uploaded_file,
    dataframe: pd.DataFrame,
    dataset_path: str | None = None,
) -> None:
    """
    Store the uploaded dataset in the Streamlit session.

    Parameters
    ----------
    uploaded_file
        Original Streamlit UploadedFile.

    dataframe
        Parsed dataframe.

    dataset_path
        Absolute path of the temporary dataset file created
        by the uploader.

    Notes
    -----
    The backend pipeline requires a real filesystem path.
    Therefore only the uploader should create and supply this
    value. This method never attempts to reconstruct it from
    the uploaded filename.
    """

    st.session_state[
        UPLOADED_FILE_KEY
    ] = uploaded_file

    st.session_state[
        DATAFRAME_KEY
    ] = dataframe

    st.session_state[
        DATASET_PATH_KEY
    ] = dataset_path


def store_pipeline_result(
    pipeline_result: PipelineResult,
) -> None:
    """
    Store the latest backend pipeline result.
    """

    st.session_state[
        PIPELINE_RESULT_KEY
    ] = pipeline_result


# ==========================================================
# Getters
# ==========================================================

def get_dataframe() -> pd.DataFrame | None:
    """
    Return the stored dataframe.
    """

    return st.session_state.get(
        DATAFRAME_KEY,
    )


def get_uploaded_file():
    """
    Return the uploaded file.
    """

    return st.session_state.get(
        UPLOADED_FILE_KEY,
    )


def get_dataset_path() -> str | None:
    """
    Return the temporary dataset path.

    Returns
    -------
    str | None
        Filesystem path used by the backend pipeline.
    """

    return st.session_state.get(
        DATASET_PATH_KEY,
    )


def get_dataset():
    """
    Return the uploaded file and dataframe.

    IMPORTANT
    ---------
    This function intentionally returns ONLY TWO values
    for backward compatibility with Sprint 10.

    Dataset path is available separately through
    get_dataset_path().
    """

    return (
        get_uploaded_file(),
        get_dataframe(),
    )


def get_pipeline_result() -> PipelineResult | None:
    """
    Return the cached backend pipeline result.
    """

    if not has_pipeline_result():
        return None

    return st.session_state[
        PIPELINE_RESULT_KEY
    ]


# ==========================================================
# Status
# ==========================================================

def has_dataset() -> bool:
    """
    Return True if a dataset exists.
    """

    return (
        DATAFRAME_KEY
        in st.session_state
    )


def has_pipeline_result() -> bool:
    """
    Return True if a completed pipeline result
    exists.
    """

    return (
        PIPELINE_RESULT_KEY
        in st.session_state
    )


# ==========================================================
# Clear
# ==========================================================

def clear_dataset() -> None:
    """
    Remove all dataset-related session state.
    """

    for key in (
        DATAFRAME_KEY,
        UPLOADED_FILE_KEY,
        DATASET_PATH_KEY,
        PIPELINE_RESULT_KEY,
    ):
        st.session_state.pop(
            key,
            None,
        )