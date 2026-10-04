from crewai import Task

from agents.delivery.agent import create_delivery_agent
from models.schemas import DeliveryResult, AllocationResult


def create_delivery_task(
    allocation_result: AllocationResult,
) -> Task:
    agent = create_delivery_agent()

    return Task(
        description=f"""
        Coordinate the following water delivery:

        Tank ID: {allocation_result.tank_id}
        Supplier ID: {allocation_result.supplier_id}
        Allocated quantity: {allocation_result.allocated_quantity} units
        Priority: {allocation_result.priority}

        The delivery has been approved for dispatch.

        Determine:
        1. Delivery quantity
        2. Supplier
        3. Delivery status
        4. Estimated arrival time

        Use the actual Allocation Agent result provided above.

        Assume the delivery is successfully dispatched and is currently
        in transit. Provide a realistic estimated arrival time.

        Return the result as a structured DeliveryResult.
        """,
        expected_output="""
        A DeliveryResult containing:
        - tank_id
        - supplier_id
        - quantity
        - status
        - estimated_arrival
        """,
        agent=agent,
        output_pydantic=DeliveryResult,
    )