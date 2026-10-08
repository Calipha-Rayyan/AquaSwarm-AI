from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import escape
from typing import Any, Dict, Iterable, Optional

import streamlit as st

from ui.theme import dashboard_css

PIPELINE_ORDER = [
    "Demand",
    "Anomaly",
    "Supply",
    "Allocation",
    "Approval",
    "Delivery",
    "Verification",
]

SCENARIO_LABELS = {
    "LIVE": "Live conditions",
    "DEMAND_SURGE": "Demand surge",
    "LOW_LEVEL": "Low reserve",
    "CRITICAL_LOW": "Critical shortage",
}

_WAVE_PATH = "M0 10 Q 50 0 100 10 T 200 10 T 300 10 T 400 10 V20 H0Z"
_WAVE_SVG = (
    f'<svg viewBox="0 0 400 20" preserveAspectRatio="none">'
    f'<path d="{_WAVE_PATH}"/></svg>'
)
_RIVER_LINE = (
    '<div class="aq-river-line"><svg viewBox="0 0 800 26" preserveAspectRatio="none">'
    '<path d="M0 13 Q 50 2 100 13 T 200 13 T 300 13 T 400 13 T 500 13 T 600 13 T 700 13 T 800 13" '
    'fill="none" stroke="#4de3f0" stroke-opacity=".55" stroke-width="2"/>'
    '<path d="M0 17 Q 60 7 120 17 T 240 17 T 360 17 T 480 17 T 600 17 T 720 17 T 840 17" '
    'fill="none" stroke="#8ff5e0" stroke-opacity=".3" stroke-width="1.5"/></svg></div>'
)


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def esc(value: Any) -> str:
    """Escape anything that came from an LLM, backend or user."""
    return escape(str(value), quote=True)


