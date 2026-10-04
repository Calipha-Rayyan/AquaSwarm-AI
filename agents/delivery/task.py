from crewai import Task

from agents.delivery.agent import create_delivery_agent
from models.schemas import DeliveryResult, AllocationResult


def create_delivery_task(
    allocation_result: AllocationResult,
) -> Task:
    agent = create_delivery_agent()

    delivery_quantity = allocation_result.allocated_quantity
    supplier_id = allocation_result.supplier_id
    delivery_status = "In Transit"

    return Task(
        description=f"""
        Coordinate the following approved water delivery:

        Tank ID: {allocation_result.tank_id}
        Supplier ID: {supplier_id}
        Allocated quantity: {delivery_quantity} units
        Priority: {allocation_result.priority}

        Deterministic delivery information:

        Delivery quantity:
        {delivery_quantity} units

        Supplier:
        {supplier_id}

        Delivery status:
        {delivery_status}

        These values are authoritative.

        The delivery has been approved and dispatched.
        The delivery is currently in transit.

        Provide:
        1. The estimated arrival time
        2. Brief reasoning about the delivery status

        Do not change:
        - the delivery quantity
        - the supplier ID
        - the delivery status

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