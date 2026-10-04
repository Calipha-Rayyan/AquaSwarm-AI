from crewai import Task

from agents.allocation.agent import create_allocation_agent
from models.schemas import AllocationResult, DemandResult, SupplyResult


def create_allocation_task(
    demand_result: DemandResult,
    supply_result: SupplyResult,
) -> Task:
    agent = create_allocation_agent()

    recommended_supplier = next(
        (
            supplier
            for supplier in supply_result.suppliers
            if supplier.supplier_id == supply_result.recommended_supplier
        ),
        None,
    )

    return Task(
        description=f"""
        Determine the water allocation for the following situation.

        Tank ID: {demand_result.tank_id}

        Demand Analysis:
        Estimated demand: {demand_result.estimated_demand} units
        Water shortage: {demand_result.shortage} units
        Priority: {demand_result.priority}

        Supply Analysis:
        Recommended supplier: {supply_result.recommended_supplier}

        Recommended supplier details:
        Available quantity: {
            recommended_supplier.available_quantity
            if recommended_supplier else "Unknown"
        } units
        Distance: {
            recommended_supplier.distance_km
            if recommended_supplier else "Unknown"
        } km
        Estimated cost: {
            recommended_supplier.estimated_cost
            if recommended_supplier else "Unknown"
        }

        Determine:
        1. The quantity of water to allocate
        2. The supplier to use
        3. The priority
        4. Brief reasoning

        The allocated quantity should address the identified shortage
        and should not exceed the recommended supplier's available quantity.

        Use the actual Demand Agent and Supply Agent results provided above.

        Return the result as a structured AllocationResult.
        """,
        expected_output="""
        An AllocationResult containing:
        - tank_id
        - allocated_quantity
        - supplier_id
        - priority
        - reasoning
        """,
        agent=agent,
        output_pydantic=AllocationResult,
    )