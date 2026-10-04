from crewai import Crew, Process

from agents.delivery.agent import create_delivery_agent
from agents.delivery.task import create_delivery_task
from models.schemas import AllocationResult


def build_sample_allocation() -> AllocationResult:
    """Return a consistent approved allocation for a delivery smoke test."""
    return AllocationResult(
        tank_id="TANK-001",
        allocated_quantity=2000.0,
        supplier_id="S-001",
        priority="HIGH",
        reasoning=(
            "The tank has a high-priority shortage and S-001 was selected "
            "because it can provide the required allocation."
        ),
    )


def main():
    allocation_result = build_sample_allocation()

    agent = create_delivery_agent()
    task = create_delivery_task(
        allocation_result=allocation_result,
        eta_minutes=45,
        approval_confirmed=True,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\n==============================")
    print("RUNNING DELIVERY AGENT")
    print("==============================")

    result = crew.kickoff()

    print("\n==============================")
    print("DELIVERY AGENT RESULT")
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
