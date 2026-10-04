from crewai import Task

from agents.anomaly.agent import create_anomaly_agent
from models.schemas import WaterData, DemandResult, AnomalyResult


def _validate_inputs(
    water_data: WaterData,
    demand_result: DemandResult,
) -> None:
    """Fail early when upstream agent results do not match the tank being analyzed."""
    if water_data.tank_id != demand_result.tank_id:
        raise ValueError(
            "WaterData and DemandResult must refer to the same tank. "
            f"Got {water_data.tank_id!r} and {demand_result.tank_id!r}."
        )

    if water_data.capacity <= 0:
        raise ValueError("Tank capacity must be greater than zero.")

    if not 0 <= water_data.current_level <= water_data.capacity:
        raise ValueError(
            "Current water level must be between 0 and the tank capacity."
        )

    if water_data.daily_demand < 0 or water_data.inflow < 0:
        raise ValueError("Daily demand and inflow cannot be negative.")

    if demand_result.estimated_demand < 0 or demand_result.shortage < 0:
        raise ValueError("Demand and shortage values cannot be negative.")


def _build_signal_summary(
    water_data: WaterData,
    demand_result: DemandResult,
) -> str:
    """Create transparent numeric signals for the LLM to evaluate."""
    fill_percent = (water_data.current_level / water_data.capacity) * 100.0
    net_daily_change = water_data.inflow - water_data.daily_demand
    demand_gap = water_data.daily_demand - water_data.inflow

    return (
        "Derived monitoring signals:\n"
        f"- Tank fill level: {fill_percent:.2f}% of capacity\n"
        f"- Net daily change from inflow minus demand: {net_daily_change:.2f} units\n"
        f"- Demand minus inflow gap: {demand_gap:.2f} units\n"
        f"- Reported shortage from Demand Agent: {demand_result.shortage:.2f} units\n\n"
        "Interpretation guidance:\n"
        "- A low fill percentage can indicate a low-level condition.\n"
        "- Persistent demand materially exceeding inflow can support a possible "
        "supply imbalance or depletion risk.\n"
        "- Do not label leakage solely from low water level; leakage should only be "
        "considered when the supplied figures support unexplained loss or abnormal "
        "behavior.\n"
        "- A shortage by itself is not necessarily an anomaly. Classify it as an "
        "anomaly only when the operating measurements indicate abnormal conditions.\n"
        "- Do not invent historical baselines, sensor readings, or external evidence."
    )


def create_anomaly_task(
    water_data: WaterData,
    demand_result: DemandResult,
) -> Task:
    """Create the anomaly-analysis task from the actual upstream results."""
    _validate_inputs(water_data, demand_result)

    agent = create_anomaly_agent()
    signal_summary = _build_signal_summary(water_data, demand_result)

    description = f"""
Analyze the following AquaSwarm water tank situation for possible
operational anomalies.

Water data:
- Tank ID: {water_data.tank_id}
- Current water level: {water_data.current_level} units
- Tank capacity: {water_data.capacity} units
- Daily demand: {water_data.daily_demand} units
- Inflow: {water_data.inflow} units
- Timestamp: {water_data.timestamp}

Demand analysis:
- Estimated demand: {demand_result.estimated_demand} units
- Water shortage: {demand_result.shortage} units
- Priority: {demand_result.priority}
- Demand reasoning: {demand_result.reasoning}

{signal_summary}

Determine:
1. Whether an operational anomaly is detected.
2. The anomaly type, if any. Prefer one concise type such as:
   LOW_WATER_LEVEL, ABNORMAL_INFLOW, POSSIBLE_LEAKAGE,
   RAPID_DEPLETION, or NONE.
3. Severity using one of: LOW, MEDIUM, HIGH, CRITICAL.
4. A brief evidence-based reasoning.

Important constraints:
- Use only the supplied water data and Demand Agent result.
- Keep the same tank_id in the final result.
- Do not treat ordinary shortage as an anomaly unless the measurements
  indicate abnormal behavior.
- Do not invent historical data or unsupported causes.
- When no anomaly is supported, use anomaly_detected=false and
  anomaly_type=NONE.

Return the result as a structured AnomalyResult.
"""

    return Task(
        description=description,
        expected_output="""
A valid AnomalyResult containing:
- tank_id
- anomaly_detected
- anomaly_type
- severity
- reasoning

The tank_id must match the input tank.
""",
        agent=agent,
        output_pydantic=AnomalyResult,
    )
