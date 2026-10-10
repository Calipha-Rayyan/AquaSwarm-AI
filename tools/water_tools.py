"""Deterministic water-management calculations for AquaSwarm AI.

Everything the pipeline treats as authoritative is computed here, so the
LLM agents only explain results and never invent numbers.

Operating model
---------------
* ``daily_demand`` and ``inflow`` are both per-day volumes.
* Days of cover = how long the stored water lasts at the current net
  drawdown (demand minus inflow).
* A tank needs replenishment when it holds less than the target reserve:
  ``reserve_days`` of net demand, never below ``min_operating_fill_pct`` of
  capacity, and never above ``max_fill_pct`` of capacity.
* Priority is driven by days of cover and fill level, so it changes as
  conditions change instead of being fixed by one absolute unit threshold.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import inf, isfinite
from typing import Dict, List, Optional


# --------------------------------------------------------------------------
# Policy (override per call, or globally through config.settings)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class WaterPolicy:
    reserve_days: float = 7.0              # target days of cover
    min_operating_fill_pct: float = 40.0   # never plan below this fill
    max_fill_pct: float = 95.0             # never plan above this fill
    critical_fill_pct: float = 20.0        # tank's own critical threshold
    critical_cover_days: float = 1.0
    high_cover_days: float = 3.0
    high_fill_pct: float = 30.0
    medium_fill_pct: float = 50.0


def default_policy() -> WaterPolicy:
    """Policy built from config.settings when available."""
    try:
        from config import settings as s

        return WaterPolicy(
            reserve_days=s.AQUASWARM_RESERVE_DAYS,
            min_operating_fill_pct=s.AQUASWARM_MIN_OPERATING_FILL_PCT,
            max_fill_pct=s.AQUASWARM_MAX_FILL_PCT,
        )
    except Exception:
        return WaterPolicy()


def _number(value, field_name: str, allow_zero: bool = True) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc

    if not isfinite(number):
        raise ValueError(f"{field_name} must be finite.")

    if number < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    if not allow_zero and number == 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return number


# --------------------------------------------------------------------------
# Building blocks
# --------------------------------------------------------------------------
def calculate_fill_percentage(current_level: float, capacity: float) -> float:
    """Tank fill percentage, clamped to 0-100."""
    current = _number(current_level, "current_level")
    cap = _number(capacity, "capacity", allow_zero=False)
    return min(max((current / cap) * 100.0, 0.0), 100.0)


def calculate_days_of_cover(
    current_level: float, daily_demand: float, inflow: float = 0.0
) -> Optional[float]:
    """Days the stored water lasts. ``None`` means the tank is not draining
    (inflow covers demand), i.e. effectively unlimited cover."""
    level = _number(current_level, "current_level")
    demand = _number(daily_demand, "daily_demand")
    supply = _number(inflow, "inflow")

    drawdown = demand - supply
    if drawdown <= 0:
        return None
    return level / drawdown


def calculate_target_level(
    capacity: float,
    daily_demand: float,
    inflow: float = 0.0,
    policy: Optional[WaterPolicy] = None,
) -> float:
    """Level the tank should hold: the reserve target, bounded by the
    operating floor and the maximum safe fill."""
    p = policy or default_policy()
    cap = _number(capacity, "capacity", allow_zero=False)
    demand = _number(daily_demand, "daily_demand")
    supply = _number(inflow, "inflow")

    reserve_need = max(demand - supply, 0.0) * p.reserve_days
    floor = cap * p.min_operating_fill_pct / 100.0
    ceiling = cap * p.max_fill_pct / 100.0
    return min(max(reserve_need, floor), ceiling)


def calculate_shortage(
    current_level: float,
    daily_demand: float,
    inflow: float = 0.0,
    capacity: Optional[float] = None,
    policy: Optional[WaterPolicy] = None,
) -> float:
    """Volume needed to restore the target reserve.

    Without ``capacity`` the legacy rule is used (demand minus level) so old
    callers keep working.
    """
    level = _number(current_level, "current_level")
    demand = _number(daily_demand, "daily_demand")

    if capacity is None:
        return max(demand - level, 0.0)

    target = calculate_target_level(capacity, demand, inflow, policy)
    return max(target - level, 0.0)


def determine_priority(
    fill_percentage: float,
    shortage: float,
    days_of_cover: Optional[float] = None,
    policy: Optional[WaterPolicy] = None,
) -> str:
    """Operational priority: CRITICAL / HIGH / MEDIUM / LOW.

    ``days_of_cover=None`` means the tank is not draining.
    """
    p = policy or default_policy()
    fill = _number(fill_percentage, "fill_percentage")
    shortage_value = _number(shortage, "shortage")
    if fill > 100:
        raise ValueError("fill_percentage cannot exceed 100.")

    cover = inf if days_of_cover is None else float(days_of_cover)

    if fill <= p.critical_fill_pct or cover < p.critical_cover_days:
        return "CRITICAL"
    if fill < p.high_fill_pct or cover < p.high_cover_days:
        return "HIGH"
    if shortage_value > 0 or fill < p.medium_fill_pct:
        return "MEDIUM"
    return "LOW"


# --------------------------------------------------------------------------
# One-call assessment used by the demand task and the flow
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class TankAssessment:
    fill_percentage: float
    days_of_cover: Optional[float]
    net_daily_change: float
    target_level: float
    shortage: float
    priority: str
    estimated_demand: float

    def as_dict(self) -> Dict:
        return asdict(self)

    @property
    def hours_to_empty(self) -> Optional[float]:
        return None if self.days_of_cover is None else self.days_of_cover * 24.0

    @property
    def cover_label(self) -> str:
        if self.days_of_cover is None:
            return "Self-sustaining"
        if self.days_of_cover < 2:
            return f"{self.days_of_cover * 24:.1f} hours"
        return f"{self.days_of_cover:.1f} days"


def assess_tank(
    current_level: float,
    capacity: float,
    daily_demand: float,
    inflow: float = 0.0,
    policy: Optional[WaterPolicy] = None,
) -> TankAssessment:
    p = policy or default_policy()
    fill = calculate_fill_percentage(current_level, capacity)
    cover = calculate_days_of_cover(current_level, daily_demand, inflow)
    target = calculate_target_level(capacity, daily_demand, inflow, p)
    shortage = calculate_shortage(current_level, daily_demand, inflow, capacity, p)
    priority = determine_priority(fill, shortage, cover, p)
    return TankAssessment(
        fill_percentage=fill,
        days_of_cover=cover,
        net_daily_change=float(inflow) - float(daily_demand),
        target_level=target,
        shortage=shortage,
        priority=priority,
        estimated_demand=float(daily_demand),
    )


# --------------------------------------------------------------------------
# Supplier ranking (unchanged behaviour)
# --------------------------------------------------------------------------
def rank_suppliers(suppliers: List[Dict], priority: Optional[str] = None) -> List[Dict]:
    """Rank eligible suppliers.

    Normal conditions: lowest cost first. When the situation is urgent
    (HIGH/CRITICAL) the fastest supplier (ETA) comes first, because delay is
    then more costly than price. Distance and larger quantity break ties.
    """
    if suppliers is None:
        return []

    urgent = str(priority or "").upper() in {"HIGH", "CRITICAL"}
    normalized = []
    for supplier in suppliers:
        if not isinstance(supplier, dict):
            raise ValueError("Each supplier must be a dictionary.")

        supplier_id = supplier.get("supplier_id")
        if supplier_id is None or str(supplier_id).strip() == "":
            raise ValueError("Each supplier requires supplier_id.")

        item = dict(supplier)
        item["supplier_id"] = str(supplier_id).strip()
        item["available_quantity"] = _number(
            supplier.get("available_quantity", 0), "available_quantity"
        )
        item["distance_km"] = _number(supplier.get("distance_km", 0), "distance_km")
        item["estimated_cost"] = _number(
            supplier.get("estimated_cost", 0), "estimated_cost"
        )
        eta = supplier.get("eta_minutes")
        item["_eta"] = float(eta) if eta is not None else 1e9
        normalized.append(item)

    def key(item):
        if urgent:
            return (item["_eta"], item["estimated_cost"], item["distance_km"],
                    -item["available_quantity"], item["supplier_id"])
        return (item["estimated_cost"], item["_eta"], item["distance_km"],
                -item["available_quantity"], item["supplier_id"])

    ranked = sorted(normalized, key=key)
    for item in ranked:
        item.pop("_eta", None)
    return ranked


# --------------------------------------------------------------------------
# Multi-tank allocation under limited supply (PRD UC-04 / FR-06)
# --------------------------------------------------------------------------
_LEVEL_WEIGHT = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def plan_allocation(needs: List[Dict], suppliers: List[Dict]) -> Dict:
    """Share limited supplier volume between tanks that need water.

    ``needs``: dicts with tank_code, site_name, shortage, priority,
    criticality, population, days_of_cover.
    ``suppliers``: dicts with supplier_id, available (bool),
    available_quantity, estimated_cost, distance_km, eta_minutes.

    Tanks are served in a transparent order: operational priority, then site
    criticality, then least days of cover, then population served. A supplier's
    volume is consumed as it is allocated. Nothing is allocated beyond
    availability; what cannot be covered is reported as unmet demand.
    """
    def order(n):
        cover = n.get("days_of_cover")
        return (
            -_LEVEL_WEIGHT.get(str(n.get("priority", "LOW")).upper(), 1),
            -_LEVEL_WEIGHT.get(str(n.get("criticality", "MEDIUM")).upper(), 2),
            float("inf") if cover is None else float(cover),
            -int(n.get("population") or 0),
            str(n.get("tank_code")),
        )

    queue = sorted((n for n in needs if float(n.get("shortage", 0)) > 0), key=order)
    pool = {
        str(s["supplier_id"]): dict(s)
        for s in suppliers
        if s.get("available") and float(s.get("available_quantity", 0)) > 0
    }

    rows, notes = [], []
    for need in queue:
        wanted = float(need["shortage"])
        urgent = str(need.get("priority", "")).upper() in {"HIGH", "CRITICAL"}
        ranked = rank_suppliers(list(pool.values()), "HIGH" if urgent else None)

        full = next((s for s in ranked if float(s["available_quantity"]) >= wanted), None)
        chosen = full or (max(ranked, key=lambda s: float(s["available_quantity"])) if ranked else None)

        if chosen is None:
            rows.append({**need, "supplier_id": None, "allocated": 0.0, "unmet": wanted})
            notes.append(f"{need['tank_code']}: no supplier volume left.")
            continue

        given = min(wanted, float(chosen["available_quantity"]))
        pool[str(chosen["supplier_id"])]["available_quantity"] = float(chosen["available_quantity"]) - given
        rows.append({**need, "supplier_id": str(chosen["supplier_id"]),
                     "allocated": given, "unmet": wanted - given})
        if wanted - given > 0:
            notes.append(
                f"{need['tank_code']}: only {given:g} of {wanted:g} units could be covered "
                f"(largest remaining supplier volume)."
            )

    total_need = sum(float(n["shortage"]) for n in queue)
    total_given = sum(r["allocated"] for r in rows)
    return {
        "allocations": rows,
        "total_need": total_need,
        "total_allocated": total_given,
        "unmet_total": max(total_need - total_given, 0.0),
        "constraint_notes": notes,
    }