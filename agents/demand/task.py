from crewai import Task

from agents.demand.agent import create_demand_agent
from models.schemas import DemandResult


def create_demand_task() -> Task:
    agent = create_demand_agent()

    return Task(
        description="""
        Analyze the following water tank situation:

        Tank ID: TANK-001
        Current water level: 30 units
        Tank capacity: 100 units
        Daily demand: 80 units
        Inflow: 10 units

        Determine:
        1. Estimated water demand
        2. Water shortage
        3. Priority level
        4. Brief reasoning

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