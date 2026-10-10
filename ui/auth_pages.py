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


def _first_run() -> None:
    _title("Set up AquaSwarm", "Create the administrator account. You can invite your team afterwards.")
    with st.form("first_run"):
        name = st.text_input("Full name")
        email = st.text_input("Work e-mail")
        password = st.text_input("Password", type="password", help=None)
        confirm = st.text_input("Confirm password", type="password")
        st.caption("At least 10 characters, with letters and numbers.")
        go = st.form_submit_button("Create administrator", type="primary", use_container_width=True)
    if go:
        if password != confirm:
            st.error("The passwords do not match.")
            return
        try:
            user = users.create_first_admin(email, name, password)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.session_state.user = user
        st.rerun()


def _sign_in() -> None:
    _title("Sign in", "Access the AquaSwarm operations control center.")
    with st.form("sign_in"):
        email = st.text_input("E-mail", placeholder="you@organization.com")
        password = st.text_input("Password", type="password")
        go = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    if go:
        if not email.strip() or not password:
            st.error("Enter your e-mail and password.")
            return
        try:
            st.session_state.user = users.authenticate(email, password)
        except users.AuthError as exc:
            st.error(str(exc))
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
        go = st.form_submit_button("Send request", type="primary", use_container_width=True)
    if go:
        if password != confirm:
            st.error("The passwords do not match.")
            return
        try:
            users.request_access(email, name, password, role, note)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.success("Request sent. You can sign in once an administrator approves it.")


def _reset_password() -> None:
    _title("Reset password", "Request a one-time code, then choose a new password.")
    with st.form("reset_request"):
        email = st.text_input("Account e-mail", key="rst_email")
        go = st.form_submit_button("Request a code", use_container_width=True)
    if go:
        try:
            users.request_password_reset(email)
        except Exception:
            pass  # never reveal whether the account exists
        st.info("If that account exists, a code has been sent or queued. "
                "If you do not receive an e-mail, ask your administrator to issue one.")

    st.markdown('<div class="auth-note">Already have a code?</div>', unsafe_allow_html=True)
    with st.form("reset_complete"):
        email2 = st.text_input("Account e-mail", key="rst_email2")
        code = st.text_input("One-time code")
        new_pw = st.text_input("New password", type="password", key="rst_pw")
        confirm = st.text_input("Confirm new password", type="password", key="rst_pw2")
        done = st.form_submit_button("Set new password", type="primary", use_container_width=True)
    if done:
        if new_pw != confirm:
            st.error("The passwords do not match.")
            return
        try:
            users.complete_password_reset(email2, code, new_pw)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.success("Password updated. You can sign in now.")


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