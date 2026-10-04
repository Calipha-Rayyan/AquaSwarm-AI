from crewai import Task

from agents.allocation.agent import create_allocation_agent
from models.schemas import AllocationResult, DemandResult, SupplyResult


def _validate_inputs(
    demand_result: DemandResult,
    supply_result: SupplyResult,
) -> None:
    """Validate upstream results before sending them to the LLM."""
    if demand_result.tank_id != supply_result.tank_id:
        raise ValueError(
            "DemandResult and SupplyResult must refer to the same tank."
        )

    if demand_result.shortage < 0:
        raise ValueError("Water shortage cannot be negative.")

    if not supply_result.recommended_supplier:
        raise ValueError(
            "Supply Agent did not provide a recommended supplier."
        )

    recommended = next(
        (
            supplier
            for supplier in supply_result.suppliers
            if supplier.supplier_id == supply_result.recommended_supplier
        ),
        None,
    )

    if recommended is None:
        raise ValueError(
            "The recommended supplier is missing from SupplyResult.suppliers."
        )

    if recommended.available_quantity < 0:
        raise ValueError("Supplier available quantity cannot be negative.")

    if demand_result.shortage > recommended.available_quantity:
        raise ValueError(
            "The recommended supplier cannot fulfill the reported shortage."
        )


def create_allocation_task(
    demand_result: DemandResult,
    supply_result: SupplyResult,
) -> Task:
    """Create the allocation task from validated Demand and Supply results."""
    _validate_inputs(demand_result, supply_result)

    agent = create_allocation_agent()

    recommended_supplier = next(
        supplier
        for supplier in supply_result.suppliers
        if supplier.supplier_id == supply_result.recommended_supplier
    )

    # This is the deterministic upper bound. The LLM should explain the
    # decision, not invent a quantity outside this safe range.
    max_allocatable = min(
        float(demand_result.shortage),
        float(recommended_supplier.available_quantity),
    )

    return Task(
        description=f"""
You are making the final allocation decision for AquaSwarm AI.

The upstream agents have already produced the following validated results.

================ DEMAND RESULT ================
Tank ID: {demand_result.tank_id}
Estimated demand: {demand_result.estimated_demand} units
Water shortage: {demand_result.shortage} units
Priority: {demand_result.priority}
Demand reasoning: {demand_result.reasoning}

================ SUPPLY RESULT ================
Recommended supplier: {supply_result.recommended_supplier}
Supplier list:
{supply_result.suppliers}

Supply reasoning: {supply_result.reasoning}

Recommended supplier details:
Supplier ID: {recommended_supplier.supplier_id}
Available quantity: {recommended_supplier.available_quantity} units
Distance: {recommended_supplier.distance_km} km
Estimated cost: {recommended_supplier.estimated_cost}

================ ALLOCATION RULES ================
1. Tank ID must remain {demand_result.tank_id}.
2. Supplier ID must remain {recommended_supplier.supplier_id}.
3. Allocation cannot be negative.
4. Allocation cannot exceed the reported shortage of {demand_result.shortage} units.
5. Allocation cannot exceed supplier availability of
   {recommended_supplier.available_quantity} units.
6. Therefore, the maximum safe allocation is {max_allocatable} units.
7. Keep the priority exactly as: {demand_result.priority}.
8. Base the reasoning on the supplied results. Do not invent facts.

Return exactly one structured AllocationResult containing:
- tank_id
- allocated_quantity
- supplier_id
- priority
- reasoning
""".strip(),
        expected_output=(
            "A structured AllocationResult. "
            "allocated_quantity must be between 0 and the maximum safe "
            "allocation supplied in the task."
        ),
        agent=agent,
        output_pydantic=AllocationResult,
    )
