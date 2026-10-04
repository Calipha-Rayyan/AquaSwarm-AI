from crewai import Task

from agents.supply.agent import create_supply_agent
from models.schemas import WaterData, DemandResult, SupplyResult
from tools.water_tools import rank_suppliers


def create_supply_task(
    water_data: WaterData,
    demand_result: DemandResult,
) -> Task:
    agent = create_supply_agent()

    required_quantity = demand_result.shortage

    all_suppliers = [
        {
            "supplier_id": "S-001",
            "available_quantity": 100,
            "distance_km": 15,
            "estimated_cost": 500,
        },
        {
            "supplier_id": "S-002",
            "available_quantity": 60,
            "distance_km": 8,
            "estimated_cost": 600,
        },
        {
            "supplier_id": "S-003",
            "available_quantity": 30,
            "distance_km": 5,
            "estimated_cost": 350,
        },
    ]

    eligible_suppliers = [
        supplier
        for supplier in all_suppliers
        if supplier["available_quantity"] >= required_quantity
    ]

    ranked_suppliers = rank_suppliers(eligible_suppliers)

    recommended_supplier = (
        ranked_suppliers[0]["supplier_id"]
        if ranked_suppliers
        else None
    )

    return Task(
        description=f"""
        Analyze the following water supply requirement.

        Tank ID: {water_data.tank_id}
        Required water quantity: {required_quantity} units
        Priority: {demand_result.priority}

        Available suppliers:

        {all_suppliers}

        Deterministic supplier filtering has already been performed.

        Eligible suppliers that can fulfill the required quantity:
        {eligible_suppliers}

        Suppliers have also been ranked using the water management
        ranking tool based on estimated cost and distance.

        Ranked eligible suppliers:
        {ranked_suppliers}

        Recommended supplier:
        {recommended_supplier}

        Use these calculations as the authoritative supplier selection.

        Provide:
        1. The available supplier options
        2. The recommended supplier
        3. Brief reasoning explaining why the recommended supplier
           is suitable

        Do not change the recommended supplier.

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