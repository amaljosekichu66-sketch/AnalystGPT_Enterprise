"""
Admin management view for AnalystGPT Enterprise Streamlit frontend.

Covers the admin API (P2-25): paginated user directory; role, status and
email changes; deletion (which purges the user's data); clearing a login
lockout; and the durable audit log. Success messages survive the rerun that
follows a change - they used to vanish because st.rerun() came right after
st.success().

The backend enforces every permission; the role check here only decides what
to show.
"""

from __future__ import annotations

import streamlit as st

from src.frontend.components.safe_text import markdown_text
from src.frontend.components.scroll_to_top import scroll_to_top
from src.frontend.services.admin_service import AdminService
from src.frontend.services.session_manager import get_current_user, is_admin, is_authenticated

PAGE_SIZE = 25
ROLES = ["ADMIN", "ANALYST", "VIEWER"]
STATUSES = ["ACTIVE", "INACTIVE", "SUSPENDED"]
_FLASH_KEY = "_admin_flash"


def _flash(message: str) -> None:
    st.session_state[_FLASH_KEY] = message
    st.rerun()


def _render_user(service: AdminService, user: dict) -> None:
    user_id = user.get("id")
    username = user.get("username", "")
    role, status = user.get("role"), user.get("status")
    me = (get_current_user() or {}).get("id")

    with st.expander(f"👤 {username} ({role}) — {status}", expanded=False):
        st.caption(f"User ID {user_id} · created {user.get('created_at', 'N/A')}")
        c1, c2, c3 = st.columns(3)
        new_role = c1.selectbox("Role", ROLES, index=ROLES.index(role) if role in ROLES else 1, key=f"role_{user_id}")
        new_status = c2.selectbox(
            "Status", STATUSES, index=STATUSES.index(status) if status in STATUSES else 0, key=f"status_{user_id}"
        )
        new_email = c3.text_input("Email", value=user.get("email", ""), key=f"email_{user_id}")

        save_col, unlock_col, delete_col = st.columns(3)
        with save_col:
            if st.button("Save changes", key=f"save_{user_id}", width="stretch"):
                changes = {
                    "role": new_role if new_role != role else None,
                    "status_val": new_status if new_status != status else None,
                    "email": new_email.strip() if new_email.strip() != user.get("email") else None,
                }
                if not any(changes.values()):
                    st.info("No changes to save.")
                else:
                    ok, _, err = service.update_user(user_id, **changes)
                    if ok:
                        _flash(f"User '{username}' updated.")
                    st.error(err)
        with unlock_col:
            if st.button("Clear login lockout", key=f"unlock_{user_id}", width="stretch"):
                ok, _, err = service.unlock_user(user_id)
                if ok:
                    _flash(f"Login lockout cleared for '{username}'.")
                st.error(err)
        with delete_col:
            if user_id == me:
                st.caption("You cannot delete your own account here.")
            else:
                confirm = st.checkbox("Confirm delete (removes all their data)", key=f"confirm_{user_id}")
                if st.button("Delete user", key=f"delete_{user_id}", disabled=not confirm, width="stretch"):
                    ok, _, err = service.delete_user(user_id)
                    if ok:
                        _flash(f"User '{username}' and their data were deleted.")
                    st.error(err)


def _render_directory(service: AdminService) -> None:
    page = int(st.session_state.get("_admin_page", 0))
    ok, data, err = service.list_users(limit=PAGE_SIZE, offset=page * PAGE_SIZE)
    if not ok or not data:
        st.error(err or "The user directory could not be loaded.")
        return

    total = int(data.get("total", 0))
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    st.subheader(f"Registered users ({total})")
    for user in data.get("items", []):
        _render_user(service, user)

    prev_col, info_col, next_col = st.columns([1, 2, 1])
    with prev_col:
        if st.button("◀ Previous", disabled=page <= 0, width="stretch"):
            st.session_state["_admin_page"] = page - 1
            st.rerun()
    info_col.caption(f"Page {page + 1} of {pages}")
    with next_col:
        if st.button("Next ▶", disabled=page + 1 >= pages, width="stretch"):
            st.session_state["_admin_page"] = page + 1
            st.rerun()


def _render_audit_log(service: AdminService) -> None:
    event_type = st.selectbox(
        "Event type",
        [
            "All",
            "LOGIN_FAILURE",
            "USER_ROLE_CHANGED",
            "USER_STATUS_CHANGED",
            "USER_DELETED",
            "ACCESS_DENIED",
            "ADMIN_CROSS_TENANT_ACCESS",
            "RATE_LIMITED",
            "POLICY_APPROVED",
            "POLICY_REJECTED",
        ],
        key="audit_event_type",
    )
    ok, events, err = service.audit_events(limit=200, event_type=None if event_type == "All" else event_type)
    if not ok:
        st.error(err)
        return
    if not events:
        st.info("No audit events match.")
        return
    st.dataframe(
        [
            {
                "When": e.get("occurred_at"),
                "Type": e.get("event_type"),
                "Action": e.get("action"),
                "Actor": e.get("actor_username"),
                "Target": f"{e.get('target_resource') or ''} {e.get('target_id') or ''}".strip(),
                "Outcome": e.get("outcome"),
            }
            for e in events
        ],
        hide_index=True,
        width="stretch",
    )


def render() -> None:
    """
    Render the administration page.
    """
    scroll_to_top()
    if not is_authenticated():
        st.error("Authentication required to access this resource.")
        return
    if not is_admin():
        st.error("⛔ Access Denied: You do not have permission to access the administration panel.")
        st.info("Required role: ADMIN. If you believe this is an error, please contact your system administrator.")
        return

    st.title("⚙️ Administration")
    st.caption("Manage user accounts, roles and access, and review the audit trail.")

    flash = st.session_state.pop(_FLASH_KEY, None)
    if flash:
        st.success(markdown_text(flash))

    service = AdminService()
    users_tab, audit_tab = st.tabs(["Users", "Audit log"])
    with users_tab:
        _render_directory(service)
    with audit_tab:
        _render_audit_log(service)
