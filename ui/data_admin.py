from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd
import streamlit as st

from backend import notify, users
from ui.pages import empty_state, header


def _optional_number(text: str, label: str):
    text = (text or "").strip().replace(",", "")
    if not text:
        return None
    try:
        val = float(text)
        if val < 0:
            raise ValueError(f"{label} cannot be negative.")
        return val
    except ValueError as exc:
        if "cannot be negative" in str(exc):
            raise
        raise ValueError(f"{label} must be a valid number.") from exc


# ---------------------------------------------------------------- data
def render_data(client, role: str) -> None:
    header("Data", "Manage sites, tanks, readings, and sensor telemetry")
    can_manage = role in {"manager", "admin"}
    tanks = client.get_tanks()

    labels = ["Record readings"] + (["Sites & tanks"] if can_manage else []) + ["Sensors & telemetry"]
    tabs = st.tabs(labels)

    # ---- 1. Record readings (operators and above)
    with tabs[0]:
        if not tanks:
            empty_state(
                "No tanks available",
                "A manager must add a site and tank in the 'Sites & tanks' tab before you can record readings.",
            )
        else:
            st.caption("Record physical or dipstick water measurements. Leave a field blank if you do not have that reading.")

            # Selected tank
            selected_tank = st.selectbox(
                "Select Tank",
                tanks,
                format_func=lambda t: f"{t['tank_code']} · {t['site_name']} · {t['name']}",
                key="reading_tank_selector",
            )

            # Metadata Display Card for the selected tank
            curr_level = float(selected_tank.get("current_level", 0))
            cap = float(selected_tank.get("capacity", 1)) or 1.0
            crit_threshold = float(selected_tank.get("critical_threshold", 20))
            crit_units = cap * (crit_threshold / 100.0)
            fill_pct = min(max((curr_level / cap) * 100.0, 0.0), 100.0)

            st.markdown(
                f"""
                <div style="background:rgba(5,43,64,.85);border:1px solid rgba(120,225,240,.24);border-radius:14px;padding:16px 20px;margin:10px 0 16px;">
                  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                    <div>
                      <span style="color:#4de3f0;font-weight:800;font-size:16px;">{selected_tank['tank_code']}</span>
                      <span style="color:#8fb7c4;font-size:13px;margin-left:8px;">{selected_tank['site_name']} · {selected_tank['name']}</span>
                    </div>
                    <span style="font-size:12px;font-weight:700;color:#d6f7fb;background:rgba(77,227,240,.12);border:1px solid rgba(77,227,240,.3);padding:4px 10px;border-radius:99px;">
                      Fill: {fill_pct:.1f}%
                    </span>
                  </div>
                  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-top:14px;">
                    <div><span style="font-size:11px;color:#8fb7c4;text-transform:uppercase;">Current Level</span><br><b style="font-size:18px;color:#f6feff;">{curr_level:,.0f} units</b></div>
                    <div><span style="font-size:11px;color:#8fb7c4;text-transform:uppercase;">Tank Capacity</span><br><b style="font-size:18px;color:#f6feff;">{cap:,.0f} units</b></div>
                    <div><span style="font-size:11px;color:#8fb7c4;text-transform:uppercase;">Critical Reserve</span><br><b style="font-size:18px;color:{'#ff7b72' if curr_level <= crit_units else '#8ff5e0'};">{crit_threshold:.0f}% ({crit_units:,.0f} u)</b></div>
                    <div><span style="font-size:11px;color:#8fb7c4;text-transform:uppercase;">Site Criticality</span><br><b style="font-size:18px;color:#ffd27a;">{selected_tank.get('criticality', 'MEDIUM')}</b></div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("record_reading_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                level_str = c1.text_input(
                    "New water level (units)",
                    placeholder="e.g. 4500",
                    help=f"Must be between 0 and total tank capacity ({cap:g} units).",
                )
                used_str = c2.text_input(
                    "Water used in last 24h / Consumption (units)",
                    placeholder="e.g. 1200",
                    help="Non-negative water draw-off in units.",
                )
                go = st.form_submit_button("💾 Save Verified Reading", type="primary", use_container_width=True)

            if go:
                try:
                    parsed_level = _optional_number(level_str, "Water level")
                    parsed_used = _optional_number(used_str, "Water consumption")

                    if parsed_level is None and parsed_used is None:
                        st.error("Please provide at least one measurement: water level, 24h consumption, or both.")
                    else:
                        if parsed_level is not None and parsed_level > cap:
                            st.error(f"Water level cannot exceed tank capacity of {cap:g} units (entered: {parsed_level:g}).")
                        else:
                            updated = client.record_reading({
                                "tank_code": selected_tank["tank_code"],
                                "current_level": parsed_level,
                                "consumption": parsed_used,
                                "source": "OPERATOR",
                            })
                            new_lvl = float(updated.get("current_level", curr_level))
                            st.success(
                                f"✅ Reading recorded for {updated.get('tank_code', selected_tank['tank_code'])}. "
                                f"Current level updated to {new_lvl:,.0f} units ({new_lvl / cap * 100:.1f}% capacity)."
                            )
                            st.rerun()
                except Exception as exc:
                    st.error(f"Error saving reading: {exc}")

    if not can_manage and len(labels) == 2:
        return

    # ---- 2. Sites & tanks (managers)
    if can_manage:
        with tabs[1]:
            sites = client.get_sites()
            site_tab, tank_tab, profile_tab = st.tabs(["Add site", "Add tank", "Edit site profile"])

            with site_tab:
                with st.form("add_site", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    name = c1.text_input("Site name", placeholder="e.g. North Ridge Treatment Center")
                    location = c2.text_input("Location / City", placeholder="e.g. Sector 4, Islamabad")
                    manager = c1.text_input("Site manager name (optional)")
                    population = c2.number_input("People served / Population", min_value=0, value=0, step=50)
                    criticality = st.selectbox(
                        "Criticality Level",
                        ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                        index=1,
                        format_func=str.title,
                    )
                    go = st.form_submit_button("Add New Site", type="primary", use_container_width=True)

                if go:
                    if not (name or "").strip():
                        st.error("Site name is required.")
                    elif not (location or "").strip():
                        st.error("Location is required.")
                    else:
                        try:
                            client.create_site({
                                "name": name.strip(),
                                "location": location.strip(),
                                "manager_name": manager.strip() if manager else "",
                                "population": int(population),
                                "criticality": criticality,
                            })
                            st.success(f"Site '{name}' created successfully.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

            with tank_tab:
                if not sites:
                    st.info("You must add a site first before creating tanks.")
                else:
                    with st.form("add_tank", clear_on_submit=True):
                        site = st.selectbox("Belongs to Site", sites, format_func=lambda s: f"{s['name']} ({s['location']})")
                        c1, c2 = st.columns(2)
                        name = c1.text_input("Tank name / Label", placeholder="e.g. High-Pressure Tank A")
                        code = c2.text_input("Tank code (optional, e.g. TANK-006)", placeholder="Leave blank to auto-generate")
                        capacity = c1.number_input("Total Capacity (units)", min_value=1.0, value=10000.0, step=500.0)
                        level = c2.number_input("Initial Water Level (units)", min_value=0.0, value=5000.0, step=100.0)
                        threshold = st.slider("Critical Reserve Threshold (% of capacity)", min_value=5, max_value=60, value=20)
                        go = st.form_submit_button("Add Tank", type="primary", use_container_width=True)

                    if go:
                        if not (name or "").strip():
                            st.error("Tank name is required.")
                        elif level > capacity:
                            st.error("Initial level cannot exceed total tank capacity.")
                        else:
                            try:
                                created_tank = client.create_tank({
                                    "site_id": site["id"],
                                    "name": name.strip(),
                                    "capacity": float(capacity),
                                    "current_level": float(level),
                                    "critical_threshold": float(threshold),
                                    "tank_code": code.strip() if code else None,
                                })
                                st.success(f"Tank {created_tank['tank_code']} ('{name}') added to {site['name']}.")
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))

            with profile_tab:
                if not sites:
                    st.info("No sites available to edit.")
                else:
                    site = st.selectbox("Site to edit", sites, format_func=lambda s: s["name"], key="edit_site_pick")
                    levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                    curr_crit = str(site.get("criticality") or "MEDIUM").upper()
                    crit_idx = levels.index(curr_crit) if curr_crit in levels else 1

                    with st.form(f"edit_site_{site['id']}"):
                        population = st.number_input("People served", min_value=0, value=int(site.get("population") or 0), step=25)
                        criticality = st.selectbox("Criticality", levels, index=crit_idx, format_func=str.title)
                        manager = st.text_input("Site manager", value=site.get("manager_name") or "")
                        location = st.text_input("Location", value=site.get("location") or "")
                        go = st.form_submit_button("Update Site Profile", type="primary", use_container_width=True)

                    if go:
                        try:
                            client.update_site(site["id"], {
                                "population": int(population),
                                "criticality": criticality,
                                "manager_name": manager,
                                "location": location,
                            })
                            st.success(f"Profile for '{site['name']}' updated.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

    # ---- 3. Sensors & telemetry (active monitoring + simulator console)
    sensor_tab_idx = 2 if can_manage else 1
    with tabs[sensor_tab_idx]:
        st.markdown("### 📡 Sensor Telemetry & Connectivity Console")
        st.caption(
            "Live status of automated IoT/ESP32 water telemetry, secured ingestion endpoint, and interactive testing tools. "
            "Sensors connect directly to the `/readings` API using authenticated tokens."
        )

        # Telemetry Status Table
        consumption_rows = client.get_consumption(limit=500)
        latest_readings: dict[str, dict] = {}
        for row in consumption_rows:
            tc = row.get("tank_code")
            if tc and tc not in latest_readings:
                latest_readings[tc] = row

        status_records = []
        now_utc = datetime.now(timezone.utc)

        for t in tanks:
            tcode = t["tank_code"]
            latest = latest_readings.get(tcode)
            last_source = (latest.get("source") if latest else "NONE") or "NONE"
            last_time = (latest.get("timestamp") if latest else t.get("updated_at")) or "—"

            # Determine connectivity status
            is_recent = False
            if last_time and last_time != "—":
                try:
                    moment = datetime.fromisoformat(str(last_time).replace("Z", "+00:00"))
                    if moment.tzinfo is None:
                        moment = moment.replace(tzinfo=timezone.utc)
                    age_hours = (now_utc - moment).total_seconds() / 3600.0
                    is_recent = age_hours <= 24.0
                except Exception:
                    pass

            if last_source in ("SENSOR", "SIMULATOR") and is_recent:
                state_label = "🟢 Connected (Live Telemetry)"
            elif last_source in ("SENSOR", "SIMULATOR"):
                state_label = "🟡 Configured (Signal > 24h ago)"
            else:
                state_label = "⚪ Awaiting Hardware Telemetry"

            status_records.append({
                "Tank Code": tcode,
                "Site": t["site_name"],
                "Connectivity Status": state_label,
                "Last Source": last_source,
                "Last Signal (UTC)": last_time[:19].replace("T", " ") if last_time != "—" else "—",
                "Current Level": f"{float(t['current_level']):,.0f} / {float(t['capacity']):,.0f} u",
            })

        if status_records:
            st.dataframe(pd.DataFrame(status_records), hide_index=True, use_container_width=True)

        st.markdown("---")

        # Interactive Telemetry Simulator & API Testing
        sim_col, doc_col = st.columns([1.1, 0.9], gap="large")

        with sim_col:
            st.markdown("#### 🧪 Telemetry Simulator & Ingestion Test")
            st.caption("Inject authenticated sensor readings into the database to verify the end-to-end pipeline without physical ESP32 hardware.")

            if tanks:
                sim_tank = st.selectbox(
                    "Target Tank for Simulation",
                    tanks,
                    format_func=lambda t: f"{t['tank_code']} · {t['name']} (Cap: {float(t['capacity']):,.0f})",
                    key="sim_tank_select",
                )
                sim_cap = float(sim_tank["capacity"])

                with st.form("sensor_simulator_form"):
                    sim_c1, sim_c2 = st.columns(2)
                    sim_level = sim_c1.number_input(
                        "Simulated Level (units)",
                        min_value=0.0,
                        max_value=sim_cap,
                        value=round(sim_cap * 0.45, 1),
                        step=100.0,
                    )
                    sim_flow = sim_c2.number_input(
                        "Simulated Flow / 24h Drawoff (units)",
                        min_value=0.0,
                        value=round(sim_cap * 0.15, 1),
                        step=50.0,
                    )
                    sim_source = st.selectbox("Telemetry Source Tag", ["SENSOR", "SIMULATOR", "METER"], index=0)
                    sim_go = st.form_submit_button("⚡ Transmit Ingestion Telemetry", type="primary", use_container_width=True)

                if sim_go:
                    try:
                        res = client.record_reading({
                            "tank_code": sim_tank["tank_code"],
                            "current_level": float(sim_level),
                            "consumption": float(sim_flow),
                            "source": sim_source,
                        })
                        st.success(
                            f"📡 Ingestion Received: {res.get('tank_code')} level recorded at {float(res.get('current_level', sim_level)):,.0f} units "
                            f"(Source: {sim_source}, Time: UTC {res.get('timestamp', '')[:19]})."
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Ingestion rejected: {exc}")

        with doc_col:
            st.markdown("#### ⚙️ Hardware Telemetry")
            st.markdown(
                "Sensors continuously transmit liquid volume and consumption increments using authenticated HTTP POST endpoints."
            )
            st.info(
                "📖 **Dedicated Integration Portal**\n\n"
                "Detailed GPIO wiring schematics, ESP32 / Raspberry Pi Pico W firmware templates, "
                "and device-reachable endpoint configuration are available in the **Hardware & Sensors** page in the sidebar menu."
            )

            with st.expander("🛠️ Developer Quick-Reference: Ingestion API"):
                st.markdown(
                    """
                    **Ingestion Endpoint**: `POST /readings`  
                    **Host**: `127.0.0.1:8000` *(Local testing address — physical Wi-Fi devices require your host's reachable LAN IP)*  
                    **Header**: `X-API-Key: <AQUASWARM_API_KEY>`

                    ```http
                    POST /readings HTTP/1.1
                    Host: 127.0.0.1:8000
                    Content-Type: application/json
                    X-API-Key: <AQUASWARM_API_KEY>

                    {
                      "tank_code": "TANK-001",
                      "current_level": 3600.0,
                      "consumption": 1200.0,
                      "source": "SENSOR"
                    }
                    ```

                    **Supported Hardware Summary**:
                    - **ESP32**: JSN-SR04T Ultrasonic (Trig: GPIO 5, Echo: GPIO 18 via voltage divider) • YF-S201 Flow (Pulse: GPIO 19 with 4.7kΩ pull-up)
                    - **Raspberry Pi Pico W**: JSN-SR04T Ultrasonic (Trig: GP3, Echo: GP2 via voltage divider) • YF-S201 Flow (Pulse: GP4 with pull-up)
                    """
                )

        # System Notification Diagnostics
        st.markdown("---")
        st.markdown("#### 🔔 System Notifications & Alert Channels")
        notif_status = notify.get_notification_status()

        nc1, nc2, nc3 = st.columns(3)
        with nc1:
            st.metric("E-mail (SMTP)", "Configured" if notif_status["email_ready"] else "Not Configured")
            st.caption(f"Host: {notif_status['email_host']}")
        with nc2:
            st.metric("WhatsApp Provider", notif_status["whatsapp_provider"])
            st.caption("Twilio or Meta Cloud API")
        with nc3:
            st.metric("Active Channels", len(notif_status["active_channels"]))
            st.caption(", ".join(notif_status["active_channels"]) or "None active")

        with st.expander("Send Test Notification"):
            with st.form("test_notification_form"):
                n_chan = st.selectbox("Channel", ["Email", "WhatsApp"], index=0)
                n_recipient = st.text_input("Recipient (Email address or phone number with country code)", placeholder="admin@example.com or +1234567890")
                n_go = st.form_submit_button("Send Test Message", use_container_width=True)

            if n_go:
                if not (n_recipient or "").strip():
                    st.error("Please enter a recipient.")
                else:
                    res = notify.test_notification(n_chan.lower(), n_recipient.strip())
                    if res.get("success"):
                        st.success(res.get("message", "Test notification dispatched."))
                    else:
                        st.warning(f"Notification status: {res.get('error', 'Could not deliver test notification.')}")


# ---------------------------------------------------------------- team
def render_team(current_user: dict) -> None:
    header("Team access", "Approve requests, set roles and help people regain access")
    people = users.list_users()
    pending = [u for u in people if u["status"] == "PENDING"]
    resets = users.pending_resets()

    req_tab, people_tab, reset_tab = st.tabs([
        f"Requests ({len(pending)})",
        f"People ({len(people) - len(pending)})",
        f"Password resets ({len(resets)})",
    ])
    with req_tab:
        if not pending:
            empty_state("No pending requests", "New access requests appear here for approval.")
        for person in pending:
            with st.container(border=True):
                st.markdown(f"**{person['full_name']}** · {person['email']}")
                st.caption(f"Requested {person['requested_role']} · {person['request_note'] or 'no note'}")
                role = st.selectbox(
                    "Role",
                    list(users.ROLES),
                    index=list(users.ROLES).index(person["requested_role"] or "operator"),
                    key=f"role_{person['id']}",
                )
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
                new_role = c2.selectbox(
                    "Role",
                    list(users.ROLES),
                    index=list(users.ROLES).index(person["role"]),
                    key=f"r_{person['id']}",
                    disabled=mine,
                    label_visibility="collapsed",
                )
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