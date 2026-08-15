"""
Frontend services package for AnalystGPT Enterprise.
"""

from .api_client import APIClient
from .auth_service import AuthService
from .dashboard_service import get_dashboard_data
from .report_service import get_report_data
from .session_manager import (
    clear_authenticated_session,
    clear_dataset,
    get_auth_token,
    get_current_user,
    get_dataframe,
    get_dataset,
    get_dataset_path,
    get_pipeline_result,
    get_uploaded_file,
    get_user_role,
    has_dataset,
    has_pipeline_result,
    is_admin,
    is_authenticated,
    set_authenticated_session,
    store_dataset,
    store_pipeline_result,
)

__all__ = [
    "APIClient",
    "AuthService",
    "get_dashboard_data",
    "get_report_data",
    "is_authenticated",
    "get_auth_token",
    "get_current_user",
    "get_user_role",
    "is_admin",
    "set_authenticated_session",
    "clear_authenticated_session",
    "store_dataset",
    "store_pipeline_result",
    "get_dataframe",
    "get_uploaded_file",
    "get_dataset_path",
    "get_dataset",
    "get_pipeline_result",
    "has_dataset",
    "has_pipeline_result",
    "clear_dataset",
]
