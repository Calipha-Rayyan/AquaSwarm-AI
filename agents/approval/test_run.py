from crewai import Crew, Process

from agents.approval.agent import create_manager_approval_agent
from agents.approval.task import create_manager_approval_task
from models.schemas import AllocationResult


def build_sample_allocation() -> AllocationResult:
    """Return a consistent sample allocation for a smoke test."""
    return AllocationResult(
        tank_id="TANK-001",
        allocated_quantity=2000,
        supplier_id=1,
        priority="HIGH",
        reasoning=(
            "The tank has a high-priority shortage and Supplier 1 is the "
            "recommended available source."
        ),
    )


def main():
    allocation_result = build_sample_allocation()

    agent = create_manager_approval_agent()
    task = create_manager_approval_task(allocation_result)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    print("\n==============================")
    print("APPROVAL REVIEW RESULT")
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
