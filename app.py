from __future__ import annotations

import threading
import time

import streamlit as st

from ui.components import (
    authenticate,
    build_network_svg,
    get_backend_status,
    get_tank_options,
)
from ui.components.auth import using_default_credentials
from ui.dashboard import live_html, render_dashboard
from ui.theme import base_css, dashboard_css
from workflows.aquaswarm_flow import SCENARIOS, AquaSwarmFlow, AquaSwarmState

st.set_page_config(
    page_title="AquaSwarm AI",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAX_LOGIN_FAILURES = 5
LOCKOUT_SECONDS = 60
BLOCKING_STATUSES = {
    "Awaiting Manager Approval",
    "Delivery Dispatched",
    "Delivery In Progress",
}


# ---------------------------------------------------------------------------
# Manager actions
# ---------------------------------------------------------------------------

def resume_flow_from_state(workflow_state: AquaSwarmState) -> AquaSwarmFlow:
    """Restore an interrupted operation into a new flow instance."""
    restored_state = AquaSwarmState.model_validate(workflow_state.model_dump())
    return AquaSwarmFlow(initial_state=restored_state)


def handle_manager_decision(approved: bool, reason: str = "") -> bool:
    """Record the human decision and continue the approved/rejected branch."""
    workflow_state = st.session_state.get("workflow_state")
    if workflow_state is None:
        st.error("No active water operation found.")
        return False

    decided_by = st.session_state.get("current_user", "Manager")
    try:
        with st.spinner("Recording the decision and running the next agents…"):
            flow = resume_flow_from_state(workflow_state)
            flow.manager_decision(approved=approved, decided_by=decided_by, reason=reason.strip())
        st.session_state.workflow_state = flow.state
        return True
    except Exception as exc:
        st.error(f"Unable to process manager decision: {exc}")
        return False


def handle_delivery_completion(actual_quantity: float) -> bool:
    """Record the physical received quantity and trigger verification."""
    workflow_state = st.session_state.get("workflow_state")
    if workflow_state is None:
        st.error("No active water operation found.")
        return False

    try:
        with st.spinner("Verifying the delivery…"):
            flow = resume_flow_from_state(workflow_state)
            flow.complete_delivery(float(actual_quantity))
        st.session_state.workflow_state = flow.state
        return True
    except Exception as exc:
        st.error(f"Unable to complete delivery: {exc}")
        return False


# ---------------------------------------------------------------------------
# Running the pipeline with a live, animated view
# ---------------------------------------------------------------------------

def run_operation(tank_id: str, scenario: str) -> None:
    """Run the agent pipeline in a worker thread and animate its progress.

    The flow updates its own stage records; this loop only reads them, so no
    Streamlit calls happen off the main thread.
    """
    flow = AquaSwarmFlow()
    flow.state.selected_tank_id = tank_id
    flow.state.scenario = scenario

    outcome: dict = {}

    def target() -> None:
        try:
            flow.kickoff()
        except Exception as exc:  # reported below, never swallowed
            outcome["error"] = exc

    worker = threading.Thread(target=target, daemon=True)
    worker.start()

    st.html(dashboard_css())
    view = st.empty()

    previous_statuses: dict = {}
    previous_signature = None

    while worker.is_alive():
        try:
            statuses = {name: rec.status for name, rec in list(flow.state.stages.items())}
            signature = (
                tuple(sorted(statuses.items())),
                len(flow.state.activity),
                flow.state.operation_status,
            )
        except RuntimeError:  # a stage was added while reading; try again
            time.sleep(0.1)
            continue

        if signature != previous_signature:
            fresh = {
                name for name, status in statuses.items()
                if status == "done" and previous_statuses.get(name) != "done"
            }
            view.html(live_html(flow.state, fresh))
            previous_statuses, previous_signature = statuses, signature
        time.sleep(0.25)

    worker.join()

    error = outcome.get("error")
    state = flow.state
    message = ""
    if error is not None:
        message = state.error_message or f"{type(error).__name__}: {error}"
    elif state.operation_status == "Pipeline Error":
        message = state.error_message

    st.session_state.workflow_state = state
    st.session_state.run_error = message
    st.rerun()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def _locked_out() -> int:
    until = st.session_state.get("login_locked_until", 0.0)
    return max(0, int(until - time.time()))


def render_login() -> None:
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

    with right:
        with st.container(key="login_card"):
            st.markdown(
                """
                <div class="login-title">Secure Session</div>
                <div class="login-copy">Access the AquaSwarm operations control center.</div>
                <div class="login-field-label">EMAIL</div>
                """,
                unsafe_allow_html=True,
            )
            email = st.text_input(
                "Email", placeholder="you@organization.com",
                key="login_email", label_visibility="collapsed",
            )
            st.markdown(
                '<div class="login-field-label login-password-label">PASSWORD</div>',
                unsafe_allow_html=True,
            )
            password = st.text_input(
                "Password", type="password", placeholder="Enter your password",
                key="login_password", label_visibility="collapsed",
            )

            wait = _locked_out()
            submitted = st.button(
                "Sign In  →", key="login_submit",
                use_container_width=True, type="primary", disabled=wait > 0,
            )

            if wait > 0:
                st.error(f"Too many failed attempts. Try again in {wait}s.")
            elif submitted:
                if not email.strip() or not password:
                    st.error("Please enter your email and password.")
                elif authenticate(email, password):
                    st.session_state.authenticated = True
                    st.session_state.current_user = email.strip().lower()
                    st.session_state.login_failures = 0
                    st.session_state.pop("login_password", None)
                    st.rerun()
                else:
                    failures = st.session_state.get("login_failures", 0) + 1
                    st.session_state.login_failures = failures
                    if failures >= MAX_LOGIN_FAILURES:
                        st.session_state.login_locked_until = time.time() + LOCKOUT_SECONDS
                        st.session_state.login_failures = 0
                        st.error(f"Too many failed attempts. Locked for {LOCKOUT_SECONDS}s.")
                    else:
                        st.error("Invalid email or password.")

            if using_default_credentials():
                st.caption(
                    "Demo credentials are active. Set AQUASWARM_DEMO_PASSWORD "
                    "before sharing this app."
                )
            st.markdown('<p class="secure">🔒 Authorized personnel only</p>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

@st.cache_data(ttl=15, show_spinner=False)
def _backend_status() -> dict:
    return get_backend_status()


def render_app() -> None:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("current_user", "")
    st.session_state.setdefault("workflow_state", None)
    st.session_state.setdefault("run_error", "")

    if not st.session_state.authenticated:
        render_login()
        return

    st.markdown(base_css(), unsafe_allow_html=True)

    st.sidebar.markdown(
        """<div style="padding:8px 0 10px 0;">
          <div style="color:#f6feff;font-weight:800;font-size:19px;letter-spacing:-.2px;">💧 AquaSwarm Control</div>
          <div style="color:#8fb7c4;font-size:11px;margin-top:3px;">Manager operations workspace</div>
        </div>""",
        unsafe_allow_html=True,
    )

    status = _backend_status()

    try:
        tank_options = get_tank_options()
    except Exception as exc:
        render_dashboard(
            None,
            run_error=f"Backend data unavailable — {exc}",
            backend_status=status,
        )
        if st.sidebar.button("↻ Retry backend connection", use_container_width=True):
            _backend_status.clear()
            st.rerun()
        with st.sidebar.expander("Diagnostics"):
            st.json(status)
        return

    selected_default = st.session_state.get("selected_tank_id", tank_options[0])
    if selected_default not in tank_options:
        selected_default = tank_options[0]

    selected_tank = st.sidebar.selectbox(
        "Select Tank", tank_options,
        index=tank_options.index(selected_default), key="selected_tank_id",
    )

    scenario_keys = list(SCENARIOS)
    scenario = st.sidebar.selectbox(
        "Data scenario",
        scenario_keys,
        format_func=lambda key: SCENARIOS[key],
        key="scenario",
        help=(
            "Live uses the tank's real backend reading. The other scenarios "
            "change the reading in memory to demonstrate how priority reacts "
            "and never write to the backend."
        ),
    )
    st.sidebar.caption(
        "Live data is the default. Simulations exercise the full pipeline "
        "without touching real tank levels."
    )

    workflow_state = st.session_state.get("workflow_state")
    current_status = str(getattr(workflow_state, "operation_status", "Ready"))
    if workflow_state is not None:
        st.sidebar.markdown(
            f'<div style="margin:10px 0 14px;padding:10px 12px;border:1px solid rgba(120,225,240,.2);'
            f'border-radius:12px;background:rgba(3,24,38,.7);">'
            f'<div style="color:#8fb7c4;font-size:9px;letter-spacing:1.4px;text-transform:uppercase;">Operation</div>'
            f'<div style="color:#effcff;font-size:12.5px;font-weight:700;margin-top:4px;">{current_status}</div></div>',
            unsafe_allow_html=True,
        )
    st.sidebar.markdown("---")

    run_disabled = current_status in BLOCKING_STATUSES

    if st.sidebar.button(
        "▶ Run Water Operation",
        use_container_width=True, type="primary", disabled=run_disabled,
    ):
        st.session_state.run_error = ""
        run_operation(selected_tank, scenario)  # ends with st.rerun()

    if run_disabled:
        st.sidebar.caption("Finish or reset the current operation to start a new one.")

    if st.sidebar.button("Reset Current Operation", use_container_width=True):
        st.session_state.workflow_state = None
        st.session_state.run_error = ""
        st.rerun()

    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = ""
        st.session_state.workflow_state = None
        st.session_state.run_error = ""
        st.rerun()

    with st.sidebar.expander("Backend status"):
        dot = "🟢" if status.get("ok") else "🔴"
        st.markdown(f"{dot} **{status.get('label', '?')}** · {status.get('tanks', 0)} tanks · {status.get('suppliers', 0)} suppliers")
        if status.get("error"):
            st.caption(status["error"])
        if st.button("Re-check", key="recheck_backend", use_container_width=True):
            _backend_status.clear()
            st.rerun()

    render_dashboard(
        st.session_state.workflow_state,
        approval_handler=handle_manager_decision,
        delivery_completion_handler=handle_delivery_completion,
        run_error=st.session_state.get("run_error", ""),
        backend_status=status,
    )


if __name__ == "__main__":
    render_app()