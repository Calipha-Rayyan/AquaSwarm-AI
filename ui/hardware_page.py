"""Hardware & Sensor Integration Module for AquaSwarm AI.

Provides comprehensive IoT device integration documentation, microcontroller wiring
diagrams (ESP32 & Raspberry Pi Pico W), telemetry API specifications, firmware templates,
and live hardware diagnostics.
"""
from __future__ import annotations

import socket
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

from ui.dashboard import _compact, esc
from ui.pages import header


def get_local_ip() -> str:
    """Best-effort discovery of local LAN IP address for microcontroller connectivity."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.1.6"


def render_hardware_integration(client: Any, role: str) -> None:
    """Render the dedicated Hardware & Sensor Integration portal."""
    header(
        "Hardware & Sensor Integration",
        "Microcontroller wiring, IoT telemetry endpoints, and live ingestion monitoring",
    )

    # ----------------------------------------------------------------------
    # 1. Truthful Implementation Status Disclaimer
    # ----------------------------------------------------------------------
    st.markdown(
        """
        <div style="background:rgba(20,45,65,0.75); border:1px solid rgba(77,227,240,0.3); border-radius:10px; padding:18px 22px; margin-bottom:20px;">
          <div style="color:#8ff5e0; font-weight:700; font-size:16px; margin-bottom:8px;">
            🔍 Hardware Integration & Implementation Status
          </div>
          <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:12px; margin-top:10px;">
            <div style="background:rgba(10,25,38,0.65); padding:12px 14px; border-radius:6px; border-left:3px solid #8ff5e0;">
              <b style="color:#8ff5e0;">✅ REST Ingestion API</b><br>
              <span style="font-size:12px; color:#c7eaf2;">Fully implemented (<code>POST /readings</code>), secured via <code>X-API-Key</code>, validated against tank bounds, and verified by automated tests.</span>
            </div>
            <div style="background:rgba(10,25,38,0.65); padding:12px 14px; border-radius:6px; border-left:3px solid #4de3f0;">
              <b style="color:#4de3f0;">✅ Software Simulator</b><br>
              <span style="font-size:12px; color:#c7eaf2;">Fully operational in-app simulation testbench to inject telemetry packets and verify database updates without hardware.</span>
            </div>
            <div style="background:rgba(10,25,38,0.65); padding:12px 14px; border-radius:6px; border-left:3px solid #ffd27a;">
              <b style="color:#ffd27a;">📋 Hardware Architecture</b><br>
              <span style="font-size:12px; color:#c7eaf2;">Documented pinouts, circuit schematics (voltage divider & pull-up), and firmware templates for ESP32 and Raspberry Pi Pico W.</span>
            </div>
            <div style="background:rgba(10,25,38,0.65); padding:12px 14px; border-radius:6px; border-left:3px solid #ff7b72;">
              <b style="color:#ff7b72;">⏳ Physical Bench Testing</b><br>
              <span style="font-size:12px; color:#c7eaf2;">Pending physical connection. Microcontroller boards and physical sensors have not yet been connected or bench-tested on live tanks.</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------------------
    # 2. Configurable Reachable Backend URL
    # ----------------------------------------------------------------------
    local_ip = get_local_ip()
    st.markdown("### 🌐 Device-Reachable Backend URL Configuration")
    st.caption(
        "Real microcontrollers (ESP32 / Pico W) cannot reach <code>127.0.0.1</code> because loopback resolves to the microcontroller itself. "
        "Select or configure the IP address that physical devices will use to post telemetry.",
        unsafe_allow_html=True,
    )

    url_col1, url_col2 = st.columns([1.2, 1.8], gap="medium")
    with url_col1:
        endpoint_preset = st.radio(
            "Select Target Network Environment",
            [
                f"📶 Local LAN Endpoint (http://{local_ip}:8000)",
                "💻 Local Loopback (http://127.0.0.1:8000)",
                "🌐 Custom Hostname / Domain",
            ],
            index=0,
            key="hw_endpoint_preset",
        )

    with url_col2:
        if "Local LAN" in endpoint_preset:
            configured_url = f"http://{local_ip}:8000"
            st.info(
                f"**Reachable on Local Wi-Fi**: Microcontrollers connected to the same Wi-Fi network will transmit HTTP POST requests to: **`{configured_url}`**.\n\n"
                f"*Requirement*: The backend service must be running with `--host 0.0.0.0 --port 8000` and the host firewall must permit inbound port 8000 connections."
            )
        elif "Local Loopback" in endpoint_preset:
            configured_url = "http://127.0.0.1:8000"
            st.warning(
                "**Local Machine Only (Host Loopback)**: `127.0.0.1:8000` only resolves from inside this host computer (e.g. curl or Python scripts). "
                "Physical ESP32 / Pico W microcontrollers cannot reach this address over Wi-Fi."
            )
        else:
            custom_input = st.text_input(
                "Custom Backend Endpoint",
                value=f"http://{local_ip}:8000",
                placeholder="https://api.aquaswarm.io or http://192.168.1.100:8000",
                key="hw_custom_url_input",
            )
            configured_url = (custom_input or f"http://{local_ip}:8000").rstrip("/")

    # Strip protocol for host header display
    host_header = configured_url.replace("http://", "").replace("https://", "")

    st.markdown("---")

    # ----------------------------------------------------------------------
    # 3. Main Integration Sections (Tabs)
    # ----------------------------------------------------------------------
    tab_api, tab_wiring, tab_code, tab_diag = st.tabs([
        "📡 REST Telemetry API",
        "🔌 Microcontroller & Pinouts",
        "💻 Device Firmware Snippets",
        "🧪 Live Telemetry & Testing",
    ])

    # ======================================================================
    # TAB 1: REST Telemetry API
    # ======================================================================
    with tab_api:
        st.markdown("#### 📡 Sensor Ingestion API (`POST /readings`)")
        st.write(
            "Physical microcontrollers and pulse meters post telemetry payloads over HTTP. "
            "All requests are validated against tank capacity and secured via API key headers."
        )

        st.markdown(
            f"""
            ```http
            POST /readings HTTP/1.1
            Host: {host_header}
            Content-Type: application/json
            X-API-Key: <AQUASWARM_API_KEY>

            {{
              "tank_code": "TANK-001",
              "current_level": 3600.0,
              "consumption": 1200.0,
              "source": "SENSOR"
            }}
            ```
            """
        )

        st.markdown("##### Payload Field Reference")
        schema_data = [
            {"Field": "tank_code", "Type": "string", "Required": "Yes", "Description": "Unique facility tank code (e.g. 'TANK-001'). Checked against database."},
            {"Field": "current_level", "Type": "float", "Required": "Optional*", "Description": "Instantaneous liquid volume (units/liters). Must be 0 ≤ level ≤ capacity."},
            {"Field": "consumption", "Type": "float", "Required": "Optional*", "Description": "Volume drawn off over the measurement period. Must be ≥ 0."},
            {"Field": "source", "Type": "string", "Required": "No", "Description": "Telemetry origin tag: 'SENSOR', 'SIMULATOR', 'METER', or 'OPERATOR'. Default: 'SENSOR'."},
            {"Field": "timestamp", "Type": "string", "Required": "No", "Description": "ISO-8601 UTC timestamp. Defaults to server receipt time if omitted."},
        ]
        st.dataframe(pd.DataFrame(schema_data), hide_index=True, use_container_width=True)
        st.caption("*At least one measurement (`current_level` or `consumption`) must be provided.")

        st.markdown("##### Security & Response Codes")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                """
                - **Header Authentication**: Must pass `X-API-Key: <AQUASWARM_API_KEY>` matching server configuration.
                - **Constant-Time Verification**: Server uses HMAC constant-time comparison to prevent timing attacks.
                - **CORS Restricted**: Browser cross-origin requests restricted to configured frontend origins.
                """
            )
        with c2:
            st.markdown(
                """
                - **`200 OK`**: Reading validated and stored. Returns updated fill percentage.
                - **`400 Bad Request`**: Level exceeds capacity or negative consumption.
                - **`401 Unauthorized`**: Missing or invalid `X-API-Key`.
                - **`404 Not Found`**: Specified `tank_code` does not exist.
                """
            )

        st.markdown("##### Quick Command Line Testing")
        c_curl, c_ps = st.columns(2)
        with c_curl:
            st.caption("Linux / macOS / Git Bash:")
            st.code(
                f"""curl -X POST "{configured_url}/readings" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: <AQUASWARM_API_KEY>" \\
  -d '{{"tank_code": "TANK-001", "current_level": 3600.0, "consumption": 1200.0, "source": "SENSOR"}}'""",
                language="bash",
            )
        with c_ps:
            st.caption("Windows PowerShell:")
            st.code(
                f"""$headers = @{{
  "Content-Type" = "application/json"
  "X-API-Key"    = "<AQUASWARM_API_KEY>"
}}
$body = @{{
  tank_code     = "TANK-001"
  current_level = 3600.0
  consumption   = 1200.0
  source        = "SENSOR"
}} | ConvertTo-Json

Invoke-RestMethod -Uri "{configured_url}/readings" -Method Post -Headers $headers -Body $body""",
                language="powershell",
            )

    # ======================================================================
    # TAB 2: Microcontroller & Pinouts
    # ======================================================================
    with tab_wiring:
        st.markdown("#### 🔌 Supported Microcontrollers & Sensor Wiring")

        esp_col, pico_col = st.columns(2, gap="large")

        with esp_col:
            st.markdown(
                """
                <div style="background:rgba(18,40,58,0.7); border:1px solid rgba(77,227,240,0.25); border-radius:8px; padding:16px;">
                  <h4 style="color:#4de3f0; margin-top:0;">ESP32 (NodeMCU / WROOM-32)</h4>
                  <p style="font-size:13px; color:#c7eaf2;">Recommended for outdoor enclosures and standard Wi-Fi facilities.</p>
                  <table style="width:100%; font-size:12px; color:#e0f7fa;">
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.1);"><th align="left">Sensor</th><th align="left">Sensor Pin</th><th align="left">ESP32 Pin</th></tr>
                    <tr><td><b>JSN-SR04T</b> (Ultrasonic)</td><td>VCC</td><td>5V (VIN)</td></tr>
                    <tr><td></td><td>GND</td><td>GND</td></tr>
                    <tr><td></td><td>TRIG</td><td>GPIO 5 (Output)</td></tr>
                    <tr><td></td><td>ECHO</td><td>GPIO 18 (Input)*</td></tr>
                    <tr style="border-top:1px solid rgba(255,255,255,0.1);"><td><b>YF-S201</b> (Flow Meter)</td><td>Red (VCC)</td><td>5V (VIN)</td></tr>
                    <tr><td></td><td>Black (GND)</td><td>GND</td></tr>
                    <tr><td></td><td>Yellow (Pulse)</td><td>GPIO 19 (Input)**</td></tr>
                  </table>
                  <p style="font-size:11px; color:#ffd27a; margin-top:10px;">
                    * <i>Note</i>: JSN-SR04T Echo is 5V. Use a 1kΩ / 2kΩ voltage divider to step down to 3.3V.<br>
                    ** <i>Note</i>: Place a 4.7kΩ pull-up resistor between 3.3V and the yellow pulse signal.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with pico_col:
            st.markdown(
                """
                <div style="background:rgba(18,40,58,0.7); border:1px solid rgba(143,245,224,0.25); border-radius:8px; padding:16px;">
                  <h4 style="color:#8ff5e0; margin-top:0;">Raspberry Pi Pico W (RP2040)</h4>
                  <p style="font-size:13px; color:#c7eaf2;">Low-power MicroPython solution with on-board CYW43439 Wi-Fi.</p>
                  <table style="width:100%; font-size:12px; color:#e0f7fa;">
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.1);"><th align="left">Sensor</th><th align="left">Sensor Pin</th><th align="left">Pico W Pin</th></tr>
                    <tr><td><b>JSN-SR04T</b> (Ultrasonic)</td><td>VCC</td><td>VBUS (Pin 40, 5V)</td></tr>
                    <tr><td></td><td>GND</td><td>GND (Pin 38)</td></tr>
                    <tr><td></td><td>TRIG</td><td>GP3 (Pin 5, Output)</td></tr>
                    <tr><td></td><td>ECHO</td><td>GP2 (Pin 4, Input)*</td></tr>
                    <tr style="border-top:1px solid rgba(255,255,255,0.1);"><td><b>YF-S201</b> (Flow Meter)</td><td>Red (VCC)</td><td>VBUS (5V)</td></tr>
                    <tr><td></td><td>Black (GND)</td><td>GND</td></tr>
                    <tr><td></td><td>Yellow (Pulse)</td><td>GP4 (Pin 6, Input)**</td></tr>
                  </table>
                  <p style="font-size:11px; color:#ffd27a; margin-top:10px;">
                    * <i>Note</i>: Always step down Echo signal from 5V to 3.3V using two resistors.<br>
                    ** <i>Note</i>: Enable internal pull-up in MicroPython: <code>Pin(4, Pin.IN, Pin.PULL_UP)</code>.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("##### Sensor Physics & Calibration Formulas")
        cal1, cal2 = st.columns(2)
        with cal1:
            st.markdown(
                """
                **Water Level Calibration (JSN-SR04T)**
                - **Distance to Water**: $d = \\frac{t_{\\text{echo}} \\times 0.0343}{2}$ cm
                - **Current Liquid Height**: $h = \\text{Total Tank Height} - d$
                - **Current Volume**: $V = h \\times \\text{Cross-Sectional Area}$
                - **Blind Zone**: Minimum measuring distance is 20 cm. Mount the transducer with at least 20 cm clearance above max overflow level.
                """
            )
        with cal2:
            st.markdown(
                """
                **Flow Drawoff Calibration (YF-S201)**
                - **Pulse Characteristic**: 450 pulses per liter (nominal).
                - **Instantaneous Flow Rate**: $Q = \\frac{F}{7.5}$ L/min (where $F$ is pulse frequency in Hz).
                - **Accumulated Consumption**: $\\Delta V = \\frac{\\text{Total Pulses}}{450}$ liters.
                - **Working Pressure**: $\\le 1.75\\text{ MPa}$.
                """
            )

    # ======================================================================
    # TAB 3: Device Firmware Snippets
    # ======================================================================
    with tab_code:
        st.markdown("#### 💻 Ready-to-Flash Device Firmware")
        st.caption(
            f"The templates below automatically incorporate the currently configured endpoint: **`{configured_url}/readings`**."
        )

        fw_type = st.radio("Choose Microcontroller Platform", ["ESP32 (C++ / Arduino IDE)", "Raspberry Pi Pico W (MicroPython)"], horizontal=True)

        if "ESP32" in fw_type:
            st.code(
                f"""// AquaSwarm AI — ESP32 Telemetry Firmware (Arduino IDE / PlatformIO)
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* WIFI_SSID     = "<WIFI_SSID>";
const char* WIFI_PASSWORD = "<WIFI_PASSWORD>";
const char* API_URL       = "{configured_url}/readings";
const char* API_KEY       = "<AQUASWARM_API_KEY>"; // Replace with your secure key
const char* TANK_CODE     = "TANK-001";

// Pinout
const int TRIG_PIN  = 5;
const int ECHO_PIN  = 18;
const int FLOW_PIN  = 19;

const float TANK_TOTAL_DEPTH_CM = 300.0; // Facility tank dimensions
const float TANK_CAPACITY_UNITS = 10000.0;
volatile unsigned long pulseCount = 0;

void IRAM_ATTR pulseCounter() {{
  pulseCount++;
}}

void setup() {{
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(FLOW_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(FLOW_PIN), pulseCounter, FALLING);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {{
    delay(500);
    Serial.print(".");
  }}
  Serial.println("\\nWiFi Connected!");
}}

float measureDistanceCm() {{
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH, 35000);
  if (duration == 0) return -1.0;
  return (duration * 0.0343) / 2.0;
}}

void loop() {{
  if (WiFi.status() == WL_CONNECTED) {{
    float distance = measureDistanceCm();
    float currentLevel = 0.0;
    if (distance > 0 && distance <= TANK_TOTAL_DEPTH_CM) {{
      float waterDepth = TANK_TOTAL_DEPTH_CM - distance;
      currentLevel = (waterDepth / TANK_TOTAL_DEPTH_CM) * TANK_CAPACITY_UNITS;
    }}

    // Flow consumption calculation (450 pulses = 1 liter)
    float consumptionUnits = pulseCount / 450.0;
    pulseCount = 0; // Reset counter for next window

    HTTPClient http;
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", API_KEY);

    StaticJsonDocument<200> doc;
    doc["tank_code"]     = TANK_CODE;
    doc["current_level"] = round(currentLevel * 10) / 10.0;
    doc["consumption"]   = round(consumptionUnits * 10) / 10.0;
    doc["source"]        = "SENSOR";

    String requestBody;
    serializeJson(doc, requestBody);

    int httpCode = http.POST(requestBody);
    Serial.printf("Ingestion status: %d\\n", httpCode);
    http.end();
  }}
  delay(60000); // Sample & transmit every 60 seconds
}}""",
                language="cpp",
            )
        else:
            st.code(
                f"""# AquaSwarm AI — Raspberry Pi Pico W Telemetry Firmware (MicroPython)
import network
import urequests
import ujson
import time
from machine import Pin, time_pulse_us

WIFI_SSID     = "<WIFI_SSID>"
WIFI_PASSWORD = "<WIFI_PASSWORD>"
API_URL       = "{configured_url}/readings"
API_KEY       = "<AQUASWARM_API_KEY>"
TANK_CODE     = "TANK-001"

TRIG_PIN = Pin(3, Pin.OUT)
ECHO_PIN = Pin(2, Pin.IN)
FLOW_PIN = Pin(4, Pin.IN, Pin.PULL_UP)

TANK_DEPTH_CM = 300.0
TANK_CAPACITY = 10000.0
pulses = 0

def on_pulse(pin):
    global pulses
    pulses += 1

FLOW_PIN.irq(trigger=Pin.IRQ_FALLING, handler=on_pulse)

# Connect Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)
while not wlan.isconnected():
    time.sleep(0.5)

print("Wi-Fi Connected:", wlan.ifconfig())

def measure_distance():
    TRIG_PIN.low()
    time.sleep_us(2)
    TRIG_PIN.high()
    time.sleep_us(10)
    TRIG_PIN.low()
    pulse_time = time_pulse_us(ECHO_PIN, 1, 30000)
    if pulse_time < 0:
        return None
    return (pulse_time * 0.0343) / 2.0

while True:
    dist = measure_distance()
    current_level = 0.0
    if dist is not None and dist <= TANK_DEPTH_CM:
        water_height = TANK_DEPTH_CM - dist
        current_level = (water_height / TANK_DEPTH_CM) * TANK_CAPACITY

    consumption = pulses / 450.0
    pulses = 0

    headers = {{
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
    }}
    payload = {{
        "tank_code": TANK_CODE,
        "current_level": round(current_level, 1),
        "consumption": round(consumption, 1),
        "source": "SENSOR",
    }}

    try:
        res = urequests.post(API_URL, headers=headers, data=ujson.dumps(payload))
        print("Telemetry sent. Status:", res.status_code)
        res.close()
    except Exception as e:
        print("Ingestion failed:", e)

    time.sleep(60)""",
                language="python",
            )

    # ======================================================================
    # TAB 4: Live Telemetry & Testing Console
    # ======================================================================
    with tab_diag:
        st.markdown("#### 🧪 Live Hardware Connectivity & Simulation Console")
        st.write(
            "Inspect signals received from field hardware and test transmission without physical microcontrollers."
        )

        tanks = client.get_tanks() or []
        if not tanks:
            st.info("ℹ️ No tanks found in the database. Please configure sites and tanks first in the Data section.")
            return

        # Fetch latest readings using supported BackendClient methods with fallback
        try:
            latest_readings_list = client.get_latest_readings()
        except (AttributeError, Exception):
            try:
                consumption_rows = client.get_consumption(limit=500) or []
                latest_readings_list = []
                seen = set()
                for row in consumption_rows:
                    tc = row.get("tank_code")
                    if tc and tc not in seen:
                        seen.add(tc)
                        latest_readings_list.append(row)
            except Exception:
                latest_readings_list = []

        latest_readings = {r["tank_code"]: r for r in (latest_readings_list or []) if r.get("tank_code")}
        now_utc = datetime.now(timezone.utc)

        # Truthful empty-state message if no hardware telemetry recorded
        has_hardware_telemetry = any(
            latest_readings.get(t["tank_code"]) and latest_readings[t["tank_code"]].get("source") in ("SENSOR", "SIMULATOR", "METER")
            for t in tanks
        )

        if not has_hardware_telemetry:
            st.info(
                "📡 **Hardware Telemetry Status: Awaiting Ingestion**\n\n"
                "No live sensor telemetry has been recorded yet for the configured tanks. "
                "Physical ESP32 / Pico W devices have not yet been connected to the live `/readings` endpoint.\n\n"
                "Use the **Ingestion Telemetry Simulator** below to inject authenticated test packets into SQLite and verify the end-to-end pipeline."
            )

        status_records = []
        for t in tanks:
            tcode = t["tank_code"]
            latest = latest_readings.get(tcode)
            last_source = (latest.get("source") if latest else "NONE") or "NONE"
            last_time = (latest.get("timestamp") if latest else t.get("updated_at")) or "—"

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
                "Current Volume": f"{float(t['current_level']):,.0f} / {float(t['capacity']):,.0f} u",
            })

        if status_records:
            st.dataframe(pd.DataFrame(status_records), hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown("##### ⚡ Ingestion Telemetry Simulator")
        st.caption("Transmit a mock sensor packet directly to the database to verify the ingestion pipeline.")

        if tanks:
            sim_tank = st.selectbox(
                "Select Tank to Transmit Data To",
                tanks,
                format_func=lambda t: f"{t['tank_code']} · {t['name']} (Cap: {float(t['capacity']):,.0f})",
                key="hw_diag_sim_tank",
            )
            sim_cap = float(sim_tank["capacity"])

            with st.form("hw_diag_sim_form"):
                sc1, sc2, sc3 = st.columns(3)
                sim_level = sc1.number_input(
                    "Simulated Water Level (units)",
                    min_value=0.0,
                    max_value=sim_cap,
                    value=round(sim_cap * 0.45, 1),
                    step=100.0,
                )
                sim_flow = sc2.number_input(
                    "Simulated Consumption / Drawoff (units)",
                    min_value=0.0,
                    value=round(sim_cap * 0.15, 1),
                    step=50.0,
                )
                sim_src = sc3.selectbox("Telemetry Tag", ["SENSOR", "SIMULATOR", "METER"], index=0)
                sim_btn = st.form_submit_button("🚀 Transmit Test Telemetry", type="primary", use_container_width=True)

            if sim_btn:
                try:
                    res = client.record_reading({
                        "tank_code": sim_tank["tank_code"],
                        "current_level": float(sim_level),
                        "consumption": float(sim_flow),
                        "source": sim_src,
                    })
                    st.success(
                        f"✅ Ingestion Successful: {res.get('tank_code')} recorded at {float(res.get('current_level', sim_level)):,.0f} units "
                        f"(Tag: {sim_src}, Timestamp: UTC {res.get('timestamp', '')[:19]})."
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Transmission rejected: {exc}")
