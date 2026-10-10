from __future__ import annotations

import threading
import time

import streamlit as st

from backend import users
from ui.auth_pages import render_auth_gate
from ui.components import build_client, get_tank_options
from ui.dashboard import live_html, progress_html, render_dashboard
from ui.data_admin import render_data, render_team
from ui.pages import (
    empty_state,
    header,
    render_alerts_activity,
    render_deliveries,
    render_overview,
    render_roadmap,
    render_suppliers,
)
from ui.theme import base_css, dashboard_css
from workflows.aquaswarm_flow import SCENARIOS, AquaSwarmFlow, AquaSwarmState

st.set_page_config(
    page_title="AquaSwarm AI",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

APPROVERS = {"manager", "admin"}
DELIVERY_CONFIRMERS = {"operator", "manager", "admin"}
DATA_MANAGERS = {"manager", "admin"}
BLOCKING_STATUSES = {"Awaiting Manager Approval", "Delivery Dispatched", "Delivery In Progress"}

FLASH = {
    "Awaiting Manager Approval": ("✅", "Analysis complete — the proposed allocation is waiting for approval."),
    "No Replenishment Required": ("✅", "Analysis complete — no replenishment is needed."),
    "No Eligible Supplier": ("⚠️", "Analysis complete — no supplier can cover this shortage."),
    "Pipeline Error": ("❌", "The analysis could not be completed."),
}


# ---------------------------------------------------------------------------
# Actions (permissions are enforced here as well as in the UI)
# ---------------------------------------------------------------------------

def _actor() -> str:
    user = st.session_state.user
    return f"{user['full_name']} ({user['email']})"


def resume_flow_from_state(workflow_state: AquaSwarmState) -> AquaSwarmFlow:
    restored = AquaSwarmState.model_validate(workflow_state.model_dump())
    return AquaSwarmFlow(initial_state=restored)


def handle_manager_decision(approved: bool, reason: str = "") -> bool:
    if st.session_state.user["role"] not in APPROVERS:
        st.error("Your role cannot approve or reject deliveries.")
        return False
    state = st.session_state.get("workflow_state")
    if state is None:
        st.error("No active water operation found.")
        return False
    try:
        with st.spinner("Recording the decision and running the next agents…"):
            flow = resume_flow_from_state(state)
            flow.manager_decision(approved=approved, decided_by=_actor(), reason=reason.strip())
        st.session_state.workflow_state = flow.state
        st.session_state.flash = ("✅", "Decision recorded." if approved else "Allocation rejected; a recovery plan was prepared.")
        return True
    except Exception as exc:
        st.error(f"Unable to process the decision: {exc}")
        return False


def handle_delivery_completion(actual_quantity: float, evidence: str = "") -> bool:
    if st.session_state.user["role"] not in DELIVERY_CONFIRMERS:
        st.error("Your role cannot confirm deliveries.")
        return False
    state = st.session_state.get("workflow_state")
    if state is None:
        st.error("No active water operation found.")
        return False
    try:
        with st.spinner("Verifying the delivery…"):
            flow = resume_flow_from_state(state)
            flow.complete_delivery(float(actual_quantity), evidence)
        st.session_state.workflow_state = flow.state
        st.session_state.flash = ("✅", "Delivery recorded and verified.")
        return True
    except Exception as exc:
        st.error(f"Unable to complete the delivery: {exc}")
        return False


# ---------------------------------------------------------------------------
# Running the pipeline with a live message bar
# ---------------------------------------------------------------------------

def run_operation(tank_id: str, scenario: str) -> None:
    """Run the agents in a worker thread and show professional live progress.

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
        except Exception as exc:
            outcome["error"] = exc

    started = time.monotonic()
    worker = threading.Thread(target=target, daemon=True)
    worker.start()

    st.html(dashboard_css())
    bar = st.empty()
    view = st.empty()
    bar.html(progress_html(flow.state, 0.0))

    previous_statuses: dict = {}
    previous_signature = None
    last_bar = 0.0

    while worker.is_alive():
        elapsed = time.monotonic() - started
        try:
            statuses = {n: r.status for n, r in list(flow.state.stages.items())}
            signature = (tuple(sorted(statuses.items())), len(flow.state.activity), flow.state.operation_status)
        except RuntimeError:
            time.sleep(0.1)
            continue

        changed = signature != previous_signature
        if changed:
            fresh = {n for n, s in statuses.items() if s == "done" and previous_statuses.get(n) != "done"}
            view.html(live_html(flow.state, fresh))
            previous_statuses, previous_signature = statuses, signature
        if changed or elapsed - last_bar >= 1.0:
            bar.html(progress_html(flow.state, elapsed))
            last_bar = elapsed
        time.sleep(0.25)

    worker.join()

    state = flow.state
    error = outcome.get("error")
    message = ""
    if error is not None:
        message = state.error_message or f"{type(error).__name__}: {error}"
    elif state.operation_status == "Pipeline Error":
        message = state.error_message

    st.session_state.workflow_state = state
    st.session_state.run_error = message
    st.session_state.flash = FLASH.get(state.operation_status)
    st.rerun()


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_operation(client, user: dict) -> None:
    try:
        tank_options = get_tank_options()
    except Exception as exc:
        render_dashboard(None, run_error=f"Tank data unavailable — {exc}")
        if st.sidebar.button("Try again", use_container_width=True):
            st.rerun()
        return

    if not tank_options:
        header("Operation", "Run the AI agents on a tank")
        empty_state("Nothing to analyse yet",
                    "Add a site and a tank under Data, record a reading, then return here to start an operation.")
        return

    default = st.session_state.get("selected_tank_id", tank_options[0])
    if default not in tank_options:
        default = tank_options[0]
    tank = st.sidebar.selectbox("Select tank", tank_options, index=tank_options.index(default), key="selected_tank_id")
    scenario = st.sidebar.selectbox("Operating scenario", list(SCENARIOS), format_func=lambda k: SCENARIOS[k], key="scenario")

    state = st.session_state.get("workflow_state")
    status = str(getattr(state, "operation_status", "Ready"))
    if state is not None:
        st.sidebar.markdown(
            f'<div class="userchip" style="margin-top:12px"><div><div class="rl">Operation</div>'
            f'<div class="nm">{status}</div></div></div>',
            unsafe_allow_html=True,
        )

    blocked = status in BLOCKING_STATUSES
    if st.sidebar.button("▶ Run water operation", use_container_width=True, type="primary", disabled=blocked):
        st.session_state.run_error = ""
        run_operation(tank, scenario)
    if blocked:
        st.sidebar.caption("Finish or reset the current operation to start a new one.")
    if st.sidebar.button("Reset current operation", use_container_width=True):
        st.session_state.workflow_state = None
        st.session_state.run_error = ""
        st.rerun()

    render_dashboard(
        st.session_state.get("workflow_state"),
        approval_handler=handle_manager_decision,
        delivery_completion_handler=handle_delivery_completion,
        run_error=st.session_state.get("run_error", ""),
        can_approve=user["role"] in APPROVERS,
        can_confirm_delivery=user["role"] in DELIVERY_CONFIRMERS,
    )


def sidebar_account(user: dict) -> None:
    with st.sidebar.expander("Account"):
        with st.form("change_password", clear_on_submit=True):
            current = st.text_input("Current password", type="password")
            new = st.text_input("New password", type="password")
            confirm = st.text_input("Confirm new password", type="password")
            go = st.form_submit_button("Change password", use_container_width=True)
        if go:
            if new != confirm:
                st.error("The new passwords do not match.")
            else:
                try:
                    users.change_password(user["id"], current, new)
                    st.success("Password changed.")
                except ValueError as exc:
                    st.error(str(exc))
    if st.sidebar.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# App shell
# ---------------------------------------------------------------------------

def render_app() -> None:
    st.session_state.setdefault("workflow_state", None)
    st.session_state.setdefault("run_error", "")

    user = st.session_state.get("user")
    if not user:
        render_auth_gate()
        return

    # Re-check the account on every run so a disabled user is signed out.
    try:
        current = users.get_user(user["id"])
    except Exception:
        current = None
    if not current or current["status"] != "ACTIVE":
        st.session_state.clear()
        st.rerun()
    st.session_state.user = user = current

    st.markdown(base_css(), unsafe_allow_html=True)

    flash = st.session_state.pop("flash", None)
    if flash:
        st.toast(flash[1], icon=flash[0])

    initials = "".join(part[0] for part in user["full_name"].split()[:2]).upper() or "?"
    st.sidebar.markdown(
        f"""<div style="padding:8px 0 12px 0;"><div style="color:#f6feff;font-weight:800;font-size:19px;letter-spacing:-.2px;">💧 AquaSwarm</div>
        <div style="color:#8fb7c4;font-size:11px;margin-top:3px;">Water operations control center</div></div>
        <div class="userchip"><div class="av">{initials}</div><div><div class="nm">{user['full_name']}</div>
        <div class="rl">{user['role']}</div></div></div>""",
        unsafe_allow_html=True,
    )

    pages = ["Overview", "Operation", "Deliveries", "Alerts & activity", "Suppliers", "Data"]
    if user["role"] == "admin":
        pages.append("Team access")
    pages.append("Roadmap")
    page = st.sidebar.radio("Navigate", pages, key="nav", label_visibility="collapsed")
    st.sidebar.markdown("---")

    client = build_client()
    try:
        if page == "Overview":
            render_overview(client)
        elif page == "Operation":
            page_operation(client, user)
        elif page == "Deliveries":
            render_deliveries(client)
        elif page == "Alerts & activity":
            render_alerts_activity(client)
        elif page == "Suppliers":
            render_suppliers(client, can_edit=user["role"] in DATA_MANAGERS)
        elif page == "Data":
            render_data(client, user["role"])
        elif page == "Team access" and user["role"] == "admin":
            render_team(user)
        else:
            render_roadmap()
    except Exception as exc:
        st.error(f"This page could not be loaded: {exc}")
        if st.button("Try again"):
            st.rerun()

    st.sidebar.markdown("---")
    sidebar_account(user)


if __name__ == "__main__":
    render_app()