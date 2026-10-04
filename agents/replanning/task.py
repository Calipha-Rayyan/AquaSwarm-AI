from crewai import Task

from agents.replanning.agent import create_replanning_agent
from models.schemas import AllocationResult, ManagerApprovalResult, ReplanningResult


_ALLOWED_ACTIONS = {
    "REPLAN_ALLOCATION",
    "REVIEW_SUPPLIER",
    "REVIEW_QUANTITY",
    "REQUEST_NEW_APPROVAL",
}


def _validate_inputs(
    allocation_result: AllocationResult,
    manager_approval_result: ManagerApprovalResult,
) -> None:
    """Validate that the replanning task is being triggered by a rejection."""
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

    if not manager_approval_result.reasoning:
        raise ValueError("ManagerApprovalResult.reasoning cannot be empty.")

    if manager_approval_result.tank_id != allocation_result.tank_id:
        raise ValueError(
            "AllocationResult and ManagerApprovalResult must refer to the same tank."
        )

    if manager_approval_result.approved is True:
        raise ValueError(
            "Replanning should not run for an approved allocation. "
            "Use replanning only after a rejection."
        )

    decision = str(manager_approval_result.manager_decision).strip().upper()
    if decision not in {"REJECT", "REJECTED"}:
        raise ValueError(
            "Replanning requires a rejected manager decision. "
            f"Received: {manager_approval_result.manager_decision!r}"
        )


def create_replanning_task(
    allocation_result: AllocationResult,
    manager_approval_result: ManagerApprovalResult,
) -> Task:
    """
    Create a recovery-planning task from the actual allocation and manager decision.

    The LLM recommends one action. It does not execute the new allocation or
    automatically authorize a new physical delivery.
    """
    _validate_inputs(allocation_result, manager_approval_result)

    agent = create_replanning_agent()

    return Task(
        description=f"""
Analyze the rejected AquaSwarm water allocation below and recommend the next
replanning action.

Allocation under review:
- Tank ID: {allocation_result.tank_id}
- Quantity: {allocation_result.allocated_quantity} units
- Supplier ID: {allocation_result.supplier_id}
- Priority: {allocation_result.priority}
- Allocation reasoning: {allocation_result.reasoning}

Human manager decision:
- Approved: {manager_approval_result.approved}
- Decision: {manager_approval_result.manager_decision}
- Reasoning: {manager_approval_result.reasoning}

Select exactly one next action from:
- REPLAN_ALLOCATION
- REVIEW_SUPPLIER
- REVIEW_QUANTITY
- REQUEST_NEW_APPROVAL

Decision guidance:
- REVIEW_SUPPLIER: use when the rejection reason points to a supplier problem
  or the selected supplier should be reconsidered.
- REVIEW_QUANTITY: use when the rejection reason points to the requested amount
  or allocation size.
- REPLAN_ALLOCATION: use when the overall allocation needs to be redesigned or
  the rejection reason does not fit a narrower supplier/quantity review.
- REQUEST_NEW_APPROVAL: use only when the allocation has been sufficiently
  revised and the next step is to send the revised proposal back to the manager.
- Base the choice only on the manager's stated reason and supplied allocation.
- Do not invent missing supplier capacity, cost, distance, tank data, or policy.
- Do not modify the original allocation values in the output.
- Do not perform the new allocation, delivery, or approval yourself.
- Do not claim the new plan is approved.

Return a structured ReplanningResult containing:
- tank_id: exactly the original tank ID
- action: exactly one allowed action
- reason: a concise explanation grounded in the manager decision
""",
        expected_output="""
A valid ReplanningResult containing:
- tank_id
- action
- reason

The action must be exactly one of:
REPLAN_ALLOCATION, REVIEW_SUPPLIER, REVIEW_QUANTITY, REQUEST_NEW_APPROVAL.

The tank_id must exactly match the AllocationResult.
""",
        agent=agent,
        output_pydantic=ReplanningResult,
    )
