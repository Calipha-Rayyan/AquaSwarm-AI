import math
from typing import Any, Iterable, Mapping, Optional

from crewai import Task

from agents.supply.agent import create_supply_agent
from models.schemas import WaterData, DemandResult, SupplyResult
from tools.water_tools import rank_suppliers


def _validate_inputs(
    water_data: WaterData,
    demand_result: DemandResult,
) -> None:
    """Validate the upstream demand result before supplier selection."""
    if water_data.tank_id is None or str(water_data.tank_id).strip() == "":
        raise ValueError("WaterData.tank_id cannot be empty.")

    try:
        shortage = float(demand_result.shortage)
    except (TypeError, ValueError) as exc:
        raise ValueError("DemandResult.shortage must be numeric.") from exc

    if not math.isfinite(shortage):
        raise ValueError("DemandResult.shortage must be finite.")

    if shortage < 0:
        raise ValueError("DemandResult.shortage cannot be negative.")

    if demand_result.priority is None or str(demand_result.priority).strip() == "":
        raise ValueError("DemandResult.priority cannot be empty.")


def _normalise_supplier(raw: Mapping[str, Any]) -> dict:
    """
    Normalize backend/CSV supplier records to the structure expected by the
    supplier-ranking tool.

    The current backend supplier schema exposes capacity + available, while the
    original agent task used available_quantity. For this prototype, capacity is
    treated as the maximum fulfillable quantity when the supplier is available.
    """
    supplier_id = raw.get("supplier_code", raw.get("supplier_id", raw.get("id")))
    if supplier_id is None or str(supplier_id).strip() == "":
        raise ValueError(f"Supplier record is missing an identifier: {raw}")

    capacity = raw.get("available_quantity", raw.get("capacity"))
    if capacity is None:
        raise ValueError(
            f"Supplier {supplier_id!r} is missing available quantity/capacity."
        )

    try:
        capacity = float(capacity)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Supplier {supplier_id!r} has a non-numeric capacity."
        ) from exc

    if not math.isfinite(capacity) or capacity < 0:
        raise ValueError(
            f"Supplier {supplier_id!r} has an invalid capacity."
        )

    available_value = raw.get("available", True)
    available = (
        available_value
        if isinstance(available_value, bool)
        else str(available_value).strip().lower() in {"1", "true", "yes", "available"}
    )

    available_quantity = float(
        raw.get("available_quantity", capacity if available else 0.0)
    )

    if not math.isfinite(available_quantity) or available_quantity < 0:
        raise ValueError(
            f"Supplier {supplier_id!r} has invalid available quantity."
        )

    distance = raw.get("distance_km", 0.0)
    cost = raw.get("estimated_cost", 0.0)
    eta = raw.get("eta_minutes")

    try:
        distance = float(distance or 0.0)
        cost = float(cost or 0.0)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Supplier {supplier_id!r} has invalid distance or cost."
        ) from exc

    if distance < 0 or cost < 0 or not math.isfinite(distance) or not math.isfinite(cost):
        raise ValueError(
            f"Supplier {supplier_id!r} has invalid distance or estimated cost."
        )

    if eta is not None:
        try:
            eta = int(eta)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Supplier {supplier_id!r} has invalid ETA minutes."
            ) from exc

        if eta < 0:
            raise ValueError(
                f"Supplier {supplier_id!r} has negative ETA minutes."
            )

    return {
        "supplier_id": str(supplier_id),
        "name": raw.get("name", str(supplier_id)),
        "available": bool(available),
        "available_quantity": available_quantity if available else 0.0,
        "capacity": capacity,
        "distance_km": distance,
        "estimated_cost": cost,
        "eta_minutes": eta,
    }


def _load_suppliers(
    suppliers: Optional[Iterable[Mapping[str, Any]]],
) -> list[dict]:
    """Use supplied supplier records or retrieve them from the AquaSwarm backend."""
    if suppliers is None:
        from backend.client import BackendClient

        suppliers = BackendClient().get_suppliers(available_only=False)

    normalised = [_normalise_supplier(item) for item in suppliers]

    if not normalised:
        raise ValueError("No supplier records were provided by the data source.")

    return normalised


