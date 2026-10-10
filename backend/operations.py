"""Validated write operations for real operational data.

Used by the Streamlit app (in-process) and by the FastAPI endpoints, so both
paths share one set of rules. Every function raises ValueError with a clear,
user-presentable message when the input is not acceptable.
"""
from __future__ import annotations

import math
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from backend.database import get_connection, query_all, query_one

CRITICALITY_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any, label: str, max_len: int = 120, required: bool = True) -> str:
    text = str(value if value is not None else "").strip()
    if required and not text:
        raise ValueError(f"{label} is required.")
    if len(text) > max_len:
        raise ValueError(f"{label} must be at most {max_len} characters.")
    return text


def _number(value: Any, label: str, minimum: float = 0.0, exclusive: bool = False,
            maximum: Optional[float] = None) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a number.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number.")
    if number < minimum or (exclusive and number == minimum):
        word = "greater than" if exclusive else "at least"
        raise ValueError(f"{label} must be {word} {minimum:g}.")
    if maximum is not None and number > maximum:
        raise ValueError(f"{label} must be at most {maximum:g}.")
    return number


def _timestamp(value: Optional[str]) -> str:
    if not value:
        return _now()
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Timestamp must be ISO 8601, e.g. 2026-10-08T09:30:00Z.") from exc
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    moment = moment.astimezone(timezone.utc)
    if (moment - datetime.now(timezone.utc)).total_seconds() > 300:
        raise ValueError("Timestamp cannot be in the future.")
    return moment.isoformat()


# ---------------------------------------------------------------- sites
def create_site(name: str, location: str, manager_name: str = "",
                population: int = 0, criticality: str = "MEDIUM") -> dict:
    name = _text(name, "Site name")
    location = _text(location, "Location")
    manager_name = _text(manager_name, "Manager name", required=False)
    population = int(_number(population, "Population"))
    criticality = _text(criticality, "Criticality").upper()
    if criticality not in CRITICALITY_LEVELS:
        raise ValueError(f"Criticality must be one of {', '.join(CRITICALITY_LEVELS)}.")

    if query_one("SELECT id FROM sites WHERE lower(name) = lower(?)", (name,)):
        raise ValueError(f"A site named '{name}' already exists.")

    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO sites (name, location, manager_name, created_at, population, criticality) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, location, manager_name or None, _now(), population, criticality),
        )
        conn.commit()
        site_id = int(cur.lastrowid)
    return query_one("SELECT * FROM sites WHERE id = ?", (site_id,))


def update_site(site_id: int, **fields: Any) -> dict:
    site = query_one("SELECT * FROM sites WHERE id = ?", (int(site_id),))
    if not site:
        raise ValueError("Site not found.")

    updates: dict = {}
    if "name" in fields:
        updates["name"] = _text(fields["name"], "Site name")
    if "location" in fields:
        updates["location"] = _text(fields["location"], "Location")
    if "manager_name" in fields:
        updates["manager_name"] = _text(fields["manager_name"], "Manager name", required=False) or None
    if "population" in fields:
        updates["population"] = int(_number(fields["population"], "Population"))
    if "criticality" in fields:
        level = _text(fields["criticality"], "Criticality").upper()
        if level not in CRITICALITY_LEVELS:
            raise ValueError(f"Criticality must be one of {', '.join(CRITICALITY_LEVELS)}.")
        updates["criticality"] = level
    if not updates:
        return site

    assignments = ", ".join(f"{column} = ?" for column in updates)
    with get_connection() as conn:
        conn.execute(f"UPDATE sites SET {assignments} WHERE id = ?", (*updates.values(), int(site_id)))
        conn.commit()
    return query_one("SELECT * FROM sites WHERE id = ?", (int(site_id),))


# ---------------------------------------------------------------- tanks
def _next_tank_code() -> str:
    highest = 0
    for row in query_all("SELECT tank_code FROM tanks"):
        match = re.fullmatch(r"TANK-(\d+)", str(row["tank_code"]).upper())
        if match:
            highest = max(highest, int(match.group(1)))
    return f"TANK-{highest + 1:03d}"


def create_tank(site_id: int, name: str, capacity: float, current_level: float,
                critical_threshold: float = 20.0, tank_code: Optional[str] = None) -> dict:
    if not query_one("SELECT id FROM sites WHERE id = ?", (int(site_id),)):
        raise ValueError("Choose an existing site for this tank.")
    name = _text(name, "Tank name")
    capacity = _number(capacity, "Capacity", exclusive=True)
    current_level = _number(current_level, "Current level")
    if current_level > capacity:
        raise ValueError("Current level cannot exceed the tank capacity.")
    critical_threshold = _number(critical_threshold, "Critical threshold", maximum=100)

    code = _text(tank_code, "Tank code", 30, required=False).upper() or _next_tank_code()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]*", code):
        raise ValueError("Tank code may only contain letters, numbers, '-' and '_'.")
    if query_one("SELECT id FROM tanks WHERE tank_code = ?", (code,)):
        raise ValueError(f"Tank code {code} is already in use.")

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO tanks (tank_code, site_id, name, capacity, current_level, "
            "critical_threshold, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code, int(site_id), name, capacity, current_level, critical_threshold, _now()),
        )
        conn.commit()
    return query_one("SELECT * FROM tanks WHERE tank_code = ?", (code,))


