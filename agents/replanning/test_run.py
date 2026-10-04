from crewai import Crew, Process
from types import SimpleNamespace

from agents.replanning.agent import create_replanning_agent
from agents.replanning.task import create_replanning_task


def build_sample_results():
    """
    Build a realistic rejected-allocation scenario.

    SimpleNamespace is used here so the smoke test stays independent of the
    exact Pydantic implementation in models/schemas.py while providing the
    same attributes required by the replanning task.
    """
    allocation_result = SimpleNamespace(
        tank_id="TANK-001",
        allocated_quantity=2000.0,
        supplier_id="S-001",
        priority="HIGH",
        reasoning=(
            "The allocation was designed to cover the identified shortage "
            "using supplier S-001."
        ),
    )

    manager_approval_result = SimpleNamespace(
        tank_id="TANK-001",
        approved=False,
        manager_decision="REJECT",
        reasoning=(
            "The selected supplier should be reviewed before the delivery "
            "can proceed."
        ),
    )

    return allocation_result, manager_approval_result


def main():
    allocation_result, manager_approval_result = build_sample_results()

    agent = create_replanning_agent()
    task = create_replanning_task(
        allocation_result=allocation_result,
        manager_approval_result=manager_approval_result,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\n==============================")
    print("RUNNING REPLANNING AGENT")
    print("==============================")

    result = crew.kickoff()

    print("\n==============================")
    print("REPLANNING AGENT RESULT")
    print("==============================")

    if getattr(result, "pydantic", None) is not None:
        model = result.pydantic
        if hasattr(model, "model_dump"):
            print(model.model_dump())
        else:
            print(model)
    else:
        print(result)


if __name__ == "__main__":
    main()
