from crewai import Task

from agents.anomaly.agent import create_anomaly_agent
from models.schemas import WaterData, DemandResult, AnomalyResult


def create_anomaly_task(
    water_data: WaterData,
    demand_result: DemandResult,
) -> Task:
    agent = create_anomaly_agent()

    return Task(
        description=f"""
        Analyze the following water tank situation for possible anomalies.

        Tank ID: {water_data.tank_id}
        Current water level: {water_data.current_level} units
        Tank capacity: {water_data.capacity} units
        Daily demand: {water_data.daily_demand} units
        Inflow: {water_data.inflow} units

        Demand analysis:
        Estimated demand: {demand_result.estimated_demand} units
        Shortage: {demand_result.shortage} units
        Priority: {demand_result.priority}

        Determine:
        1. Whether an anomaly is detected
        2. The type of anomaly, if any
        3. Severity
        4. Brief reasoning

        Use the provided water data and demand analysis.
        Return the result as a structured AnomalyResult.
        """,
        expected_output="""
        An AnomalyResult containing:
        - tank_id
        - anomaly_detected
        - anomaly_type
        - severity
        - reasoning
        """,
        agent=agent,
        output_pydantic=AnomalyResult,
    )