from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from agents.registry import (
    SWARM_AGENTS,
    OPERATIONAL_AGENTS,
    get_agent_spec,
    get_configured_agent_count,
    get_active_agents_from_state,
)
from backend.api import app
from backend import operations as ops
from backend.notify import get_notification_status, test_notification as send_test_notification
from tools.water_tools import evaluate_forecasting_readiness, plan_allocation_with_routing
from ui.auth_pages import validate_password_strength
from workflows.aquaswarm_flow import AquaSwarmState


def _get_api_headers() -> dict[str, str]:
    """Helper returning valid API key headers based on current configuration."""
    from backend.security import configured_api_key
    key = configured_api_key() or "aquaswarm-local-dev-key"
    return {"X-API-Key": key}


# ---------------------------------------------------------------------------
# 1. Authoritative Agent Registry Tests
# ---------------------------------------------------------------------------

def test_agent_registry_count_and_roles():
    """Verify that exactly 8 operational AI agents are configured in the authoritative registry."""
    assert get_configured_agent_count() == 8
    expected_agents = [
        "Demand Agent",
        "Anomaly Agent",
        "Supply Agent",
        "Allocation Agent",
        "Approval Review Agent",
        "Delivery Agent",
        "Verification Agent",
        "Replanning Agent",
    ]
    assert list(OPERATIONAL_AGENTS.keys()) == expected_agents

    for name in expected_agents:
        spec = get_agent_spec(name)
        assert spec is not None
        assert spec.role_description
        assert spec.stage
        assert spec.module_path


def test_active_agents_lifecycle():
    """Active agents in a run are derived deterministically from workflow state."""
    state = AquaSwarmState(selected_tank_id="TANK-001")
    # Initial state with no agents complete
    active = get_active_agents_from_state(state)
    assert len(active) == 0

    # Simulate demand and anomaly execution
    state.ai_agents.append("Demand Agent")
    state.ai_agents.append("Anomaly Agent")
    active = get_active_agents_from_state(state)
    assert "Demand Agent" in active
    assert "Anomaly Agent" in active
    assert len(active) == 2

    # Replanning is conditional: not in active list if replanning was not triggered
    assert "Replanning Agent" not in active
    state.ai_agents.append("Replanning Agent")
    active_after_replan = get_active_agents_from_state(state)
    assert "Replanning Agent" in active_after_replan
    assert len(active_after_replan) == 3


# ---------------------------------------------------------------------------
# 2. Reading Ingestion API Tests (POST /readings)
# ---------------------------------------------------------------------------

def test_readings_api_security():
    """POST /readings requires a valid X-API-Key when API key protection is active."""
    test_client = TestClient(app)
    payload = {
        "tank_code": "TANK-001",
        "current_level": 8500.0,
        "consumption": 150.0,
        "source": "esp32-sensor",
    }

    old_key = os.environ.get("AQUASWARM_API_KEY")
    try:
        os.environ["AQUASWARM_API_KEY"] = "secret-test-key-xyz"

        # Missing API key
        res_no_key = test_client.post("/readings", json=payload)
        assert res_no_key.status_code == 401

        # Invalid API key
        res_bad_key = test_client.post(
            "/readings",
            json=payload,
            headers={"X-API-Key": "wrong-key"},
        )
        assert res_bad_key.status_code == 401

        # Valid API key
        res_ok = test_client.post(
            "/readings",
            json=payload,
            headers={"X-API-Key": "secret-test-key-xyz"},
        )
        assert res_ok.status_code == 200
        assert res_ok.json()["status"] == "RECORDED"
    finally:
        if old_key is not None:
            os.environ["AQUASWARM_API_KEY"] = old_key
        else:
            os.environ.pop("AQUASWARM_API_KEY", None)


def test_readings_api_validation_bounds():
    """POST /readings validates inputs: rejects negative consumption, level > capacity, unknown tank."""
    test_client = TestClient(app)
    headers = _get_api_headers()

    # Negative consumption
    res_neg = test_client.post(
        "/readings",
        json={"tank_code": "TANK-001", "current_level": 5000.0, "consumption": -50.0},
        headers=headers,
    )
    assert res_neg.status_code in {400, 422}

    # Current level exceeding known capacity (TANK-001 capacity is 10000.0)
    res_overflow = test_client.post(
        "/readings",
        json={"tank_code": "TANK-001", "current_level": 999999.0, "consumption": 100.0},
        headers=headers,
    )
    assert res_overflow.status_code == 400

    # Unknown tank
    res_unknown = test_client.post(
        "/readings",
        json={"tank_code": "TANK-NONEXISTENT-999", "current_level": 1000.0, "consumption": 10.0},
        headers=headers,
    )
    assert res_unknown.status_code == 404