def _validate_ranked_result(
    ranked_suppliers: list[dict],
    recommended_supplier: Optional[str],
) -> None:
    """Ensure the deterministic ranking result is internally consistent."""
    supplier_ids = {str(item["supplier_id"]) for item in ranked_suppliers}

    if recommended_supplier is not None and str(recommended_supplier) not in supplier_ids:
        raise ValueError(
            "rank_suppliers() returned a recommended supplier that is not in the "
            "ranked supplier list."
        )


def create_supply_task(
    water_data: WaterData,
    demand_result: DemandResult,
    suppliers: Optional[Iterable[Mapping[str, Any]]] = None,
) -> Task:
    """
    Create a supply-analysis task using real supplier data.

    Supplier eligibility and ranking are deterministic. The LLM explains the
    resulting decision but cannot change the recommended supplier.
    """
    _validate_inputs(water_data, demand_result)

    required_quantity = float(demand_result.shortage)
    all_suppliers = _load_suppliers(suppliers)

    if required_quantity == 0:
        eligible_suppliers = []
        ranked_suppliers = []
        recommended_supplier = None
    else:
        eligible_suppliers = [
            supplier
            for supplier in all_suppliers
            if supplier["available"] and supplier["available_quantity"] >= required_quantity
        ]

        ranked_suppliers = rank_suppliers(eligible_suppliers)

        recommended_supplier = (
            str(ranked_suppliers[0]["supplier_id"])
            if ranked_suppliers
            else None
        )

    _validate_ranked_result(ranked_suppliers, recommended_supplier)

    agent = create_supply_agent()

    if required_quantity == 0:
        recommendation_text = (
            "NO_SUPPLIER_REQUIRED because the deterministic shortage is zero."
        )
    elif recommended_supplier is None:
        recommendation_text = (
            "NO_ELIGIBLE_SUPPLIER because no available supplier can fulfill "
            "the required quantity."
        )
    else:
        recommendation_text = recommended_supplier

    description = f"""
Analyze the following AquaSwarm water supply requirement.

Tank ID:
{water_data.tank_id}

Required water quantity:
{required_quantity:g} units

Priority:
{demand_result.priority}

All supplier records from the current data source:
{all_suppliers}

Deterministic supplier filtering:
Only available suppliers with fulfillable quantity greater than or equal to
the required quantity are eligible.

Eligible suppliers:
{eligible_suppliers}

Deterministic ranking:
Eligible suppliers have been ranked by the AquaSwarm supplier-ranking tool.
Ranked eligible suppliers:
{ranked_suppliers}

Authoritative recommendation:
{recommendation_text}

Rules:
1. Preserve the exact tank_id.
2. Treat the eligible-supplier list and ranking as authoritative.
3. Do not change the recommended supplier.
4. Do not invent supplier capacity, cost, distance, ETA, or availability.
5. If no supplier is eligible, clearly state that procurement cannot be fulfilled
   from the supplied supplier records.
6. If required quantity is zero, state that no supplier is needed.
7. Do not create a new supplier or manually select a different supplier.

Provide:
1. The supplier options available to the task.
2. The deterministic recommended supplier, if one exists.
3. Brief reasoning explaining the recommendation or explaining why no supplier
   can currently fulfill the request.

Return the result as a structured SupplyResult.
"""

    return Task(
        description=description,
        expected_output="""
A valid SupplyResult containing:
- tank_id
- suppliers
- recommended_supplier
- reasoning

The tank_id must match the supplied WaterData.tank_id.
The recommended_supplier must match the deterministic ranking result.
Use null/None for recommended_supplier when no supplier is eligible or no supply
is required, if the SupplyResult schema permits an optional value.
""",
        agent=agent,
        output_pydantic=SupplyResult,
    )
