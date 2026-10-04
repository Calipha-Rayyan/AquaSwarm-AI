from crewai import Task

from agents.supply.agent import create_supply_agent
from models.schemas import WaterData, DemandResult, SupplyResult


def create_supply_task(
    water_data: WaterData,
    demand_result: DemandResult,
) -> Task:
    agent = create_supply_agent()

    return Task(
        description=f"""
        Analyze available water suppliers for the following requirement.

        Tank ID: {water_data.tank_id}
        Required water quantity: {demand_result.shortage} units
        Priority: {demand_result.priority}

        Available suppliers:

        Supplier S-001:
        - Available quantity: 100 units
        - Distance: 15 km
        - Estimated cost: 500

        Supplier S-002:
        - Available quantity: 60 units
        - Distance: 8 km
        - Estimated cost: 600

        Supplier S-003:
        - Available quantity: 30 units
        - Distance: 5 km
        - Estimated cost: 350

        Determine:
        1. Which suppliers can fulfill the required quantity
        2. Compare the available suppliers
        3. Recommend the most suitable supplier
        4. Provide brief reasoning

        Use the actual shortage from the Demand Agent.
        Return the result as a structured SupplyResult.
        """,
        expected_output="""
        A SupplyResult containing:
        - tank_id
        - suppliers
        - recommended_supplier
        - reasoning
        """,
        agent=agent,
        output_pydantic=SupplyResult,
    )