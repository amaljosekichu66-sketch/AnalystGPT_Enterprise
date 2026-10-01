"""
Page registry for the Streamlit app.

Kept apart from `streamlit_app.py`, which renders on import: importing the
app to read its routes executed the whole UI in bare mode and left a
Streamlit form context behind for later code.
"""

from __future__ import annotations

from src.frontend.views import (
    about_page,
    admin_page,
    ai_insights_page,
    dashboard_page,
    login_page,
    report_page,
    upload_page,
)

DEFAULT_PAGE = "Dashboard"

PAGES = {
    "Dashboard": dashboard_page.render,
    "Upload": upload_page.render,
    "Reports": report_page.render,
    "AI Insights": ai_insights_page.render,
    "Admin": admin_page.render,
    "About": about_page.render,
    "Sign In": login_page.render,
}