def test_readings_api_successful_ingestion():
    """Valid reading returns rich structured response with tank metadata."""
    test_client = TestClient(app)
    headers = _get_api_headers()
    res = test_client.post(
        "/readings",
        json={
            "tank_code": "TANK-001",
            "current_level": 7500.0,
            "consumption": 250.0,
            "source": "esp32-sensor-unit-1",
        },
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "RECORDED"
    assert data["tank_code"] == "TANK-001"
    assert data["current_level"] == 7500.0
    assert "fill_percentage" in data
    assert data["fill_percentage"] == 75.0
    assert data["source"].upper() == "ESP32-SENSOR-UNIT-1"


# ---------------------------------------------------------------------------
# 3. Delivery Deduplication & Lifecycle Tests
# ---------------------------------------------------------------------------

def test_delivery_request_deduplication_and_lifecycle():
    """Creating a delivery request with an existing operation_run_id does not create duplicate rows."""
    test_client = TestClient(app)
    headers = _get_api_headers()

    op_id = f"test-op-run-{os.urandom(4).hex()}"
    payload = {
        "site_id": 1,
        "tank_code": "TANK-001",
        "supplier_code": "S-001",
        "quantity": 1000.0,
        "notes": "Automated deduplication test",
        "operation_run_id": op_id,
    }

    # First request
    res1 = test_client.post("/delivery-requests", json=payload, headers=headers)
    assert res1.status_code == 200
    d1 = res1.json()
    delivery_id = d1["id"]
    assert d1["operation_run_id"] == op_id

    # Duplicate request with same operation_run_id returns the existing record
    res2 = test_client.post("/delivery-requests", json=payload, headers=headers)
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["id"] == delivery_id

    # Status transition: approve delivery via /approvals
    res_app = test_client.post(
        "/approvals",
        json={
            "delivery_request_id": delivery_id,
            "approved": True,
            "approved_by": "Operations Manager",
            "decision_note": "Approved for dispatch",
        },
        headers=headers,
    )
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "APPROVED"

    # Status transition: dispatch delivery
    res_disp = test_client.patch(
        f"/delivery-requests/{delivery_id}/status",
        json={"status": "DISPATCHED", "notes": "En route with tanker"},
        headers=headers,
    )
    assert res_disp.status_code == 200
    assert res_disp.json()["status"] == "DISPATCHED"

    # Status transition: complete delivery
    res_deliv = test_client.patch(
        f"/delivery-requests/{delivery_id}/status",
        json={
            "status": "DELIVERED",
            "actual_quantity": 1000.0,
            "notes": "Delivered successfully",
        },
        headers=headers,
    )
    assert res_deliv.status_code == 200
    assert res_deliv.json()["status"] == "DELIVERED"
    assert res_deliv.json()["actual_quantity"] == 1000.0

    # Verification record
    res_verif = test_client.post(
        "/verifications",
        json={
            "delivery_request_id": delivery_id,
            "expected_quantity": 1000.0,
            "actual_quantity": 1000.0,
            "note": "Flow meter discrepancy 0",
        },
        headers=headers,
    )
    assert res_verif.status_code == 200
    v_data = res_verif.json()
    assert v_data["verification_status"] == "VERIFIED"
    assert v_data["discrepancy"] == 0.0


def test_supplier_constraints_and_validation():
    """Verify supplier availability checks and capacity limits."""
    test_client = TestClient(app)
    headers = _get_api_headers()

    # S-003 is unavailable in seed data
    res_unavail = test_client.post(
        "/delivery-requests",
        json={
            "site_id": 1,
            "tank_code": "TANK-001",
            "supplier_code": "S-003",
            "quantity": 500.0,
            "notes": "Testing unavailable supplier",
        },
        headers=headers,
    )
    assert res_unavail.status_code == 400
    assert "unavailable" in res_unavail.json()["detail"].lower()

    # Exceed capacity of S-001 (capacity is 8000.0)
    res_exceed = test_client.post(
        "/delivery-requests",
        json={
            "site_id": 1,
            "tank_code": "TANK-001",
            "supplier_code": "S-001",
            "quantity": 99999.0,
            "notes": "Testing capacity exceedance",
        },
        headers=headers,
    )
    assert res_exceed.status_code == 400
    assert "capacity" in res_exceed.json()["detail"].lower()


def test_delivery_rejection_and_exception_transitions():
    """Verify delivery request rejection and exception status transitions."""
    test_client = TestClient(app)
    headers = _get_api_headers()

    # 1. Create and reject
    res_create = test_client.post(
        "/delivery-requests",
        json={
            "site_id": 1,
            "tank_code": "TANK-001",
            "supplier_code": "S-001",
            "quantity": 1000.0,
            "notes": "To be rejected",
        },
        headers=headers,
    )
    assert res_create.status_code == 200
    req_id = res_create.json()["id"]

    res_rej = test_client.post(
        "/approvals",
        json={
            "delivery_request_id": req_id,
            "approved": False,
            "approved_by": "Site Manager",
            "decision_note": "Capacity not needed today",
        },
        headers=headers,
    )
    assert res_rej.status_code == 200
    assert res_rej.json()["status"] == "REJECTED"

    # 2. Create, approve, dispatch, and trigger DELIVERY_EXCEPTION
    res2 = test_client.post(
        "/delivery-requests",
        json={
            "site_id": 1,
            "tank_code": "TANK-001",
            "supplier_code": "S-001",
            "quantity": 1200.0,
            "notes": "To be flagged as exception",
        },
        headers=headers,
    )
    req2_id = res2.json()["id"]

    test_client.post(
        "/approvals",
        json={"delivery_request_id": req2_id, "approved": True, "approved_by": "Admin"},
        headers=headers,
    )
    test_client.patch(
        f"/delivery-requests/{req2_id}/status",
        json={"status": "DISPATCHED"},
        headers=headers,
    )
    res_exc = test_client.patch(
        f"/delivery-requests/{req2_id}/status",
        json={"status": "DELIVERY_EXCEPTION", "actual_quantity": 400.0, "notes": "Tanker vehicle breakdown en route"},
        headers=headers,
    )
    assert res_exc.status_code == 200
    assert res_exc.json()["status"] == "DELIVERY_EXCEPTION"


# ---------------------------------------------------------------------------
# 4. Operations Safeguards
# ---------------------------------------------------------------------------

def test_clear_operational_data_guarded():
    """Calling clear_operational_data without developer_override raises PermissionError."""
    with pytest.raises(PermissionError):
        ops.clear_operational_data(developer_override=False)


# ---------------------------------------------------------------------------
# 5. Forecasting Readiness & Routing Tests
# ---------------------------------------------------------------------------

def test_forecasting_readiness_evaluation():
    """evaluate_forecasting_readiness computes moving average, variance, and transparent model status."""
    # Sparse historical data
    few_readings = [100.0, 110.0]
    res_sparse = evaluate_forecasting_readiness(few_readings, min_ml_records=14)
    assert res_sparse["model_readiness"] == "LIMITED_DATA"
    assert res_sparse["can_forecast_ml"] is False
    assert res_sparse["records_count"] == 2
    assert res_sparse["baseline_daily_demand"] == 105.0

    # Sufficient historical data
    rich_readings = [100.0, 105.0, 110.0, 95.0, 102.0, 108.0, 104.0, 100.0, 105.0, 110.0, 95.0, 102.0, 108.0, 104.0, 101.0]
    res_rich = evaluate_forecasting_readiness(rich_readings, min_ml_records=14)
    assert res_rich["model_readiness"] == "SUFFICIENT_FOR_ML"
    assert res_rich["can_forecast_ml"] is True
    assert res_rich["records_count"] >= 14
    assert res_rich["trend_direction"] in {"STABLE", "RISING", "FALLING"}


def test_allocation_with_routing():
    """plan_allocation_with_routing produces sequenced deliveries and route details."""
    needs = [
        {"tank_code": "TANK-001", "site_name": "North Site", "priority": "CRITICAL", "shortage": 2000.0, "criticality": "CRITICAL"},
        {"tank_code": "TANK-002", "site_name": "South Site", "priority": "HIGH", "shortage": 1500.0, "criticality": "HIGH"},
    ]
    suppliers = [
        {"supplier_id": "S-001", "name": "Apex Water", "available": True, "available_quantity": 5000.0, "distance_km": 12.0, "eta_minutes": 35, "estimated_cost": 250.0},
    ]
    res = plan_allocation_with_routing(needs, suppliers)
    assert "routed_legs" in res
    assert len(res["routed_legs"]) == 2
    assert res["total_allocated"] == 3500.0
    assert res["routed_legs"][0]["priority"] == "CRITICAL"


# ---------------------------------------------------------------------------
# 6. Notifications Status & Testing
# ---------------------------------------------------------------------------

def test_notifications_status_reporting():
    """get_notification_status reports status of both Email and WhatsApp channels."""
    status = get_notification_status()
    assert "email_ready" in status
    assert "whatsapp_ready" in status
    assert "whatsapp_provider" in status

    # Verify notification tester function returns structured dict
    res = send_test_notification("email", "manager@example.com", "Test Subject", "Test Body")
    assert "success" in res
    assert "channel" in res


# ---------------------------------------------------------------------------
# 7. Authentication & UI Validation Rules
# ---------------------------------------------------------------------------

def test_password_strength_validation():
    """validate_password_strength enforces length and alphanumeric requirements."""
    ok, err = validate_password_strength("short1")
    assert not ok
    assert "at least 10" in err

    ok, err = validate_password_strength("alllettersonly")
    assert not ok
    assert "both letters and numbers" in err

    ok, err = validate_password_strength("1234567890123")
    assert not ok
    assert "both letters and numbers" in err

    ok, err = validate_password_strength("SecureAqua2026!")
    assert ok
    assert err == ""


def test_roadmap_removed_from_app_navigation():
    """Verify that Roadmap is no longer in app navigation or ui.pages."""
    import app as main_app
    import ui.pages as pages_mod

    assert not hasattr(pages_mod, "render_roadmap")
    assert not hasattr(pages_mod, "_ROADMAP")

    # Inspect app.py source to ensure 'pages.append("Roadmap")' is absent
    with open(main_app.__file__, "r", encoding="utf-8") as f:
        src = f.read()
    assert 'pages.append("Roadmap")' not in src
    assert "render_roadmap" not in src


def test_user_unlock_and_direct_reset():
    """Verify admin unlock_user, reset_password_direct, and authenticate flows."""
    from backend import users

    # Verify user exists
    user_row = users.query_one("SELECT id, email FROM users LIMIT 1")
    assert user_row is not None
    email = user_row["email"]

    # Test direct password reset
    test_pw = "AquaRecovery2026!"
    assert users.reset_password_direct(email, test_pw) is True

    # Test authenticate with updated password
    authenticated = users.authenticate(email, test_pw)
    assert authenticated["email"] == email

    # Test unlock
    assert users.unlock_user(email) is True

    # Reset back to AquaAdmin2026!
    users.reset_password_direct(email, "AquaAdmin2026!")


def test_local_dev_password_reset_code_generation():
    """In local environments without SMTP configured, request_password_reset yields one-time code."""
    from backend import users

    user_row = users.query_one("SELECT email FROM users LIMIT 1")
    assert user_row is not None
    email = user_row["email"]

    code = users.request_password_reset(email)
    assert code is not None
    assert len(code) == 8

    # Complete reset with the code
    users.complete_password_reset(email, code, "AquaAdmin2026!")
    auth = users.authenticate(email, "AquaAdmin2026!")
    assert auth["email"] == email


def test_hardware_page_and_navigation():
    """Verify Hardware & Sensors page is integrated in app navigation and modules import properly."""
    import app as main_app
    from ui.hardware_page import get_local_ip, render_hardware_integration

    # Check local IP helper
    ip = get_local_ip()
    assert isinstance(ip, str)
    assert len(ip) > 0

    # Check app.py navigation list includes Hardware & Sensors
    with open(main_app.__file__, "r", encoding="utf-8") as f:
        src = f.read()
    assert '"Hardware & Sensors"' in src
    assert "render_hardware_integration" in src


def test_hardware_specifications_and_placeholder_integrity():
    """Verify hardware specifications adhere to security, pinout, and loopback documentation rules."""
    import ui.hardware_page as hw_mod
    import ui.data_admin as data_mod

    with open(hw_mod.__file__, "r", encoding="utf-8") as f:
        hw_src = f.read()
    with open(data_mod.__file__, "r", encoding="utf-8") as f:
        data_src = f.read()

    # 1. Must use placeholder for API Key in documentation
    assert "<AQUASWARM_API_KEY>" in hw_src
    assert "<AQUASWARM_API_KEY>" in data_src

    # 2. Must clearly label 127.0.0.1:8000 as local testing loopback
    assert "Local Loopback" in hw_src or "Local Testing" in hw_src
    assert "Local testing address" in data_src or "Local testing" in data_src

    # 3. Microcontroller pinout verification
    assert "GPIO 5" in hw_src and "GPIO 18" in hw_src  # JSN-SR04T
    assert "GPIO 19" in hw_src  # YF-S201
    assert "Pico W" in hw_src or "Raspberry Pi" in hw_src

    # 4. Truthful implementation disclosure
    assert "Hardware Integration & Implementation Status" in hw_src or "Implementation & Hardware Readiness Status" in hw_src
    assert "bench-testing" in hw_src or "bench-tested" in hw_src or "bench testing" in hw_src


def test_client_get_latest_readings_method():
    """Verify BackendClient has get_latest_readings and returns list of readings."""
    from backend.client import BackendClient
    client = BackendClient(mode="inprocess")
    assert hasattr(client, "get_latest_readings")
    readings = client.get_latest_readings()
    assert isinstance(readings, list)
    # If readings exist, verify each has tank_code
    for r in readings:
        assert "tank_code" in r



