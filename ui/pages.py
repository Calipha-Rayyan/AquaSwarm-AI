from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from tools.water_tools import assess_tank, default_policy, plan_allocation
from ui.dashboard import _compact, _n, esc
from ui.theme import dashboard_css

_PRIORITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
_ACTIVE_DELIVERY = {"PENDING", "APPROVED", "DISPATCHED"}

_EXTRA_CSS = """
<style>
.tgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin-top:6px;}
.tcard .bar{height:10px;border-radius:10px;background:rgba(120,225,240,.12);overflow:hidden;margin:12px 0 8px;}
.tcard .bar i{display:block;height:100%;border-radius:10px;background:linear-gradient(90deg,#12a8b8,#4de3f0,#8ff5e0,#4de3f0);
  background-size:200% 100%;animation:aqFlow 2.4s linear infinite;}
.tcard .bar.low i{background:linear-gradient(90deg,#ff7b72,#ffa05a);}
.tcard .meta{display:flex;justify-content:space-between;font-size:12px;color:#8fb7c4;margin-top:4px;}
.tcard .meta b{color:#e6fafd;}
.pill.road-live{background:rgba(143,245,224,.14);color:#8ff5e0;} .pill.road-part{background:rgba(255,210,122,.14);color:#ffd27a;}
.pill.road-plan{background:rgba(143,183,196,.14);color:#8fb7c4;}
.empty{text-align:center;padding:38px 20px;}
.empty .big-drop{margin:0 auto 18px;}
</style>
"""


def header(title: str, subtitle: str) -> None:
    st.html(dashboard_css() + _EXTRA_CSS)
    st.markdown(f'<div class="pg-title">{esc(title)}</div><div class="pg-sub">{esc(subtitle)}</div>',
                unsafe_allow_html=True)


def _banner(kind: str, title: str, text: str) -> str:
    icon = {"err": "!", "warn": "i", "ok": "✓"}[kind]
    return (f'<div class="aq"><div class="banner {kind}"><div class="ic">{icon}</div>'
            f'<div><b>{esc(title)}</b><br>{esc(text)}</div></div></div>')


def empty_state(title: str, text: str) -> None:
    st.html(_compact(
        f'<div class="aq"><div class="card empty"><div class="big-drop" style="width:46px;height:46px;border-radius:0 50% 50% 50%;'
        f'transform:rotate(45deg);background:linear-gradient(135deg,#d6f7fb,#12a8b8);box-shadow:0 0 30px rgba(77,227,240,.5)"></div>'
        f'<div class="ctitle" style="font-size:19px">{esc(title)}</div><div class="csub" style="font-size:13px;margin-top:6px">{esc(text)}</div></div></div>'
    ))


def _safe(call, default):
    try:
        return call()
    except Exception:
        return default


# ---------------------------------------------------------------- fleet data
def fleet_snapshot(client) -> list[dict]:
    """Deterministic assessment of every tank from stored readings."""
    from config.settings import AQUASWARM_DEFAULT_INFLOW

    tanks = client.get_tanks()
    history: dict[str, list[float]] = {}
    for row in client.get_consumption(limit=1000):  # newest first
        history.setdefault(row["tank_code"], []).append(float(row["amount"]))

    snapshot = []
    for tank in tanks:
        amounts = history.get(tank["tank_code"], [])[:7]
        demand = sum(amounts) / len(amounts) if amounts else 0.0
        a = assess_tank(tank["current_level"], tank["capacity"], demand,
                        AQUASWARM_DEFAULT_INFLOW, default_policy())
        snapshot.append({
            "tank_code": tank["tank_code"], "name": tank["name"], "site_name": tank["site_name"],
            "criticality": tank.get("criticality") or "MEDIUM", "population": tank.get("population") or 0,
            "capacity": float(tank["capacity"]), "level": float(tank["current_level"]),
            "demand": demand, "readings": len(amounts), "a": a,
        })
    snapshot.sort(key=lambda t: (-_PRIORITY_RANK[t["a"].priority],
                                 t["a"].days_of_cover if t["a"].days_of_cover is not None else 1e9))
    return snapshot


def _supplier_pool(client) -> list[dict]:
    return [{
        "supplier_id": s["supplier_code"], "name": s["name"], "available": bool(s["available"]),
        "available_quantity": float(s["capacity"]) if s["available"] else 0.0,
        "estimated_cost": float(s["estimated_cost"]), "distance_km": float(s["distance_km"]),
        "eta_minutes": s["eta_minutes"],
    } for s in client.get_suppliers()]


