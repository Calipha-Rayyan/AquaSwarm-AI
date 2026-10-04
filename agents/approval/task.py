from crewai import Task

from agents.approval.agent import create_manager_approval_agent
from models.schemas import AllocationResult, ManagerApprovalResult


def create_manager_approval_task(
    allocation_result: AllocationResult,
) -> Task:
    agent = create_manager_approval_agent()

    return Task(
        description=f"""
        Review the following proposed water allocation.

        Tank ID: {allocation_result.tank_id}

        Proposed allocation:
        Quantity: {allocation_result.allocated_quantity} units
        Supplier ID: {allocation_result.supplier_id}
        Priority: {allocation_result.priority}

        Allocation reasoning:
        {allocation_result.reasoning}

        Review the allocation and determine whether it should be approved
        for delivery.

        Consider:
        1. The allocated quantity
        2. The selected supplier
        3. The priority level
        4. The allocation reasoning

        If the allocation is reasonable and appropriate, approve it.
        Otherwise, reject it.

        Provide a brief and reasonable explanation for the decision.

        Return the decision as a structured ManagerApprovalResult.
        """,
        expected_output="""
        A ManagerApprovalResult containing:
        - tank_id
        - approved
        - manager_decision
        - reasoning
        """,
        agent=agent,
        output_pydantic=ManagerApprovalResult,
    )