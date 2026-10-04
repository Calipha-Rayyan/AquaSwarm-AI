from crewai import Task

from agents.approval.agent import create_manager_approval_agent
from models.schemas import AllocationResult, ManagerApprovalResult


def _validate_allocation(allocation_result: AllocationResult) -> None:
    """Validate an allocation before sending it to the approval-review agent."""
    if not allocation_result.tank_id:
        raise ValueError("AllocationResult.tank_id cannot be empty.")

    if allocation_result.allocated_quantity <= 0:
        raise ValueError("Allocated quantity must be greater than zero.")

    if allocation_result.supplier_id is None:
        raise ValueError("AllocationResult.supplier_id cannot be empty.")

    if not allocation_result.priority:
        raise ValueError("AllocationResult.priority cannot be empty.")

    if not allocation_result.reasoning:
        raise ValueError("AllocationResult.reasoning cannot be empty.")

    allowed_priorities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    if str(allocation_result.priority).upper() not in allowed_priorities:
        raise ValueError(
            "Invalid priority. Expected one of: "
            + ", ".join(sorted(allowed_priorities))
        )


def create_manager_approval_task(
    allocation_result: AllocationResult,
) -> Task:
    """
    Create an approval-review task from the actual Allocation Agent result.

    The agent produces a recommendation. The final physical action must still
    be confirmed through the application's human-manager approval step.
    """
    _validate_allocation(allocation_result)

    agent = create_manager_approval_agent()

    priority = str(allocation_result.priority).upper()

    return Task(
        description=f"""
Review the following proposed AquaSwarm water allocation.

Proposed allocation:
- Tank ID: {allocation_result.tank_id}
- Quantity: {allocation_result.allocated_quantity} units
- Supplier ID: {allocation_result.supplier_id}
- Priority: {priority}

Allocation reasoning:
{allocation_result.reasoning}

Review the proposal for internal consistency and operational reasonableness.

Check:
1. The allocated quantity is positive.
2. The supplier selection is present and usable.
3. The priority is appropriate to the proposed action.
4. The reasoning supports the proposed allocation.
5. There is no obvious contradiction in the supplied information.

Decision guidance:
- Recommend approval when the supplied allocation is reasonable and supported.
- Recommend rejection when the supplied allocation is inconsistent, unsupported,
  unsafe, or clearly unreasonable.
- Do not invent supplier capacity, tank measurements, costs, or other facts that
  are not present in the Allocation Agent result.
- Do not change the tank_id or supplier_id.
- Treat "approved" as an AI recommendation for the human manager, not as
  authorization to perform physical delivery.

Return a structured ManagerApprovalResult with:
- tank_id: exactly the supplied tank ID
- approved: true for approval recommendation, false for rejection recommendation
- manager_decision: a concise decision such as "APPROVE" or "REJECT"
- reasoning: a brief explanation grounded only in the supplied allocation
""",
        expected_output="""
A valid ManagerApprovalResult containing:
- tank_id
- approved
- manager_decision
- reasoning

The tank_id must exactly match the AllocationResult.
The approval is a recommendation for the human manager; it is not by itself
authorization for physical delivery.
""",
        agent=agent,
        output_pydantic=ManagerApprovalResult,
    )
