from crewai import Task

from agents.verification.agent import create_verification_agent
from models.schemas import VerificationResult, AllocationResult, DeliveryResult


def create_verification_task(
    allocation_result: AllocationResult,
    delivery_result: DeliveryResult,
) -> Task:
    agent = create_verification_agent()

    quantity_matches = (
        delivery_result.quantity == allocation_result.allocated_quantity
    )

    delivery_completed = (
        delivery_result.status.lower() == "delivered"
    )

    verified = quantity_matches and delivery_completed

    discrepancy = (
        allocation_result.allocated_quantity - delivery_result.quantity
    )

    verification_status = "Verified" if verified else "Pending"

    return Task(
        description=f"""
        Verify the following water delivery:

        Tank ID: {allocation_result.tank_id}

        Approved allocation:
        Quantity: {allocation_result.allocated_quantity} units
        Supplier ID: {allocation_result.supplier_id}

        Actual delivery:
        Quantity: {delivery_result.quantity} units
        Supplier ID: {delivery_result.supplier_id}
        Status: {delivery_result.status}

        Deterministic verification checks:

        Quantity matches approved allocation:
        {quantity_matches}

        Delivery has been completed:
        {delivery_completed}

        Deterministic verification result:
        Verified: {verified}

        Discrepancy:
        {discrepancy} units

        Verification status:
        {verification_status}

        Verification rules:

        1. The delivered quantity must match the approved allocation.
        2. The delivery status must be "Delivered".
        3. Both conditions must be satisfied before the delivery
           can be marked as verified.

        Use the deterministic verification results above as
        authoritative.

        Do not mark an "In Transit" delivery as verified.

        Provide a brief reasoning explaining the verification result.

        Return the result as a structured VerificationResult.
        """,
        expected_output="""
        A VerificationResult containing:
        - tank_id
        - delivered_quantity
        - verified
        - discrepancy
        - status
        - reasoning
        """,
        agent=agent,
        output_pydantic=VerificationResult,
    )