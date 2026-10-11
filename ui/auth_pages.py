from __future__ import annotations

import streamlit as st

from backend import users
from ui.components.network import build_network_svg
from ui.theme import base_css


def _hero() -> None:
    st.markdown(
        """
        <div class="hero-kicker">AI WATER OPERATIONS</div>
        <h1 class="hero-title">Autonomous intelligence<br>for <span>water.</span></h1>
        <div class="hero-sub">Eight coordinated agents. One human in command.</div>
        <div class="login-label">LIVE AGENT NETWORK</div>
        """,
        unsafe_allow_html=True,
    )
    st.html(build_network_svg())
    st.markdown(
        """
        <div class="stats">
          <div class="stat"><div class="sv">08</div><div class="sl">OPERATIONAL AI AGENTS</div></div>
          <div class="stat"><div class="sv">24/7</div><div class="sl">MONITORING MODEL</div></div>
          <div class="stat"><div class="sv">HUMAN</div><div class="sl">FINAL CONTROL</div></div>
        </div>
        <div class="ticker"><i></i>AGENT SWARM ACTIVE · REPLANNING LOOP READY</div>
        """,
        unsafe_allow_html=True,
    )


def _title(title: str, copy: str) -> None:
    st.markdown(
        f'<div class="login-title">{title}</div><div class="login-copy">{copy}</div>',
        unsafe_allow_html=True,
    )


from agents.registry import get_configured_agent_count


def validate_password_strength(password: str) -> tuple[bool, str]:
    if not password:
        return False, "Please enter a password."
    if len(password) < 10:
        return False, "Password must be at least 10 characters long."
    import re
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return False, "Password must contain both letters and numbers."
    return True, ""


