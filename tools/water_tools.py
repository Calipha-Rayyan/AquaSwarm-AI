from typing import List, Dict


def calculate_shortage(
    current_level: float,
    daily_demand: float
) -> float:
    """Calculate the amount of water required to meet daily demand."""

    shortage = daily_demand - current_level
    return max(shortage, 0.0)


def calculate_fill_percentage(
    current_level: float,
    capacity: float
) -> float:
    """Calculate tank fill percentage."""

    if capacity <= 0:
        return 0.0

    return (current_level / capacity) * 100


def determine_priority(
    fill_percentage: float,
    shortage: float
) -> str:
    """Determine water priority based on tank condition."""

    if shortage > 50 or fill_percentage < 20:
        return "HIGH"

    if shortage > 20 or fill_percentage < 40:
        return "MEDIUM"

    return "LOW"


def rank_suppliers(
    suppliers: List[Dict]
) -> List[Dict]:
    """Rank suppliers using quantity, distance and cost."""

    return sorted(
        suppliers,
        key=lambda supplier: (
            supplier.get("estimated_cost", float("inf")),
            supplier.get("distance_km", float("inf"))
        )
    )