def _n(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return esc(value)
    return f"{number:,.0f}" if abs(number) >= 100 else f"{number:,.2f}".rstrip("0").rstrip(".")


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _compact(markup: str) -> str:
    """Remove indentation/newlines so nothing is parsed as markdown code."""
    return "".join(line.strip() for line in markup.splitlines())


def _format_eta(raw: Any) -> str:
    if not raw or str(raw).upper() == "UNKNOWN" or str(raw) == "—":
        return "Unknown"
    try:
        moment = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        local = moment.astimezone(timezone(timedelta(hours=5)))
        return local.strftime("%d %b %Y • %I:%M %p PKT")
    except (ValueError, TypeError):
        return esc(raw)


# --------------------------------------------------------------------------
# river pipeline
# --------------------------------------------------------------------------

_STATE_LABEL = {
    "pending": "Waiting",
    "running": "Analyzing",
    "active": "Active",
    "done": "Completed",
    "skipped": "Not required",
    "blocked": "Blocked",
    "rejected": "Rejected",
    "error": "Failed",
}


def _stage_label(name: str, status: str) -> str:
    if name == "Approval":
        return {"running": "AI review", "active": "Awaiting decision", "done": "Approved"}.get(
            status, _STATE_LABEL.get(status, status.title())
        )
    if name == "Delivery" and status == "active":
        return "In transit"
    if name == "Verification" and status == "blocked":
        return "Review required"
    if name == "Verification" and status == "done":
        return "Verified"
    return _STATE_LABEL.get(status, status.title())


def pipeline_html(
    stages: Dict[str, Any],
    fresh: Optional[Iterable[str]] = None,
    order: Optional[list] = None,
) -> str:
    """The agent pipeline drawn as a river of connected pools."""
    fresh_set = set(fresh or [])
    names = list(order or PIPELINE_ORDER)
    if "Replanning" in stages and "Replanning" not in names:
        names.append("Replanning")

    parts = []
    previous_status = "pending"
    for index, name in enumerate(names, start=1):
        record = stages.get(name)
        status = str(_get(record, "status", "pending"))
        detail = str(_get(record, "detail", "") or "")
        human = name == "Approval"
        is_fresh = name in fresh_set

        # water flows into a stage once the previous stage has completed
        if status == "skipped" or status == "blocked" and previous_status != "done":
            link = "dead"
        elif previous_status == "done" and status in {"running", "active"}:
            link = "flow"
        elif previous_status == "done" and status in {"done", "rejected", "error", "blocked"}:
            link = "full"
        else:
            link = ""
        if link == "full" and is_fresh:
            link += " fresh"

        symbol = {
            "done": "✓", "skipped": "—", "blocked": "!", "error": "✕", "rejected": "✕",
        }.get(status, str(index))

        classes = f"stage {status}{' human' if human else ''}{' fresh' if is_fresh else ''}"
        parts.append(
            f'<div class="{classes}">'
            f'<div class="link {link}"><div class="w"></div><i class="drop"></i><i class="drop d2"></i></div>'
            f'<div class="node"><span class="ring"></span><span class="swirl"></span>{symbol}</div>'
            f'<div class="txt"><div class="sname">{esc(name)}</div>'
            f'<div class="sstate">{esc(_stage_label(name, status))}</div>'
            f'<div class="sdetail">{esc(detail)}</div></div></div>'
        )
        previous_status = status if name != "Replanning" else previous_status

    return f'<div class="river">{"".join(parts)}</div>'


def live_html(state: Any, fresh: Optional[Iterable[str]] = None) -> str:
    """Compact live view shown while the agents are working."""
    stages = _get(state, "stages", {}) or {}
    tank = esc(_get(state, "selected_tank_id", "—"))
    scenario = str(_get(state, "scenario", "LIVE"))
    status = esc(_get(state, "operation_status", "Running"))
    activity = list(_get(state, "activity", []) or [])[-6:]

    rows = "".join(
        f'<div class="li {esc(a.get("level", "info"))}"><span class="t">{esc(a.get("time", ""))}</span>'
        f'<span class="a">{esc(a.get("agent", ""))}</span><span class="m">{esc(a.get("message", ""))}</span></div>'
        for a in reversed(activity)
    )
    sim = (
        f'<span class="aq-chip sim">Scenario · {esc(SCENARIO_LABELS.get(scenario, scenario))}</span>'
        if scenario != "LIVE" else ""
    )
    return _compact(
        f"""
        <div class="aq">
          <div class="card river-card">
            <div class="rhead">
              <div><div class="rtitle">Agents are flowing through {tank}</div>
              <div class="rop">{status}</div></div>
              <div class="aq-right">{sim}<span class="aq-chip">Live</span></div>
            </div>
            {pipeline_html(stages, fresh)}
          </div>
          <div class="card" style="margin-top:14px"><div class="ctitle">Agent activity</div>
          <div class="log" style="margin-top:8px">{rows or '<div class="li"><span class="m">Starting…</span></div>'}</div></div>
        </div>
        """
    )


# --------------------------------------------------------------------------
# pieces
# --------------------------------------------------------------------------

def _tank_html(fill: float, capacity: float, level: float, target: float, critical_pct: float, low: bool) -> str:
    fill = min(max(fill, 0.0), 100.0)
    target_pct = min(max(target / capacity * 100.0, 0.0), 100.0) if capacity else 0.0
    water_cls = "water low" if low else "water"
    return (
        f'<div class="tank">'
        f'<div class="{water_cls}" style="height:{fill:.1f}%">'
        f'<div class="wave">{_WAVE_SVG}</div><div class="wave b">{_WAVE_SVG}</div>'
        f'<div class="bubbles"><i></i><i></i><i></i></div></div>'
        f'<div class="mark" style="bottom:{target_pct:.1f}%"><span>TARGET</span></div>'
        f'<div class="mark crit" style="bottom:{critical_pct:.1f}%"><span>CRITICAL</span></div>'
        f'<div class="tank-pct">{fill:.0f}%</div></div>'
    )


def _supplier_table(supply_result: Any, ranking: list) -> str:
    recommended = _get(supply_result, "recommended_supplier")
    required = None
    rows = []
    for option in _get(supply_result, "suppliers", []) or []:
        sid = str(_get(option, "supplier_id"))
        available = _get(option, "available")
        qty = float(_get(option, "available_quantity", 0))
        if sid == recommended:
            cls, pill = "rec", '<span class="pill rec">RECOMMENDED</span>'
        elif sid in ranking:
            cls, pill = "", f'<span class="pill el">ELIGIBLE #{ranking.index(sid) + 1}</span>'
        elif available is False:
            cls, pill = "", '<span class="pill off">UNAVAILABLE</span>'
        else:
            cls, pill = "", '<span class="pill no">TOO SMALL</span>'
        eta = _get(option, "eta_minutes")
        rows.append(
            f'<tr class="{cls}"><td><b>{esc(sid)}</b><br><span style="color:#8fb7c4;font-size:11px">{esc(_get(option, "name", ""))}</span></td>'
            f'<td>{_n(qty)}</td><td>{_n(_get(option, "distance_km", 0))} km</td>'
            f'<td>{_n(_get(option, "estimated_cost", 0))}</td>'
            f'<td>{esc(eta) + " min" if eta is not None else "—"}</td><td>{pill}</td></tr>'
        )
    return (
        '<div class="tablescroll"><table class="sup"><tr><th>Supplier</th><th>Available</th>'
        '<th>Distance</th><th>Cost</th><th>ETA</th><th>Status</th></tr>' + "".join(rows) + "</table></div>"
    )


def _banner(kind: str, title: str, text: str) -> str:
    icon = {"err": "!", "warn": "i", "ok": "✓"}[kind]
    return (
        f'<div class="banner {kind}"><div class="ic">{icon}</div>'
        f'<div><b>{esc(title)}</b><br>{esc(text)}</div></div>'
    )


# --------------------------------------------------------------------------
# main renderer
# --------------------------------------------------------------------------

def render_dashboard(
    workflow_state=None,
    approval_handler=None,
    delivery_completion_handler=None,
    run_error: str = "",
    backend_status: Optional[dict] = None,
):
    """Render the AquaSwarm manager dashboard from the current flow state."""
    st.html(dashboard_css())

    state = workflow_state
    water = _get(state, "water_data")
    demand = _get(state, "demand_result")
    anomaly = _get(state, "anomaly_result")
    supply = _get(state, "supply_result")
    allocation = _get(state, "allocation_result")
    recommendation = _get(state, "approval_recommendation")
    approval = _get(state, "manager_approval_result")
    delivery = _get(state, "delivery_result")
    verification = _get(state, "verification_result")
    replanning = _get(state, "replanning_result")
    stages = _get(state, "stages", {}) or {}
    assessment = _get(state, "assessment") or {}
    status_text = str(_get(state, "operation_status", "Ready"))
    scenario = str(_get(state, "scenario", "LIVE"))
    data_source = str(_get(state, "data_source", ""))

    chips = [f'<span class="aq-chip">{esc(status_text)}</span>']
    if scenario != "LIVE":
        chips.append(f'<span class="aq-chip sim">Scenario · {esc(SCENARIO_LABELS.get(scenario, scenario))}</span>')
    ai_used = set(_get(state, "ai_agents", []) or [])
    if ai_used:
        chips.append(f'<span class="aq-chip ok">AI agents active · {len(ai_used)}</span>')
    elif _get(state, "llm_warnings", []):
        chips.append('<span class="aq-chip bad">AI agents unavailable</span>')

    st.html(
        _compact(
            f"""
            <div class="aq"><div class="aq-header">
              <div><div class="aq-brand"><span class="aq-drop"></span>AquaSwarm AI</div>
              <div class="aq-sub">Intelligent water operations · from source to tank</div></div>
              <div class="aq-right">{"".join(chips)}</div></div>{_RIVER_LINE}</div>
            """
        )
    )

    if run_error:
        st.html(_compact(f'<div class="aq">{_banner("err", "The operation could not complete", run_error)}</div>'))

    if state is None:
        st.html(
            _compact(
                """
                <div class="aq"><div class="card ready"><div class="big-drop"></div><div>
                <div class="ctitle" style="font-size:20px">Ready for a water operation</div>
                <div class="csub" style="font-size:13px;margin-top:6px">Select a tank in the control panel and start an operation. The agents assess demand, check for anomalies,
                compare suppliers and propose an allocation for your approval.</div></div></div>
                <div class="features">
                <div class="card"><div class="fk">01 · MONITOR</div><div class="ft">Demand + anomaly detection</div>
                <div class="fx">Days of cover, fill level and net balance decide the priority.</div></div>
                <div class="card"><div class="fk">02 · DECIDE</div><div class="ft">Supply + allocation</div>
                <div class="fx">Suppliers are filtered and ranked deterministically, then sized to the shortage.</div></div>
                <div class="card"><div class="fk">03 · AUTHORIZE</div><div class="ft">Human approval gate</div>
                <div class="fx">Nothing is dispatched until a manager approves it.</div></div></div></div>
                """
            )
        )
        return

    if water is None:
        message = _get(state, "error_message") or "The operation stopped before tank data was loaded."
        st.html(_compact(f'<div class="aq">{_banner("err", "Tank data unavailable", message)}</div>'))
        return

    tank_id = str(_get(water, "tank_id", "—"))
    level = float(_get(water, "current_level", 0))
    capacity = float(_get(water, "capacity", 1)) or 1.0
    demand_per_day = float(_get(water, "daily_demand", 0))
    inflow = float(_get(water, "inflow", 0))
    fill = float(assessment.get("fill_percentage", level / capacity * 100))
    target = float(assessment.get("target_level", 0))
    shortage = float(_get(demand, "shortage", assessment.get("shortage", 0)) or 0)
    priority = str(_get(demand, "priority", assessment.get("priority", "LOW"))).upper()
    cover_label = str(assessment.get("cover_label", "—"))
    net_change = float(assessment.get("net_daily_change", inflow - demand_per_day))
    needs_water = shortage > 0

    error_message = str(_get(state, "error_message", "") or "")
    if error_message and status_text == "Pipeline Error":
        st.html(_compact(f'<div class="aq">{_banner("err", "A pipeline stage failed", error_message)}</div>'))

    # ---- KPIs
    st.html(
        _compact(
            f"""
            <div class="aq"><div class="kpis">
              <div class="card"><div class="kpi-label"><span>Current level</span><span>💧</span></div>
                <div class="kpi-value">{_n(level)}<span class="kpi-unit">units</span></div>
                <div class="kpi-meta">{fill:.0f}% of {_n(capacity)} capacity</div></div>
              <div class="card"><div class="kpi-label"><span>Days of cover</span><span>⏳</span></div>
                <div class="kpi-value">{esc(cover_label.replace(" days", ""))}<span class="kpi-unit">{"days" if "days" in cover_label else ""}</span></div>
                <div class="kpi-meta">Net change {net_change:+,.0f} units/day</div></div>
              <div class="card"><div class="kpi-label"><span>Daily demand</span><span>📈</span></div>
                <div class="kpi-value">{_n(demand_per_day)}<span class="kpi-unit">units</span></div>
                <div class="kpi-meta">Inflow {_n(inflow)} units/day</div></div>
              <div class="card"><div class="kpi-label"><span>Shortage</span><span>🌊</span></div>
                <div class="kpi-value">{_n(shortage)}<span class="kpi-unit">units</span></div>
                <div class="kpi-meta">{"Below target reserve of " + _n(target) if needs_water else "Reserve is sufficient"}</div></div>
              <div class="card"><div class="kpi-label"><span>Priority</span><span>⚠</span></div>
                <div class="pbadge p-{priority.lower()}"><i></i>{esc(priority)}</div>
                <div class="kpi-meta">{"Replenishment needed" if needs_water else "No replenishment required"}</div></div>
            </div></div>
            """
        )
    )

    # ---- Tank intelligence
    st.html('<div class="aq"><div class="aq-h">Tank Intelligence</div><div class="aq-c">Live condition and water balance</div></div>')
    low = fill < 40 and needs_water
    tank_text = (
        "Below target reserve — replenishment required"
        if needs_water else "Storage level within operating range"
    )
    st.html(
        _compact(
            f"""
            <div class="aq"><div class="grid2">
              <div class="card"><div class="chead"><div><div class="ctitle">Tank status</div>
                <div class="csub">Current storage level</div></div><div class="tag">{esc(tank_id)}</div></div>
                <div class="tankwrap">{_tank_html(fill, capacity, level, target, 20.0, low)}
                  <div class="tank-info"><div class="big">{_n(level)}<small>/ {_n(capacity)} units</small></div>
                    <div class="meter"><i style="width:{min(max(fill, 0), 100):.1f}%"></i></div>
                    <div class="csub">{fill:.0f}% filled · target reserve {_n(target)}</div>
                    <div class="stat-line"><span class="dot {"" if needs_water else "ok"}"></span>{esc(tank_text)}</div></div></div></div>
              <div class="card"><div class="chead"><div><div class="ctitle">Water balance</div>
                <div class="csub">Deterministic assessment</div></div></div>
                <div class="row"><span class="l">Daily demand</span><span class="v">{_n(demand_per_day)}<small>units</small></span></div>
                <div class="row"><span class="l">Daily inflow</span><span class="v">{_n(inflow)}<small>units</small></span></div>
                <div class="row"><span class="l">Net daily change</span><span class="v {"warn" if net_change < 0 else "good"}">{net_change:+,.0f}<small>units</small></span></div>
                <div class="row"><span class="l">Target reserve</span><span class="v">{_n(target)}<small>units</small></span></div>
                <div class="row"><span class="l">Calculated shortage</span><span class="v {"warn" if needs_water else "good"}">{_n(shortage)}<small>units</small></span></div>
                <div class="row"><span class="l">Anomaly check</span><span class="v">{esc(_get(anomaly, "anomaly_type", "—") or "NONE").replace("_", " ").title() if anomaly else "—"}</span></div>
              </div></div></div>
            """
        )
    )

    if not needs_water and status_text == "No Replenishment Required":
        st.html(
            _compact(
                f'<div class="aq">{_banner("ok", "No replenishment required", f"{tank_id} holds more than its target reserve, so procurement and delivery were skipped. Anomaly monitoring still ran.")}</div>'
            )
        )

    # ---- Pipeline
    op_line = f"{tank_id}" + (f" · {_n(_get(allocation, 'allocated_quantity'))} units" if allocation else "")
    st.html('<div class="aq"><div class="aq-h">AI Agent Workflow</div><div class="aq-c">Autonomous decision pipeline with human authorization</div></div>')
    replan_html = ""
    if replanning is not None:
        replan_html = (
            '<div class="replan"><div class="node" style="border-color:#9bb4ff;color:#9bb4ff">↺</div>'
            f'<div><b>Replanning</b> · {esc(_get(replanning, "action", "")).replace("_", " ").title()} — {esc(_get(replanning, "reason", ""))}</div></div>'
        )
    pipeline_stages = {k: v for k, v in stages.items() if k != "Replanning"}
    st.html(
        _compact(
            f"""<div class="aq"><div class="card river-card"><div class="rhead">
            <div class="rtitle">AquaSwarm Decision Pipeline</div><div class="rop">{esc(op_line)}</div></div>
            {pipeline_html(pipeline_stages)}{replan_html}</div></div>"""
        )
    )

    # ---- Approval gate
    awaiting = (
        approval_handler is not None
        and approval is None
        and allocation is not None
        and status_text == "Awaiting Manager Approval"
    )
    if awaiting:
        rec_html = ""
        if recommendation is not None:
            ok = bool(_get(recommendation, "approved"))
            rec_html = (
                f'<div class="ai-rec"><span class="badge {"ok" if ok else "no"}">AI REVIEW · {esc(_get(recommendation, "manager_decision", ""))}</span>'
                f'<div>{esc(_get(recommendation, "reasoning", ""))}</div></div>'
            )
        st.html(
            _compact(
                f"""
                <div class="aq"><div class="card approval"><div class="chead"><div>
                  <div class="ctitle" style="font-size:18px">Manager approval required</div>
                  <div class="csub">Nothing is dispatched until you authorize it</div></div>
                  <div class="tag" style="color:#9bb4ff;border-color:rgba(155,180,255,.45)">AWAITING DECISION</div></div>
                  <div class="grid2" style="margin-top:6px"><div>
                    <div class="row"><span class="l">Quantity</span><span class="v">{_n(_get(allocation, "allocated_quantity"))}<small>units</small></span></div>
                    <div class="row"><span class="l">Supplier</span><span class="v">{esc(_get(allocation, "supplier_id"))}</span></div>
                    <div class="row"><span class="l">Priority</span><span class="v">{esc(_get(allocation, "priority"))}</span></div></div>
                    <div class="note"><b>Allocation reasoning</b><br>{esc(_get(allocation, "reasoning", ""))}</div></div>
                  {rec_html}</div></div>
                """
            )
        )
        reason = st.text_area(
            "Manager decision note",
            key=f"manager_approval_reason_{tank_id}",
            placeholder="Add a short reason for the approval or rejection…",
            height=90,
        )
        approve_col, reject_col = st.columns(2)
        with approve_col:
            if st.button("✓  APPROVE ALLOCATION", key=f"approve_allocation_{tank_id}",
                         use_container_width=True, type="primary"):
                if approval_handler(True, reason.strip()) is not False:
                    st.rerun()
        with reject_col:
            if st.button("✕  REJECT ALLOCATION", key=f"reject_allocation_{tank_id}",
                         use_container_width=True):
                if approval_handler(False, reason.strip()) is not False:
                    st.rerun()

    # ---- Delivery receipt (separate physical action)
    delivery_status = str(_get(delivery, "status", "")).upper()
    if (
        delivery_completion_handler is not None
        and approval is not None
        and _get(approval, "approved")
        and delivery is not None
        and delivery_status == "DISPATCHED"
    ):
        st.html(
            _compact(
                '<div class="aq"><div class="card approval"><div class="ctitle" style="font-size:18px">Delivery completion</div>'
                '<div class="csub">Enter the physically measured quantity received before verification.</div></div></div>'
            )
        )
        actual = st.number_input(
            "Actual delivered quantity", min_value=0.0,
            value=float(_get(allocation, "allocated_quantity", 0)), step=1.0,
            key=f"actual_delivery_quantity_{tank_id}",
        )
        if st.button("✓  CONFIRM DELIVERY RECEIVED", key=f"confirm_delivery_{tank_id}",
                     use_container_width=True, type="primary"):
            if delivery_completion_handler(actual) is not False:
                st.rerun()

    # ---- Supplier ranking
    if supply is not None:
        st.html(
            _compact(
                f"""<div class="aq"><div class="aq-h">Supplier Ranking</div>
                <div class="aq-c">Eligibility and ranking are deterministic: cost, then distance, then capacity</div>
                <div class="card">{_supplier_table(supply, list(_get(state, "supply_ranking", []) or []))}
                <div class="note"><b>Supply agent</b> · {esc(_get(supply, "reasoning", ""))}</div></div></div>"""
            )
        )

    # ---- Delivery + verification
    if delivery is not None:
        verified = _get(verification, "verified")
        v_text = (
            "Verified" if verified is True
            else "Review required" if verified is False
            else "Waiting for delivery"
        )
        approved_qty = _get(allocation, "allocated_quantity", 0)
        st.html(
            _compact(
                f"""
                <div class="aq"><div class="aq-h">Current Operation</div><div class="aq-c">Water movement and fulfilment</div>
                <div class="grid2">
                <div class="card"><div class="chead"><div><div class="ctitle">Delivery</div><div class="csub">Approved water movement</div></div>
                  <div class="tag">{esc(_get(delivery, "supplier_id"))}</div></div>
                  <div class="row"><span class="l">Quantity</span><span class="v">{_n(_get(delivery, "quantity"))}<small>units</small></span></div>
                  <div class="row"><span class="l">Status</span><span class="v">{esc(delivery_status.title())}</span></div>
                  <div class="row"><span class="l">Estimated arrival</span><span class="v">{_format_eta(_get(delivery, "estimated_arrival"))}</span></div></div>
                <div class="card"><div class="chead"><div><div class="ctitle">Verification</div><div class="csub">Delivery confirmation</div></div></div>
                  <div class="row"><span class="l">Result</span><span class="v {"good" if verified is True else "warn" if verified is False else ""}">{v_text}</span></div>
                  <div class="row"><span class="l">Approved quantity</span><span class="v">{_n(approved_qty)}<small>units</small></span></div>
                  <div class="row"><span class="l">Actual quantity</span><span class="v">{_n(_get(delivery, "quantity"))}<small>units</small></span></div>
                  <div class="row"><span class="l">Discrepancy</span><span class="v">{_n(_get(verification, "discrepancy", 0))}<small>units</small></span></div></div>
                </div></div>
                """
            )
        )

    updated = _get(state, "updated_level")
    if updated is not None and verification is not None and _get(verification, "verified"):
        st.html(
            _compact(
                f'<div class="aq">{_banner("ok", "Loop closed", f"The verified delivery was recorded. {tank_id} is now at {_n(updated)} units, so the next run uses the new level to set priority.")}</div>'
            )
        )

    # ---- warnings
    sync_warnings = list(_get(state, "sync_warnings", []) or [])
    llm_warnings = list(_get(state, "llm_warnings", []) or [])
    if llm_warnings:
        st.html(
            _compact(
                f'<div class="aq">{_banner("warn", "AI analysis was unavailable for some stages", "Standard operating rules were applied to those stages, so the safety limits still hold. Details: " + llm_warnings[0])}</div>'
            )
        )
    if sync_warnings:
        st.html(
            _compact(
                f'<div class="aq">{_banner("warn", "Notice", sync_warnings[-1])}</div>'
            )
        )

    # ---- activity log
    activity = list(_get(state, "activity", []) or [])
    if activity:
        rows = "".join(
            f'<div class="li {esc(a.get("level", "info"))}"><span class="t">{esc(a.get("time", ""))}</span>'
            f'<span class="a">{esc(a.get("agent", ""))}</span><span class="m">{esc(a.get("message", ""))}</span></div>'
            for a in reversed(activity[-40:])
        )
        st.html(
            _compact(
                f'<div class="aq"><div class="aq-h">Agent Activity</div><div class="aq-c">Audit trail for operation {esc(_get(state, "operation_id", ""))}</div>'
                f'<div class="card"><div class="log">{rows}</div></div></div>'
            )
        )