# ---------------------------------------------------------------- overview
def render_overview(client) -> None:
    header("Network overview", "Water, risk and supply across every site")
    snapshot = fleet_snapshot(client)
    if not snapshot:
        empty_state("No tanks yet", "Add your first site and tank under Data, then record a reading. The overview fills in automatically.")
        return

    stored = sum(t["level"] for t in snapshot)
    capacity = sum(t["capacity"] for t in snapshot)
    at_risk = [t for t in snapshot if t["a"].priority in {"HIGH", "CRITICAL"}]
    open_alerts = _safe(lambda: client.get_alerts(status="OPEN"), [])
    active = [d for d in _safe(client.get_delivery_requests, []) if d.get("status") in _ACTIVE_DELIVERY]
    sites = len({t["site_name"] for t in snapshot})

    st.html(_compact(f"""
        <div class="aq"><div class="kpis">
          <div class="card"><div class="kpi-label"><span>Water stored</span><span>💧</span></div>
            <div class="kpi-value">{_n(stored)}<span class="kpi-unit">units</span></div>
            <div class="kpi-meta">{stored / capacity * 100:.0f}% of {_n(capacity)} across {len(snapshot)} tanks</div></div>
          <div class="card"><div class="kpi-label"><span>Sites at risk</span><span>⚠</span></div>
            <div class="kpi-value">{len({t['site_name'] for t in at_risk})}<span class="kpi-unit">of {sites}</span></div>
            <div class="kpi-meta">{len(at_risk)} tank(s) high or critical</div></div>
          <div class="card"><div class="kpi-label"><span>Open alerts</span><span>🔔</span></div>
            <div class="kpi-value">{len(open_alerts)}</div><div class="kpi-meta">Awaiting review</div></div>
          <div class="card"><div class="kpi-label"><span>Active deliveries</span><span>🚚</span></div>
            <div class="kpi-value">{len(active)}</div><div class="kpi-meta">Pending, approved or dispatched</div></div>
        </div></div>"""))

    cards = []
    for t in snapshot:
        a = t["a"]
        low = a.fill_percentage < 40
        cards.append(
            f'<div class="card tcard"><div class="chead"><div><div class="ctitle">{esc(t["site_name"])}</div>'
            f'<div class="csub">{esc(t["tank_code"])} · {esc(t["name"])}</div></div>'
            f'<span class="pbadge p-{a.priority.lower()}" style="font-size:12px;padding:4px 10px;margin:0"><i></i>{a.priority}</span></div>'
            f'<div class="bar{" low" if low else ""}"><i style="width:{a.fill_percentage:.0f}%"></i></div>'
            f'<div class="meta"><span>Level <b>{_n(t["level"])}</b> / {_n(t["capacity"])}</span><b>{a.fill_percentage:.0f}%</b></div>'
            f'<div class="meta"><span>Time to empty</span><b>{esc(a.cover_label)}</b></div>'
            f'<div class="meta"><span>Shortage</span><b>{_n(a.shortage)}</b></div>'
            f'<div class="meta"><span>Readings used</span><b>{t["readings"]}</b></div></div>'
        )
    st.html(f'<div class="aq"><div class="aq-h">Tank monitoring</div><div class="aq-c">Most urgent first</div>'
            f'<div class="tgrid">{"".join(cards)}</div></div>')

    needs = [{
        "tank_code": t["tank_code"], "site_name": t["site_name"], "shortage": t["a"].shortage,
        "priority": t["a"].priority, "criticality": t["criticality"], "population": t["population"],
        "days_of_cover": t["a"].days_of_cover,
    } for t in snapshot]
    st.html('<div class="aq"><div class="aq-h">Supply plan</div><div class="aq-c">'
            'Available supplier volume shared by urgency, site criticality and population. Advisory — open a tank in Operation to prepare an approval.</div></div>')
    if not any(n["shortage"] > 0 for n in needs):
        st.html(_banner("ok", "No replenishment needed", "Every tank holds at least its target reserve."))
        return
    plan = plan_allocation(needs, _supplier_pool(client))
    frame = pd.DataFrame([{
        "Tank": r["tank_code"], "Site": r["site_name"], "Priority": r["priority"],
        "Needed": round(r["shortage"]), "Allocated": round(r["allocated"]),
        "Supplier": r["supplier_id"] or "—", "Unmet": round(r["unmet"]),
    } for r in plan["allocations"]])
    st.dataframe(frame, hide_index=True, use_container_width=True)
    if plan["unmet_total"] > 0:
        st.html(_banner("warn", f"{_n(plan['unmet_total'])} units cannot be covered",
                        " ".join(plan["constraint_notes"]) or "Available supplier volume is lower than total demand."))
    else:
        st.html(_banner("ok", "All demand can be covered",
                        f"{_n(plan['total_allocated'])} units allocated across {len(plan['allocations'])} tank(s)."))