def record_reading(tank_code: str, current_level: Optional[float] = None,
                   consumption: Optional[float] = None, timestamp: Optional[str] = None,
                   source: str = "MANUAL") -> dict:
    """Record a measured tank level and/or the water used in the last 24 hours."""
    tank = query_one("SELECT * FROM tanks WHERE tank_code = ?", (str(tank_code).strip().upper(),))
    if not tank:
        raise ValueError(f"Unknown tank {tank_code!r}.")
    if current_level is None and consumption is None:
        raise ValueError("Provide a tank level, a consumption figure, or both.")

    when = _timestamp(timestamp)
    source = _text(source, "Source", 30, required=False).upper() or "MANUAL"

    with get_connection() as conn:
        if current_level is not None:
            level = _number(current_level, "Tank level")
            if level > float(tank["capacity"]):
                raise ValueError(
                    f"Level {level:g} exceeds the tank capacity of {float(tank['capacity']):g}."
                )
            conn.execute(
                "UPDATE tanks SET current_level = ?, updated_at = ? WHERE id = ?",
                (level, when, tank["id"]),
            )
        if consumption is not None:
            used = _number(consumption, "Consumption")
            conn.execute(
                "INSERT INTO consumption (site_id, tank_id, amount, timestamp, source) "
                "VALUES (?, ?, ?, ?, ?)",
                (tank["site_id"], tank["id"], used, when, source),
            )
        conn.commit()
    return query_one("SELECT * FROM tanks WHERE id = ?", (tank["id"],))


# ---------------------------------------------------------------- suppliers
def _supplier_values(fields: dict, partial: bool) -> dict:
    values: dict = {}
    if "name" in fields or not partial:
        values["name"] = _text(fields.get("name"), "Supplier name")
    if "capacity" in fields or not partial:
        values["capacity"] = _number(fields.get("capacity"), "Capacity", exclusive=True)
    if "available" in fields or not partial:
        values["available"] = 1 if fields.get("available", True) in (True, 1, "1", "true", "True") else 0
    if "distance_km" in fields or not partial:
        values["distance_km"] = _number(fields.get("distance_km", 0), "Distance")
    if "estimated_cost" in fields or not partial:
        values["estimated_cost"] = _number(fields.get("estimated_cost", 0), "Estimated cost")
    if "eta_minutes" in fields or not partial:
        values["eta_minutes"] = int(_number(fields.get("eta_minutes", 60), "ETA (minutes)"))
    if "phone" in fields or not partial:
        values["phone"] = _text(fields.get("phone"), "Phone", 40, required=False) or None
    return values


def create_supplier(**fields: Any) -> dict:
    values = _supplier_values(fields, partial=False)
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO suppliers (supplier_code, name, capacity, available, distance_km, "
            "estimated_cost, eta_minutes, phone, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (f"TMP-{uuid.uuid4().hex[:10]}", values["name"], values["capacity"], values["available"],
             values["distance_km"], values["estimated_cost"], values["eta_minutes"],
             values["phone"], _now()),
        )
        supplier_id = int(cur.lastrowid)
        conn.execute("UPDATE suppliers SET supplier_code = ? WHERE id = ?",
                     (f"S-{supplier_id:03d}", supplier_id))
        conn.commit()
    return query_one("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))


def update_supplier(supplier_id: int, **fields: Any) -> dict:
    if not query_one("SELECT id FROM suppliers WHERE id = ?", (int(supplier_id),)):
        raise ValueError("Supplier not found.")
    values = _supplier_values(fields, partial=True)
    if not values:
        return query_one("SELECT * FROM suppliers WHERE id = ?", (int(supplier_id),))
    values["last_updated"] = _now()
    assignments = ", ".join(f"{column} = ?" for column in values)
    with get_connection() as conn:
        conn.execute(f"UPDATE suppliers SET {assignments} WHERE id = ?", (*values.values(), int(supplier_id)))
        conn.commit()
    return query_one("SELECT * FROM suppliers WHERE id = ?", (int(supplier_id),))


# ---------------------------------------------------------------- maintenance
def clear_operational_data() -> dict:
    """Remove every operational record (sites, tanks, readings, suppliers,
    deliveries, alerts, audit trail). User accounts are not touched."""
    tables = (
        "verifications", "approvals", "delivery_requests", "alerts", "agent_runs",
        "consumption", "tanks", "suppliers", "sites",
    )
    removed = {}
    with get_connection() as conn:
        for table in tables:
            removed[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
    return removed