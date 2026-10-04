from crewai import Task

from agents.verification.agent import create_verification_agent
from models.schemas import VerificationResult, AllocationResult, DeliveryResult


def create_verification_task(
    allocation_result: AllocationResult,
    delivery_result: DeliveryResult,
) -> Task:
    agent = create_verification_agent()

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

        Determine:
        1. The delivered quantity
        2. Whether the delivery is verified
        3. Any discrepancy between approved and delivered quantity
        4. Verification status
        5. Brief reasoning

        The delivery should be considered verified if the actual delivered
        quantity matches the approved allocation.

        Use the actual Allocation Agent and Delivery Agent results provided above.

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