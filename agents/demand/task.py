from crewai import Task

from agents.demand.agent import create_demand_agent
from models.schemas import DemandResult, WaterData
from tools.water_tools import (
    calculate_shortage,
    calculate_fill_percentage,
    determine_priority,
)


def create_demand_task(water_data: WaterData) -> Task:
    agent = create_demand_agent()

    shortage = calculate_shortage(
        water_data.current_level,
        water_data.daily_demand,
    )

    fill_percentage = calculate_fill_percentage(
        water_data.current_level,
        water_data.capacity,
    )

    priority = determine_priority(
        fill_percentage,
        shortage,
    )

    return Task(
        description=f"""
        Analyze the following water tank situation:

        Tank ID: {water_data.tank_id}
        Current water level: {water_data.current_level} units
        Tank capacity: {water_data.capacity} units
        Daily demand: {water_data.daily_demand} units
        Inflow: {water_data.inflow} units
        Timestamp: {water_data.timestamp}

        Deterministic calculations already performed by the water
        management tools:

        Water shortage: {shortage} units
        Tank fill percentage: {fill_percentage:.2f}%
        Priority: {priority}

        Use these calculated values as the authoritative numerical results.

        Provide:
        1. Estimated water demand
        2. Water shortage
        3. Priority level
        4. Brief reasoning explaining the tank condition

        Do not recalculate or change the provided shortage or priority.

        Return the result as a structured DemandResult.
        """,
        expected_output="""
        A DemandResult containing:
        - tank_id
        - estimated_demand
        - shortage
        - priority
        - reasoning
        """,
        agent=agent,
        output_pydantic=DemandResult,
    )