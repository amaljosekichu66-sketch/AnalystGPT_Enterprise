"""
Admin management view for AnalystGPT Enterprise Streamlit frontend.

Responsibilities
----------------
- Display user accounts with pagination.
- Enable user role and status administration via protected backend API.
- Enforce RBAC visibility in UX while backend enforces security.
"""

from __future__ import annotations

import streamlit as st

from src.frontend.components.scroll_to_top import scroll_to_top
from src.frontend.services.auth_service import AuthService
from src.frontend.services.session_manager import is_admin, is_authenticated


def render() -> None:
    """
    Render the Administrative User Management page.
    """
    scroll_to_top()
    if not is_authenticated():
        st.error("Authentication required to access this resource.")
        return

    if not is_admin():
        st.error("⛔ Access Denied: You do not have permission to access the administration panel.")
        st.info("Required role: ADMIN. If you believe this is an error, please contact your system administrator.")
        return

    st.title("⚙️ User Administration")
    st.caption("Manage enterprise user accounts, roles, and access lifecycle.")

    st.divider()

    auth_service = AuthService()
    success, data, error_msg = auth_service.admin_list_users()

    if not success or not data:
        st.error(f"Failed to load user directory: {error_msg}")
        return

    users = data.get("items", [])
    total_users = data.get("total", len(users))

    st.subheader(f"Registered Users ({total_users})")

    # Display user cards with edit controls
    for user in users:
        user_id = user.get("id")
        username = user.get("username")
        email = user.get("email")
        role = user.get("role")
        status = user.get("status")
        created_at = user.get("created_at", "N/A")

        with st.expander(f"👤 {username} ({role}) — Status: {status}", expanded=False):
            st.write(f"**User ID:** {user_id}")
            st.write(f"**Email:** {email}")
            st.write(f"**Created At:** {created_at}")

            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                new_role = st.selectbox(
                    "Role",
                    options=["ADMIN", "ANALYST", "VIEWER"],
                    index=["ADMIN", "ANALYST", "VIEWER"].index(role) if role in ["ADMIN", "ANALYST", "VIEWER"] else 1,
                    key=f"role_select_{user_id}",
                )

            with col2:
                new_status = st.selectbox(
                    "Status",
                    options=["ACTIVE", "INACTIVE", "SUSPENDED"],
                    index=(
                        ["ACTIVE", "INACTIVE", "SUSPENDED"].index(status)
                        if status in ["ACTIVE", "INACTIVE", "SUSPENDED"]
                        else 0
                    ),
                    key=f"status_select_{user_id}",
                )

            with col3:
                st.write("")
                st.write("")
                if st.button("Save Changes", key=f"save_btn_{user_id}", use_container_width=True):
                    if new_role != role or new_status != status:
                        with st.spinner("Updating user profile..."):
                            upd_ok, _, upd_err = auth_service.admin_update_user(
                                user_id=user_id,
                                role=new_role,
                                status=new_status,
                            )
                        if upd_ok:
                            st.success(f"User '{username}' updated successfully.")
                            st.rerun()
                        else:
                            st.error(f"Update failed: {upd_err}")
                    else:
                        st.info("No changes detected.")
