import math

from crewai import Task

from agents.demand.agent import create_demand_agent
from models.schemas import DemandResult, WaterData
from tools.water_tools import (
    calculate_shortage,
    calculate_fill_percentage,
    determine_priority,
)


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
            f"Unexpected priority returned by determine_priority(): {value!r}. "
            f"Expected one of {sorted(allowed)}."
        )

    return value


def create_demand_task(water_data: WaterData) -> Task:
    """
    Create a demand-analysis task from one WaterData record.

    Shortage, fill percentage, priority, and the current demand estimate are
    deterministic inputs. The LLM is used for interpretation/reasoning, not to
    replace those numerical calculations.
    """
    _validate_water_data(water_data)

    current_level = float(water_data.current_level)
    capacity = float(water_data.capacity)
    daily_demand = float(water_data.daily_demand)
    inflow = float(water_data.inflow)

    shortage = float(calculate_shortage(current_level, daily_demand))
    fill_percentage = float(calculate_fill_percentage(current_level, capacity))
    priority = _normalise_priority(
        determine_priority(fill_percentage, shortage)
    )

    if shortage < 0 or not math.isfinite(shortage):
        raise ValueError("calculate_shortage() returned an invalid value.")

    if not 0 <= fill_percentage <= 100:
        raise ValueError(
            "calculate_fill_percentage() must return a value between 0 and 100."
        )

    # The supplied dataset contains daily_demand rather than a historical
    # forecasting series. Therefore the current daily demand is the only
    # evidence-based demand estimate available to this task.
    estimated_demand = daily_demand

    agent = create_demand_agent()

    description = f"""
Analyze the following AquaSwarm water tank situation.

Tank data:
- Tank ID: {water_data.tank_id}
- Current water level: {current_level:g} units
- Tank capacity: {capacity:g} units
- Daily demand: {daily_demand:g} units
- Inflow: {inflow:g} units
- Timestamp: {water_data.timestamp}

Deterministic management calculations:
- Estimated demand: {estimated_demand:g} units
- Water shortage: {shortage:g} units
- Tank fill percentage: {fill_percentage:.2f}%
- Priority: {priority}

These deterministic numerical values are authoritative.

Your job is to:
1. Preserve the exact tank ID.
2. Preserve the exact estimated demand shown above.
3. Preserve the exact shortage shown above.
4. Preserve the exact priority shown above.
5. Explain briefly what the current tank condition means operationally.

Reasoning guidance:
- A shortage means the current level is insufficient for the supplied demand
  according to the deterministic shortage calculation.
- Low fill percentage indicates reduced available reserve.
- Inflow can be mentioned as supporting context, but it must not be used to
  replace the authoritative shortage or priority.
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
