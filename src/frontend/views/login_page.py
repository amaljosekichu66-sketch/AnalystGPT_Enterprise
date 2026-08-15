"""
Login view for AnalystGPT Enterprise Streamlit frontend.

Responsibilities
----------------
- Render login form for user authentication.
- Validate input before submission.
- Invoke AuthService to communicate with POST /api/auth/login.
- Establish authenticated session state and trigger transition.
"""

from __future__ import annotations

import streamlit as st

from src.frontend.services.auth_service import AuthService


def render() -> None:
    """
    Render the Enterprise Login and Registration page.
    """
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("🔐 Authentication")
        st.caption("AnalystGPT Enterprise Analytics Platform")

        st.divider()

        tab_signin, tab_signup = st.tabs(["Sign In", "Sign Up"])

        with tab_signin:
            with st.form("login_form", clear_on_submit=False):
                username_or_email = st.text_input(
                    "Username or Email",
                    placeholder="Enter username or email address",
                    key="login_username",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter password",
                    key="login_password",
                )

                submit_login = st.form_submit_button("Sign In", use_container_width=True)

            if submit_login:
                if not username_or_email.strip():
                    st.error("Please enter your username or email address.")
                elif not password:
                    st.error("Please enter your password.")
                else:
                    auth_service = AuthService()
                    with st.spinner("Authenticating credentials..."):
                        success, error_msg = auth_service.login(
                            username_or_email=username_or_email,
                            password=password,
                        )

                    if success:
                        st.success("Authentication successful. Loading platform...")
                        st.session_state.current_page = "Dashboard"
                        st.rerun()
                    else:
                        st.error(error_msg or "Authentication failed.")

        with tab_signup:
            with st.form("register_form", clear_on_submit=False):
                reg_username = st.text_input("Username", key="reg_user")
                reg_email = st.text_input("Email Address", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_pass")

                submit_register = st.form_submit_button("Create Account", use_container_width=True)

            if submit_register:
                if not reg_username.strip() or not reg_email.strip() or not reg_password:
                    st.error("Please fill in all fields.")
                elif "@" not in reg_email:
                    st.error("Please enter a valid email address.")
                else:
                    auth_service = AuthService()
                    with st.spinner("Creating account..."):
                        success, error_msg = auth_service.register(
                            username=reg_username,
                            email=reg_email,
                            password=reg_password,
                        )

                    if success:
                        st.success("Account created successfully! You can now sign in.")
                    else:
                        st.error(error_msg or "Registration failed.")