def _first_run() -> None:
    _title("Set up AquaSwarm", "Create the initial administrator account. You can configure facilities and invite operators afterwards.")
    st.info("🔐 **Security Requirements**: Password must be at least 10 characters and contain both letters and numbers.")
    with st.form("first_run"):
        name = st.text_input("Full name", placeholder="e.g. Operations Director")
        email = st.text_input("Work e-mail", placeholder="admin@organization.com")
        password = st.text_input("Password", type="password", placeholder="Minimum 10 characters (letters & numbers)")
        confirm = st.text_input("Confirm password", type="password", placeholder="Repeat your password")
        go = st.form_submit_button("Create administrator", type="primary", use_container_width=True)
    if go:
        clean_name = (name or "").strip()
        clean_email = (email or "").strip()
        if not clean_name:
            st.error("Please enter your full name.")
            return
        if not clean_email:
            st.error("Please enter your work e-mail address.")
            return
        valid, msg = validate_password_strength(password)
        if not valid:
            st.error(msg)
            return
        if password != confirm:
            st.error("The passwords do not match. Please re-enter the confirmation password.")
            return
        try:
            user = users.create_first_admin(clean_email, clean_name, password)
            st.session_state.user = user
            st.success("Administrator account created successfully.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def _sign_in() -> None:
    _title("Sign in", "Access the AquaSwarm operations control center.")
    with st.form("sign_in"):
        email = st.text_input("E-mail", placeholder="you@organization.com")
        password = st.text_input("Password", type="password")
        go = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    if go:
        clean_email = (email or "").strip().lower()
        if not clean_email or not password:
            st.error("Enter your e-mail and password.")
            return
        try:
            st.session_state.user = users.authenticate(clean_email, password)
        except users.AuthError as exc:
            msg = str(exc)
            if "Too many failed attempts" in msg or "locked" in msg.lower():
                st.error(f"🔒 {msg}")
                st.info("💡 **Account Locked**: You can reset your password using the **Reset password** tab above, or run `.\\.venv\\Scripts\\python.exe -m backend.users unlock <email>` in PowerShell.")
            else:
                st.error(msg)
            return
        st.rerun()


def _request_access() -> None:
    _title("Request access", "An administrator reviews every request and assigns your role.")
    with st.form("request_access"):
        name = st.text_input("Full name")
        email = st.text_input("Work e-mail", key="req_email")
        role = st.selectbox("Role you need", ["operator", "manager"],
                            format_func=lambda r: {"operator": "Operator — record readings, confirm deliveries",
                                                   "manager": "Manager — approve deliveries, manage data"}[r])
        password = st.text_input("Choose a password", type="password", key="req_pw")
        confirm = st.text_input("Confirm password", type="password", key="req_pw2")
        note = st.text_input("Note for the administrator (optional)")
        st.caption("Password must be at least 10 characters and contain letters and numbers.")
        go = st.form_submit_button("Send request", type="primary", use_container_width=True)
    if go:
        clean_name = (name or "").strip()
        clean_email = (email or "").strip()
        if not clean_name:
            st.error("Please enter your full name.")
            return
        if not clean_email:
            st.error("Please enter your work e-mail address.")
            return
        if not password:
            st.error("Please choose a password.")
            return
        if len(password) < 10:
            st.error("Password must be at least 10 characters.")
            return
        import re
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            st.error("Password must contain both letters and numbers.")
            return
        if password != confirm:
            st.error("The passwords do not match.")
            return
        try:
            users.request_access(clean_email, clean_name, password, role, note)
            st.success("Access request submitted. An administrator will review and activate your account.")
        except ValueError as exc:
            st.error(str(exc))


def _reset_password() -> None:
    _title("Reset password", "Request a one-time code, then choose a new password.")
    with st.form("reset_request"):
        email = st.text_input("Account e-mail", key="rst_email")
        go = st.form_submit_button("Request a code", use_container_width=True)
    if go:
        clean_email = (email or "").strip().lower()
        if not clean_email:
            st.error("Please enter your account e-mail address.")
            return
        code = None
        try:
            code = users.request_password_reset(clean_email)
        except Exception:
            pass  # never reveal whether the account exists
        if code:
            st.warning(
                f"⚠️ **E-mail (SMTP) is not configured on this server.**\n\n"
                f"For local administration, your one-time reset code is: **`{code}`** (valid for 30 minutes).\n\n"
                f"Enter it below in **Already have a code?** to set your new password immediately."
            )
            st.session_state["default_rst_email"] = clean_email
            st.session_state["default_rst_code"] = code
        else:
            st.info("If that account exists, a code has been sent or queued. "
                    "If you do not receive an e-mail, ask your administrator to issue one.")

    default_email = st.session_state.get("default_rst_email", "")
    default_code = st.session_state.get("default_rst_code", "")
    st.markdown('<div class="auth-note">Already have a code?</div>', unsafe_allow_html=True)
    with st.form("reset_complete"):
        email2 = st.text_input("Account e-mail", value=default_email, key="rst_email2")
        code_input = st.text_input("One-time code", value=default_code)
        new_pw = st.text_input("New password", type="password", key="rst_pw", placeholder="Minimum 10 characters (letters & numbers)")
        confirm = st.text_input("Confirm new password", type="password", key="rst_pw2")
        done = st.form_submit_button("Set new password", type="primary", use_container_width=True)
    if done:
        clean_email2 = (email2 or "").strip().lower()
        clean_code = (code_input or "").strip().upper()
        if not clean_email2 or not clean_code:
            st.error("Please provide both your account e-mail and the one-time code.")
            return
        valid, msg = validate_password_strength(new_pw)
        if not valid:
            st.error(msg)
            return
        if new_pw != confirm:
            st.error("The passwords do not match. Please re-enter the confirmation password.")
            return
        try:
            users.complete_password_reset(clean_email2, clean_code, new_pw)
            st.session_state.pop("default_rst_code", None)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.success("✅ Password updated successfully! You can now sign in using the 'Sign in' tab.")


def render_auth_gate() -> None:
    st.markdown(base_css(), unsafe_allow_html=True)
    st.markdown(
        """
        <div class="topbar">
          <div class="brand"><span class="drop"></span>AQUASWARM AI</div>
          <div class="status"><span class="pulse"></span>SYSTEM ONLINE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.3, 0.7], gap="large")
    with left:
        _hero()
    with right:
        with st.container(key="login_card"):
            try:
                first_run = not users.has_users()
            except Exception as exc:
                st.error(f"Accounts are unavailable right now: {exc}")
                return
            if first_run:
                _first_run()
                return
            sign_in, request, reset = st.tabs(["Sign in", "Request access", "Reset password"])
            with sign_in:
                _sign_in()
            with request:
                _request_access()
            with reset:
                _reset_password()
            st.markdown('<p class="secure">🔒 Authorized personnel only</p>', unsafe_allow_html=True)