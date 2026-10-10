from __future__ import annotations

import streamlit as st

from backend import operations as ops  # clear-all maintenance only
from backend import users
from ui.pages import empty_state, header


def _optional_number(text: str, label: str):
    text = (text or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be a number.") from exc


# ---------------------------------------------------------------- data
def render_data(client, role: str) -> None:
    header("Data", "Your real sites, tanks and readings")
    can_manage = role in {"manager", "admin"}
    tanks = client.get_tanks()

    labels = ["Record readings"] + (["Sites & tanks"] if can_manage else []) + (["Sensors & maintenance"] if can_manage else [])
    tabs = st.tabs(labels)

    # ---- record readings (operators and above)
    with tabs[0]:
        if not tanks:
            empty_state("No tanks yet", "A manager needs to add a site and tank first." if not can_manage
                        else "Add a site and a tank in the next tab, then record readings here.")
        else:
            st.caption("Enter what you measured. Leave a field empty if you do not have it.")
            with st.form("record_reading", clear_on_submit=True):
                tank = st.selectbox("Tank", tanks, format_func=lambda t: f"{t['tank_code']} · {t['site_name']} · {t['name']}")
                c1, c2 = st.columns(2)
                level = c1.text_input("Tank level now (units)", placeholder=f"capacity {tank['capacity']:g}")
                used = c2.text_input("Water used in the last 24 h (units)")
                go = st.form_submit_button("Save reading", type="primary", use_container_width=True)
            if go:
                try:
                    updated = client.record_reading({
                        "tank_code": tank["tank_code"],
                        "current_level": _optional_number(level, "Tank level"),
                        "consumption": _optional_number(used, "Water used"),
                        "source": "MANUAL",
                    })
                    st.success(f"Saved. {updated['tank_code']} is now at {float(updated['current_level']):,.0f} units.")
                except Exception as exc:
                    st.error(str(exc))

    if not can_manage:
        return

    # ---- sites & tanks (managers)
    with tabs[1]:
        sites = client.get_sites()
        site_tab, tank_tab, profile_tab = st.tabs(["Add site", "Add tank", "Edit site profile"])
        with site_tab:
            with st.form("add_site", clear_on_submit=True):
                c1, c2 = st.columns(2)
                name = c1.text_input("Site name")
                location = c2.text_input("Location")
                manager = c1.text_input("Site manager (optional)")
                population = c2.number_input("People served", min_value=0, value=0, step=10)
                criticality = st.selectbox("Criticality", ["LOW", "MEDIUM", "HIGH", "CRITICAL"], index=1,
                                           format_func=str.title)
                go = st.form_submit_button("Add site", type="primary", use_container_width=True)
            if go:
                try:
                    client.create_site({"name": name, "location": location, "manager_name": manager,
                                        "population": int(population), "criticality": criticality})
                    st.success(f"{name} added.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with tank_tab:
            if not sites:
                st.info("Add a site first.")
            else:
                with st.form("add_tank", clear_on_submit=True):
                    site = st.selectbox("Site", sites, format_func=lambda s: s["name"])
                    c1, c2 = st.columns(2)
                    name = c1.text_input("Tank name", placeholder="Roof tank A")
                    code = c2.text_input("Tank code (optional)", placeholder="auto: TANK-001")
                    capacity = c1.number_input("Capacity (units)", min_value=0.0, value=0.0, step=500.0)
                    level = c2.number_input("Current level (units)", min_value=0.0, value=0.0, step=100.0)
                    threshold = st.slider("Critical level (% of capacity)", 0, 60, 20)
                    go = st.form_submit_button("Add tank", type="primary", use_container_width=True)
                if go:
                    try:
                        tank = client.create_tank({"site_id": site["id"], "name": name, "capacity": capacity,
                                                   "current_level": level, "critical_threshold": float(threshold),
                                                   "tank_code": code or None})
                        st.success(f"{tank['tank_code']} added.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
        with profile_tab:
            if not sites:
                st.info("No sites yet.")
            else:
                site = st.selectbox("Site to edit", sites, format_func=lambda s: s["name"], key="edit_site_pick")
                levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                with st.form(f"edit_site_{site['id']}"):
                    population = st.number_input("People served", min_value=0, value=int(site.get("population") or 0), step=10)
                    criticality = st.selectbox("Criticality", levels,
                                               index=levels.index(str(site.get("criticality") or "MEDIUM").upper()),
                                               format_func=str.title)
                    manager = st.text_input("Site manager", value=site.get("manager_name") or "")
                    go = st.form_submit_button("Save profile", type="primary", use_container_width=True)
                if go:
                    try:
                        client.update_site(site["id"], {"population": int(population), "criticality": criticality, "manager_name": manager})
                        st.success("Site profile updated.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    # ---- sensors & maintenance
    with tabs[2]:
        st.markdown("**Sensor telemetry**")
        st.caption("ESP32 or other sensors can post readings to the secured API (HTTP mode, with your API key):")
        st.code(
            'POST /readings\nX-API-Key: <your AQUASWARM_API_KEY>\n'
            '{"tank_code": "TANK-001", "current_level": 3600, "consumption": 2400, "source": "SENSOR"}',
            language="http",
        )
        if role == "admin":
            st.markdown("**Remove all operational data**")
            st.caption("Deletes sites, tanks, readings, suppliers, deliveries, alerts and the audit trail. "
                       "User accounts are kept. This cannot be undone.")
            with st.form("clear_data"):
                confirm = st.text_input("Type CLEAR to confirm")
                go = st.form_submit_button("Remove all operational data", use_container_width=True)
            if go:
                if confirm.strip() != "CLEAR":
                    st.error("Type CLEAR exactly to confirm.")
                else:
                    removed = ops.clear_operational_data()
                    st.session_state.workflow_state = None
                    st.success(f"Removed {sum(removed.values())} records.")
                    st.rerun()


# ---------------------------------------------------------------- team
def render_team(current_user: dict) -> None:
    header("Team access", "Approve requests, set roles and help people regain access")
    people = users.list_users()
    pending = [u for u in people if u["status"] == "PENDING"]
    resets = users.pending_resets()

    req_tab, people_tab, reset_tab = st.tabs([f"Requests ({len(pending)})", f"People ({len(people) - len(pending)})",
                                              f"Password resets ({len(resets)})"])
    with req_tab:
        if not pending:
            empty_state("No pending requests", "New access requests appear here for approval.")
        for person in pending:
            with st.container(border=True):
                st.markdown(f"**{person['full_name']}** · {person['email']}")
                st.caption(f"Requested {person['requested_role']} · {person['request_note'] or 'no note'}")
                role = st.selectbox("Role", list(users.ROLES), index=list(users.ROLES).index(person["requested_role"] or "operator"),
                                    key=f"role_{person['id']}")
                a, b = st.columns(2)
                if a.button("Approve", key=f"ok_{person['id']}", type="primary", use_container_width=True):
                    users.approve_user(person["id"], role)
                    st.rerun()
                if b.button("Decline", key=f"no_{person['id']}", use_container_width=True):
                    users.reject_request(person["id"])
                    st.rerun()
    with people_tab:
        for person in (u for u in people if u["status"] != "PENDING"):
            mine = person["id"] == current_user["id"]
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.2, 1.2, 1])
                c1.markdown(f"**{person['full_name']}**{' (you)' if mine else ''}  \n{person['email']}")
                new_role = c2.selectbox("Role", list(users.ROLES), index=list(users.ROLES).index(person["role"]),
                                        key=f"r_{person['id']}", disabled=mine, label_visibility="collapsed")
                active = person["status"] == "ACTIVE"
                if c3.button("Disable" if active else "Enable", key=f"s_{person['id']}", disabled=mine, use_container_width=True):
                    try:
                        users.set_status(person["id"], "DISABLED" if active else "ACTIVE")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                if new_role != person["role"] and not mine:
                    try:
                        users.set_role(person["id"], new_role)
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
    with reset_tab:
        if not resets:
            empty_state("No reset requests", "When someone asks to reset a password, it appears here.")
        for item in resets:
            with st.container(border=True):
                st.markdown(f"**{item['full_name']}** · {item['email']}")
                st.caption(f"Requested {item['requested_at'][:16].replace('T', ' ')} UTC")
                if st.button("Issue one-time code", key=f"code_{item['id']}", use_container_width=True):
                    code = users.issue_reset_code(item["id"])
                    st.session_state[f"issued_{item['id']}"] = code
                if f"issued_{item['id']}" in st.session_state:
                    st.code(st.session_state[f"issued_{item['id']}"])
                    st.caption("Give this code to the person directly. It works once and expires in 30 minutes.")