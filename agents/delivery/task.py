from datetime import datetime, timedelta, timezone
from typing import Optional

from crewai import Task

from agents.delivery.agent import create_delivery_agent
from models.schemas import DeliveryResult, AllocationResult


def _validate_allocation(allocation_result: AllocationResult) -> None:
    """Validate the allocation before creating a delivery task."""
    if not allocation_result.tank_id:
        raise ValueError("AllocationResult.tank_id cannot be empty.")

    if allocation_result.allocated_quantity <= 0:
        raise ValueError("Allocated quantity must be greater than zero.")

    if allocation_result.supplier_id is None or str(allocation_result.supplier_id).strip() == "":
        raise ValueError("AllocationResult.supplier_id cannot be empty.")

    if not allocation_result.priority:
        raise ValueError("AllocationResult.priority cannot be empty.")

    if not allocation_result.reasoning:
        raise ValueError("AllocationResult.reasoning cannot be empty.")


def _calculate_eta(
    eta_minutes: Optional[int],
) -> str:
    """
    Calculate a deterministic ETA when supplier ETA is available.

    Returns UNKNOWN when the caller does not provide a supplier ETA, preventing
    the LLM from fabricating a travel time.
    """
    if eta_minutes is None:
        return "UNKNOWN"

    if eta_minutes < 0:
        raise ValueError("ETA minutes cannot be negative.")

    arrival = datetime.now(timezone.utc) + timedelta(minutes=eta_minutes)
    return arrival.isoformat()


def create_delivery_task(
    allocation_result: AllocationResult,
    eta_minutes: Optional[int] = None,
    approval_confirmed: bool = True,
) -> Task:
    """
    Create a delivery-coordination task from an approved allocation.

    `approval_confirmed` is expected to be true only after the application's
    human-manager approval step has completed. The default is kept true for
    compatibility with the existing workflow; production orchestration should
    pass the recorded approval explicitly.
    """
    _validate_allocation(allocation_result)

    if approval_confirmed is not True:
        raise ValueError(
            "Delivery cannot be coordinated without confirmed human-manager approval."
        )

    agent = create_delivery_agent()

    delivery_quantity = float(allocation_result.allocated_quantity)
    supplier_id = str(allocation_result.supplier_id)
    tank_id = str(allocation_result.tank_id)
    priority = str(allocation_result.priority).upper()

    # DISPATCHED matches the backend delivery state machine. The backend can
    # subsequently move this request to DELIVERED or DELIVERY_EXCEPTION.
    delivery_status = "DISPATCHED"
    estimated_arrival = _calculate_eta(eta_minutes)

    return Task(
        description=f"""
Coordinate the following already-approved AquaSwarm water delivery.

Authoritative allocation:
- Tank ID: {tank_id}
- Supplier ID: {supplier_id}
- Allocated quantity: {delivery_quantity:g} units
- Priority: {priority}

Human approval:
- Approval confirmed by application: {approval_confirmed}

Deterministic delivery state:
- Status: {delivery_status}
- Estimated arrival: {estimated_arrival}

Rules:
1. Preserve the exact tank ID, supplier ID, and allocated quantity.
2. Preserve the delivery status as DISPATCHED.
3. Use the supplied estimated arrival exactly when it is not UNKNOWN.
4. If estimated arrival is UNKNOWN, do not invent an ETA. Return UNKNOWN.
5. Do not claim the water has been delivered; DISPATCHED means the delivery
   process has started and the shipment is still outstanding.
6. A later backend verification step will determine whether the actual delivered
   quantity matches the expected quantity.
7. Do not alter allocation values or make a new supplier-selection decision.

Provide:
- tank_id
- supplier_id
- quantity
- status
- estimated_arrival

Return the result as a structured DeliveryResult.
""",
        expected_output="""
A valid DeliveryResult containing:
- tank_id: exactly the supplied tank ID
- supplier_id: exactly the supplied supplier ID
- quantity: exactly the approved allocated quantity
- status: DISPATCHED
- estimated_arrival: the supplied ETA, or UNKNOWN when no ETA was provided

Do not claim delivery completion.
""",
        agent=agent,
        output_pydantic=DeliveryResult,
    )
