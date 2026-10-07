import math

from crewai import Task

from agents.demand.agent import create_demand_agent
from models.schemas import DemandResult, WaterData
from tools.water_tools import assess_tank, default_policy


def _validate_water_data(water_data: WaterData) -> None:
    """Validate the input before running any demand calculations."""
    required_text_fields = {
        "tank_id": water_data.tank_id,
        "timestamp": water_data.timestamp,
    }

    for field_name, value in required_text_fields.items():
        if value is None or str(value).strip() == "":
            raise ValueError(f"WaterData.{field_name} cannot be empty.")

    numeric_fields = {
        "current_level": water_data.current_level,
        "capacity": water_data.capacity,
        "daily_demand": water_data.daily_demand,
        "inflow": water_data.inflow,
    }

    for field_name, value in numeric_fields.items():
        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"WaterData.{field_name} must be numeric."
            ) from exc

        if not math.isfinite(numeric_value):
            raise ValueError(f"WaterData.{field_name} must be finite.")

    if float(water_data.capacity) <= 0:
        raise ValueError("Tank capacity must be greater than zero.")

    if float(water_data.current_level) < 0:
        raise ValueError("Current water level cannot be negative.")

    if float(water_data.current_level) > float(water_data.capacity):
        raise ValueError("Current water level cannot exceed tank capacity.")

    if float(water_data.daily_demand) < 0:
        raise ValueError("Daily demand cannot be negative.")

    if float(water_data.inflow) < 0:
        raise ValueError("Inflow cannot be negative.")


def _normalise_priority(priority: str) -> str:
    """Normalise the deterministic priority value for downstream agents."""
    value = str(priority).strip().upper()
    allowed = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    if value not in allowed:
        raise ValueError(
            f"Unexpected priority from the water assessment: {value!r}. "
            f"Expected one of {sorted(allowed)}."
        )

    return value


def create_demand_task(water_data: WaterData) -> Task:
    """
    Create a demand-analysis task from one WaterData record.

    Shortage, fill percentage, days of cover, priority and the demand
    estimate are deterministic (tools.water_tools.assess_tank). The LLM only
    interprets them; the flow re-applies the deterministic values to the
    structured result so the model can never change them.
    """
    _validate_water_data(water_data)

    current_level = float(water_data.current_level)
    capacity = float(water_data.capacity)
    daily_demand = float(water_data.daily_demand)
    inflow = float(water_data.inflow)

    policy = default_policy()
    assessment = assess_tank(current_level, capacity, daily_demand, inflow, policy)

    shortage = float(assessment.shortage)
    fill_percentage = float(assessment.fill_percentage)
    priority = _normalise_priority(assessment.priority)
    estimated_demand = daily_demand

    if shortage < 0 or not math.isfinite(shortage):
        raise ValueError("The shortage calculation returned an invalid value.")

    agent = create_demand_agent()

    description = f"""
Analyze the following AquaSwarm water tank situation.

Tank data:
- Tank ID: {water_data.tank_id}
- Current water level: {current_level:g} units
- Tank capacity: {capacity:g} units
- Daily demand: {daily_demand:g} units
- Inflow: {inflow:g} units per day
- Timestamp: {water_data.timestamp}

Deterministic management calculations:
- Estimated demand: {estimated_demand:g} units
- Tank fill percentage: {fill_percentage:.2f}%
- Days of cover: {assessment.cover_label}
- Net daily change (inflow - demand): {assessment.net_daily_change:g} units
- Target reserve level ({policy.reserve_days:g} days of net demand, bounded by
  {policy.min_operating_fill_pct:g}%-{policy.max_fill_pct:g}% fill): {assessment.target_level:g} units
- Water shortage (target reserve - current level): {shortage:g} units
- Priority: {priority}

These deterministic numerical values are authoritative.

Your job is to:
1. Preserve the exact tank ID.
2. Preserve the exact estimated demand shown above.
3. Preserve the exact shortage shown above.
4. Preserve the exact priority shown above.
5. Explain briefly what the current tank condition means operationally.

Reasoning guidance:
- A shortage means the tank holds less than its target reserve.
- Days of cover and fill percentage explain how urgent the situation is.
- If the shortage is 0, state that the reserve is sufficient.
- Do not invent historical demand, population, seasonal patterns, future
  consumption, or sensor readings that were not supplied.
- Do not recalculate or modify the deterministic values.

Return the result as a structured DemandResult.
"""

    return Task(
        description=description,
        expected_output=f"""
A valid DemandResult containing:
- tank_id: exactly "{water_data.tank_id}"
- estimated_demand: exactly {estimated_demand:g}
- shortage: exactly {shortage:g}
- priority: exactly "{priority}"
- reasoning: a concise explanation grounded in the supplied data

Do not change the deterministic numeric values.
""",
        agent=agent,
        output_pydantic=DemandResult,
    )