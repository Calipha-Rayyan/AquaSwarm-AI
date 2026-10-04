from math import isfinite
from typing import Dict, List


def _number(value, field_name: str, allow_zero: bool = True) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc

    if not isfinite(number):
        raise ValueError(f"{field_name} must be finite.")

    if number < 0 or (not allow_zero and number == 0):
        raise ValueError(f"{field_name} must be greater than zero." if not allow_zero
                         else f"{field_name} cannot be negative.")
    return number


def calculate_shortage(
    current_level: float,
    daily_demand: float,
) -> float:
    """
    Calculate the water quantity required to meet the supplied daily demand
    from the current stored level.
    """
    current = _number(current_level, "current_level")
    demand = _number(daily_demand, "daily_demand")
    return max(demand - current, 0.0)


def calculate_fill_percentage(
    current_level: float,
    capacity: float,
) -> float:
    """Calculate tank fill percentage."""
    current = _number(current_level, "current_level")
    cap = _number(capacity, "capacity", allow_zero=False)

    percentage = (current / cap) * 100.0
    return min(max(percentage, 0.0), 100.0)


def determine_priority(
    fill_percentage: float,
    shortage: float,
) -> str:
    """Determine operational priority from fill level and shortage."""
    fill = _number(fill_percentage, "fill_percentage")
    shortage_value = _number(shortage, "shortage")

    if fill > 100:
        raise ValueError("fill_percentage cannot exceed 100.")

    if shortage_value > 50 or fill < 20:
        return "HIGH"

    if shortage_value > 20 or fill < 40:
        return "MEDIUM"

    return "LOW"


def rank_suppliers(
    suppliers: List[Dict],
) -> List[Dict]:
    """
    Deterministically rank already-eligible suppliers.

    Cost is the primary criterion, distance the secondary criterion, and
    larger available quantity is used as a stable tie-breaker.
    """
    if suppliers is None:
        return []

    normalized = []

    for supplier in suppliers:
        if not isinstance(supplier, dict):
            raise ValueError("Each supplier must be a dictionary.")

        supplier_id = supplier.get("supplier_id")
        if supplier_id is None or str(supplier_id).strip() == "":
            raise ValueError("Each supplier requires supplier_id.")

        available_quantity = _number(
            supplier.get("available_quantity", 0),
            "available_quantity",
        )
        distance_km = _number(
            supplier.get("distance_km", 0),
            "distance_km",
        )
        estimated_cost = _number(
            supplier.get("estimated_cost", 0),
            "estimated_cost",
        )

        item = dict(supplier)
        item["supplier_id"] = str(supplier_id).strip()
        item["available_quantity"] = available_quantity
        item["distance_km"] = distance_km
        item["estimated_cost"] = estimated_cost
        normalized.append(item)

    return sorted(
        normalized,
        key=lambda supplier: (
            supplier["estimated_cost"],
            supplier["distance_km"],
            -supplier["available_quantity"],
            supplier["supplier_id"],
        ),
    )
