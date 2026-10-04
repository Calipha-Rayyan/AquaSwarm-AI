import math

from crewai import Task

from agents.verification.agent import create_verification_agent
from models.schemas import VerificationResult, AllocationResult, DeliveryResult


QUANTITY_TOLERANCE = 0.01


def _validate_inputs(
    allocation_result: AllocationResult,
    delivery_result: DeliveryResult,
) -> None:
    """Validate allocation and delivery results before verification."""
    if not allocation_result.tank_id:
        raise ValueError("AllocationResult.tank_id cannot be empty.")

    if not delivery_result.tank_id:
        raise ValueError("DeliveryResult.tank_id cannot be empty.")

    if allocation_result.tank_id != delivery_result.tank_id:
        raise ValueError(
            "AllocationResult and DeliveryResult must refer to the same tank."
        )

    if allocation_result.supplier_id is None:
        raise ValueError("AllocationResult.supplier_id cannot be empty.")

    if delivery_result.supplier_id is None:
        raise ValueError("DeliveryResult.supplier_id cannot be empty.")

    try:
        allocated_quantity = float(allocation_result.allocated_quantity)
        delivered_quantity = float(delivery_result.quantity)
    except (TypeError, ValueError) as exc:
        raise ValueError("Allocation and delivery quantities must be numeric.") from exc

    if not math.isfinite(allocated_quantity) or not math.isfinite(delivered_quantity):
        raise ValueError("Allocation and delivery quantities must be finite.")

    if allocated_quantity <= 0:
        raise ValueError("Allocated quantity must be greater than zero.")

    if delivered_quantity < 0:
        raise ValueError("Delivered quantity cannot be negative.")

    if not delivery_result.status:
        raise ValueError("DeliveryResult.status cannot be empty.")


def _normalise_status(status: str) -> str:
    value = str(status).strip().upper().replace(" ", "_")
    if value == "IN_TRANSIT":
        return "DISPATCHED"
    return value


def create_verification_task(
    allocation_result: AllocationResult,
    delivery_result: DeliveryResult,
) -> Task:
    """
    Create a deterministic delivery-verification task.

    Verification is successful only when:
    - allocation and delivery refer to the same tank,
    - supplier IDs match,
    - delivery status is DELIVERED, and
    - quantities match within the application's 0.01-unit tolerance.
    """
    _validate_inputs(allocation_result, delivery_result)

    allocated_quantity = float(allocation_result.allocated_quantity)
    delivered_quantity = float(delivery_result.quantity)
    discrepancy = allocated_quantity - delivered_quantity

    quantity_matches = abs(discrepancy) <= QUANTITY_TOLERANCE
    supplier_matches = (
        str(delivery_result.supplier_id) == str(allocation_result.supplier_id)
    )
    delivery_status = _normalise_status(delivery_result.status)
    delivery_completed = delivery_status == "DELIVERED"

    verified = (
        quantity_matches
        and supplier_matches
        and delivery_completed
    )

    verification_status = "VERIFIED" if verified else "REVIEW_REQUIRED"

    agent = create_verification_agent()

    if verified:
        deterministic_reason = (
            "The delivery is marked DELIVERED, the supplier matches the approved "
            "supplier, and the delivered quantity matches the approved quantity "
            f"within the {QUANTITY_TOLERANCE:g}-unit tolerance."
        )
    else:
        problems = []
        if not delivery_completed:
            problems.append(f"delivery status is {delivery_status}")
        if not supplier_matches:
            problems.append("supplier ID does not match the approved supplier")
        if not quantity_matches:
            problems.append(
                f"quantity discrepancy is {discrepancy:.2f} units"
            )

        deterministic_reason = (
            "Verification failed because " + "; ".join(problems) + "."
        )

    description = f"""
Verify the following AquaSwarm water delivery.

Approved allocation:
- Tank ID: {allocation_result.tank_id}
- Allocated quantity: {allocated_quantity:g} units
- Supplier ID: {allocation_result.supplier_id}

Recorded delivery:
- Tank ID: {delivery_result.tank_id}
- Delivered quantity: {delivered_quantity:g} units
- Supplier ID: {delivery_result.supplier_id}
- Status: {delivery_result.status}

Deterministic verification checks:
- Same tank: {allocation_result.tank_id == delivery_result.tank_id}
- Same supplier: {supplier_matches}
- Delivery completed (DELIVERED): {delivery_completed}
- Quantity matches within {QUANTITY_TOLERANCE:g} units: {quantity_matches}
- Quantity discrepancy (approved - delivered): {discrepancy:.2f} units
- Verified: {verified}
- Verification status: {verification_status}

Deterministic conclusion:
{deterministic_reason}

Rules:
1. The deterministic checks above are authoritative.
2. Do not change the tank ID, supplier ID, delivered quantity, or verification result.
3. A DISPATCHED/In-Transit delivery is not verified.
4. A supplier mismatch is not verified.
5. A quantity mismatch greater than the tolerance is not verified.
6. Do not invent sensor readings, missing delivery quantities, or external evidence.
7. Do not claim that a failed verification is successful.
8. Explain the final result briefly using only the supplied facts.

Return a structured VerificationResult containing:
- tank_id: exactly the approved tank ID
- delivered_quantity: exactly the recorded delivered quantity
- verified: exactly {verified}
- discrepancy: exactly {discrepancy:.2f}
- status: exactly {verification_status}
- reasoning: concise evidence-based explanation
"""

    return Task(
        description=description,
        expected_output=f"""
A valid VerificationResult containing:
- tank_id: exactly "{allocation_result.tank_id}"
- delivered_quantity: exactly {delivered_quantity:g}
- verified: exactly {verified}
- discrepancy: exactly {discrepancy:.2f}
- status: exactly "{verification_status}"
- reasoning: concise explanation grounded only in the deterministic checks
""",
        agent=agent,
        output_pydantic=VerificationResult,
    )