# ---------------------------------------------------------------- deliveries
def _frame(rows: list[dict], columns: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame([{label: row.get(key) for key, label in columns.items()} for row in rows])


def render_deliveries(client) -> None:
    header("Deliveries", "Requests, approvals and exceptions")
    deliveries = _safe(client.get_delivery_requests, [])
    verifications = _safe(client.get_verifications, [])
    cols = {"id": "ID", "tank_code": "Tank", "site_name": "Site", "supplier_name": "Supplier", "quantity": "Quantity",
            "actual_quantity": "Received", "status": "Status", "estimated_arrival": "ETA", "requested_at": "Requested", "notes": "Notes"}

    exceptions = [d for d in deliveries if d.get("status") == "DELIVERY_EXCEPTION"]
    bad_checks = [v for v in verifications if str(v.get("verification_status")) not in {"VERIFIED", "PENDING"}]

    active_tab, history_tab, exception_tab = st.tabs(
        [f"Active ({sum(d['status'] in _ACTIVE_DELIVERY for d in deliveries)})", "History",
         f"Exceptions ({len(exceptions) + len(bad_checks)})"])
    with active_tab:
        rows = [d for d in deliveries if d["status"] in _ACTIVE_DELIVERY]
        if rows:
            st.dataframe(_frame(rows, cols), hide_index=True, use_container_width=True)
        else:
            empty_state("No active deliveries", "Approved allocations appear here until they are delivered and verified.")
    with history_tab:
        if deliveries:
            st.dataframe(_frame(deliveries, cols), hide_index=True, use_container_width=True)
        else:
            empty_state("No deliveries yet", "Completed and cancelled requests are kept here for the audit trail.")
    with exception_tab:
        if exceptions:
            st.markdown("**Failed or flagged deliveries**")
            st.dataframe(_frame(exceptions, cols), hide_index=True, use_container_width=True)
        if bad_checks:
            st.markdown("**Verification discrepancies**")
            st.dataframe(_frame(bad_checks, {"delivery_request_id": "Delivery", "tank_code": "Tank", "site_name": "Site",
                                             "expected_quantity": "Expected", "actual_quantity": "Actual",
                                             "discrepancy": "Discrepancy", "verification_status": "Result",
                                             "verification_timestamp": "Checked", "note": "Note"}),
                         hide_index=True, use_container_width=True)
        if not exceptions and not bad_checks:
            st.html(_banner("ok", "No exceptions", "Every completed delivery matched its approved quantity."))


# ---------------------------------------------------------------- alerts + activity
def render_alerts_activity(client) -> None:
    header("Alerts & AI activity", "What the system noticed, and what each agent did")
    alerts = _safe(client.get_alerts, [])
    runs = _safe(client.get_agent_runs, [])
    alert_tab, activity_tab = st.tabs([f"Alerts ({len(alerts)})", f"Agent activity ({len(runs)})"])
    with alert_tab:
        if alerts:
            st.dataframe(_frame(alerts, {"timestamp": "Time", "severity": "Severity", "alert_type": "Type", "tank_code": "Tank",
                                         "site_name": "Site", "status": "Status", "message": "Evidence"}),
                         hide_index=True, use_container_width=True)
        else:
            empty_state("No alerts", "Critical shortages and abnormal consumption raise an alert automatically.")
    with activity_tab:
        if runs:
            st.dataframe(_frame(runs, {"timestamp": "Time", "agent_name": "Agent", "status": "Status",
                                       "input_summary": "Input", "output_summary": "Result", "operation_run_id": "Operation"}),
                         hide_index=True, use_container_width=True)
        else:
            empty_state("No agent activity yet", "Run an operation to see each agent's decision trail here.")


# ---------------------------------------------------------------- suppliers
def render_suppliers(client, can_edit: bool) -> None:
    header("Suppliers", "Capacity, price and delivery time of every tanker source")
    suppliers = client.get_suppliers()
    if suppliers:
        st.dataframe(_frame(suppliers, {"supplier_code": "Code", "name": "Supplier", "capacity": "Capacity",
                                        "estimated_cost": "Price", "eta_minutes": "ETA (min)", "distance_km": "Distance (km)",
                                        "available": "Available", "phone": "Phone", "last_updated": "Updated"})
                     .assign(Available=lambda d: d["Available"].map({1: "Yes", 0: "No"})),
                     hide_index=True, use_container_width=True)
    else:
        empty_state("No suppliers yet", "Add the tanker companies you can call. The supply agent ranks only suppliers you enter.")

    if not can_edit:
        st.caption("Managers and administrators can add or update suppliers.")
        return

    add_tab, edit_tab = st.tabs(["Add supplier", "Update supplier"])
    with add_tab:
        with st.form("add_supplier", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Supplier name")
            phone = c2.text_input("Phone (optional)")
            capacity = c1.number_input("Capacity (units)", min_value=0.0, value=0.0, step=500.0)
            price = c2.number_input("Price per delivery", min_value=0.0, value=0.0, step=100.0)
            eta = c1.number_input("ETA (minutes)", min_value=0, value=60, step=5)
            distance = c2.number_input("Distance (km)", min_value=0.0, value=0.0, step=1.0)
            available = st.checkbox("Available now", value=True)
            go = st.form_submit_button("Add supplier", type="primary", use_container_width=True)
        if go:
            try:
                client.create_supplier({"name": name, "capacity": capacity, "available": available, "distance_km": distance,
                                        "estimated_cost": price, "eta_minutes": int(eta), "phone": phone or None})
                st.success(f"{name} added.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with edit_tab:
        if not suppliers:
            st.info("Add a supplier first.")
            return
        chosen = st.selectbox("Supplier", suppliers, format_func=lambda s: f"{s['supplier_code']} · {s['name']}")
        with st.form(f"edit_supplier_{chosen['id']}"):
            c1, c2 = st.columns(2)
            capacity = c1.number_input("Capacity (units)", min_value=0.0, value=float(chosen["capacity"]), step=500.0)
            price = c2.number_input("Price per delivery", min_value=0.0, value=float(chosen["estimated_cost"]), step=100.0)
            eta = c1.number_input("ETA (minutes)", min_value=0, value=int(chosen["eta_minutes"]), step=5)
            distance = c2.number_input("Distance (km)", min_value=0.0, value=float(chosen["distance_km"]), step=1.0)
            available = st.checkbox("Available now", value=bool(chosen["available"]))
            go = st.form_submit_button("Save changes", type="primary", use_container_width=True)
        if go:
            try:
                client.update_supplier(chosen["id"], {"capacity": capacity, "estimated_cost": price, "eta_minutes": int(eta),
                                                      "distance_km": distance, "available": available})
                st.success("Supplier updated.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


# ---------------------------------------------------------------- roadmap
_ROADMAP = [
    ("Phase 2", "ESP32 + ultrasonic/flow sensors for real telemetry", "road-part", "Ingestion API ready",
     "Sensors can post levels and flow to the secured readings endpoint today."),
    ("Phase 2", "Mobile/WhatsApp notifications for managers and operators", "road-part", "E-mail alerts available",
     "High-priority alerts e-mail managers when SMTP is configured; WhatsApp is next."),
    ("Phase 2", "Real supplier/tanker network with geolocation and availability", "road-part", "Supplier directory live",
     "Suppliers, prices and availability are managed in-app; map-based location is next."),
    ("Phase 3", "ML-based demand forecasting and anomaly detection trained on site history", "road-plan", "Planned",
     "Today's baseline compares the latest reading with recent history; models follow once enough history exists."),
    ("Phase 3", "Optimization engine for multi-site allocation and routing", "road-part", "Preview available",
     "The Overview supply plan already shares limited volume by urgency and criticality; routing is next."),
    ("Phase 3", "Proof-of-delivery with digital meter/sensor evidence", "road-part", "Evidence notes captured",
     "Each delivery records a proof reference; automatic sensor confirmation is next."),
    ("Phase 4", "Multi-tenant facility management platform and enterprise controls", "road-plan", "Planned",
     "Role-based access and approvals are in place as the foundation."),
]


def render_roadmap() -> None:
    header("Roadmap", "Where AquaSwarm is going, and what already exists")
    rows = "".join(
        f'<tr><td><b>{esc(phase)}</b></td><td>{esc(item)}<br><span style="color:#8fb7c4;font-size:12px">{esc(note)}</span></td>'
        f'<td><span class="pill {cls}">{esc(status)}</span></td></tr>'
        for phase, item, cls, status, note in _ROADMAP
    )
    st.html(f'<div class="aq"><div class="card"><div class="tablescroll"><table class="sup">'
            f'<tr><th>Stage</th><th>Enhancement</th><th>Status</th></tr>{rows}</table></div></div></div>')