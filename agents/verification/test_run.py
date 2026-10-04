from crewai import Crew, Process
from types import SimpleNamespace

from agents.verification.agent import create_verification_agent
from agents.verification.task import create_verification_task


def build_sample_results():
    """Return a successful delivery scenario for a verification smoke test."""
    allocation_result = SimpleNamespace(
        tank_id="TANK-001",
        allocated_quantity=2000.0,
        supplier_id="S-001",
        priority="HIGH",
        reasoning="Approved allocation to cover the identified shortage.",
    )

    delivery_result = SimpleNamespace(
        tank_id="TANK-001",
        supplier_id="S-001",
        quantity=2000.0,
        status="DELIVERED",
        estimated_arrival="2026-10-04T16:45:00+00:00",
    )

    return allocation_result, delivery_result


def main():
    allocation_result, delivery_result = build_sample_results()

    agent = create_verification_agent()
    task = create_verification_task(
        allocation_result=allocation_result,
        delivery_result=delivery_result,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\n==============================")
    print("RUNNING VERIFICATION AGENT")
    print("==============================")

    result = crew.kickoff()

    print("\n==============================")
    print("VERIFICATION AGENT RESULT")
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
