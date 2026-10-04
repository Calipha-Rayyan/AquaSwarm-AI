from typing import Any, Mapping, Optional

from crewai import Task

from agents.orchestrator.agent import create_orchestrator_agent


def _to_context(name: str, value: Any) -> str:
    """Convert an upstream result into readable, bounded orchestration context."""
    if value is None:
        return f"{name}: NOT_PROVIDED"

    if hasattr(value, "model_dump"):
        value = value.model_dump()
    elif hasattr(value, "dict"):
        value = value.dict()

    if isinstance(value, Mapping):
        fields = []
        for key, item in value.items():
            fields.append(f"- {key}: {item}")
        return f"{name}:\n" + ("\n".join(fields) if fields else "- EMPTY")

    return f"{name}:\n- {value}"


def create_orchestrator_task(
    demand_result: Optional[Any] = None,
    anomaly_result: Optional[Any] = None,
    supply_result: Optional[Any] = None,
    allocation_result: Optional[Any] = None,
    approval_result: Optional[Any] = None,
    delivery_result: Optional[Any] = None,
    verification_result: Optional[Any] = None,
    replanning_result: Optional[Any] = None,
    workflow_status: Optional[str] = None,
) -> Task:
    """
    Create a workflow-summary task from real specialist-agent results.

    This task does not perform state transitions or physical actions. The
    application/CrewAI Flow remains the source of truth for orchestration.
    """
    results = {
        "Demand Analysis": demand_result,
        "Anomaly Analysis": anomaly_result,
        "Supply Analysis": supply_result,
        "Allocation": allocation_result,
        "Manager Approval": approval_result,
        "Delivery": delivery_result,
        "Verification": verification_result,
        "Replanning": replanning_result,
    }

    if not any(value is not None for value in results.values()) and workflow_status is None:
        raise ValueError(
            "At least one upstream result or workflow_status must be supplied "
            "to create the orchestrator task."
        )

    agent = create_orchestrator_agent()

    context_sections = [
        _to_context(name, value)
        for name, value in results.items()
    ]

    current_status = workflow_status or "NOT_EXPLICITLY_PROVIDED"

    description = f"""
Review the current AquaSwarm workflow using the supplied specialist-agent results.

Current workflow status:
- {current_status}

{"".join(section + chr(10) + chr(10) for section in context_sections)}

Your responsibility is to interpret the supplied information and produce a concise
orchestration recommendation.

Determine:
1. Overall situation.
2. Current workflow stage/status.
3. Next action required, if any.
4. Whether replanning is required.
5. Brief reasoning grounded only in the supplied results.

Workflow guidance:
- Normal high-level sequence:
  Observe → Demand → Anomaly/Supply → Allocation → Human Approval →
  Delivery → Verification → Replanning when necessary.
- A manager approval result is the authority for whether a critical delivery
  action may proceed. Do not infer approval when it was not supplied.
- Do not claim delivery is completed unless the supplied delivery/verification
  result explicitly supports completion.
- Do not invent quantities, supplier information, ETA, tank conditions,
  approval decisions, or verification measurements.
- Do not modify specialist-agent results.
- Do not directly execute physical actions or database state changes.
- If information is missing, state exactly what is missing.
- Replanning is required when verification fails, a delivery exception occurs,
  or the supplied results otherwise show that the original plan is no longer valid.

Return:
- overall_situation
- workflow_status
- next_action
- replanning_required
- reasoning
"""

    return Task(
        description=description,
        expected_output="""
A concise orchestration decision containing:
- overall_situation
- workflow_status
- next_action
- replanning_required
- reasoning

Use only facts present in the supplied workflow context.
""",
        agent=agent,
    )
