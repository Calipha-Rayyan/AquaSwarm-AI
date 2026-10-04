from crewai import Task

from agents.replanning.agent import create_replanning_agent
from models.schemas import AllocationResult, ManagerApprovalResult, ReplanningResult


def create_replanning_task(
    allocation_result: AllocationResult,
    manager_approval_result: ManagerApprovalResult,
) -> Task:
    agent = create_replanning_agent()

    return Task(
        description=f"""
        Reassess the following rejected water allocation.

        Tank ID: {allocation_result.tank_id}

        Proposed allocation:
        Quantity: {allocation_result.allocated_quantity} units
        Supplier ID: {allocation_result.supplier_id}
        Priority: {allocation_result.priority}

        Manager decision:
        Approved: {manager_approval_result.approved}
        Decision: {manager_approval_result.manager_decision}
        Reasoning: {manager_approval_result.reasoning}

        Determine the next appropriate action after the rejection.

        Possible actions include:
        - REPLAN_ALLOCATION
        - REVIEW_SUPPLIER
        - REVIEW_QUANTITY
        - REQUEST_NEW_APPROVAL

        Provide a brief reason for the selected action.

        Return the result as a structured ReplanningResult.
        """,
        expected_output="""
        A ReplanningResult containing:
        - tank_id
        - action
        - reason
        """,
        agent=agent,
        output_pydantic=ReplanningResult,
    )