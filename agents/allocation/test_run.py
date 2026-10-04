from crewai import Crew, Process

from agents.allocation.agent import create_allocation_agent
from agents.allocation.task import create_allocation_task
from models.schemas import (
    DemandResult,
    SupplyOption,
    SupplyResult,
)


def build_sample_results():
    """Build realistic upstream results for an allocation-agent smoke test."""
    demand_result = DemandResult(
        tank_id="TANK-001",
        estimated_demand=5000.0,
        shortage=2000.0,
        priority="HIGH",
        reasoning=(
            "The tank has insufficient water for the expected demand, "
            "so replenishment is required."
        ),
    )

    supply_result = SupplyResult(
        tank_id="TANK-001",
        suppliers=[
            SupplyOption(
                supplier_id="S-001",
                available_quantity=10000.0,
                distance_km=15.0,
                estimated_cost=5000.0,
            ),
            SupplyOption(
                supplier_id="S-002",
                available_quantity=6000.0,
                distance_km=8.0,
                estimated_cost=6000.0,
            ),
            SupplyOption(
                supplier_id="S-003",
                available_quantity=3000.0,
                distance_km=5.0,
                estimated_cost=3500.0,
            ),
        ],
        recommended_supplier="S-001",
        reasoning=(
            "S-001 can fulfill the required quantity and was selected "
            "by the Supply Agent."
        ),
    )

    return demand_result, supply_result


def main():
    demand_result, supply_result = build_sample_results()

    agent = create_allocation_agent()
    task = create_allocation_task(
        demand_result=demand_result,
        supply_result=supply_result,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\n==============================")
    print("RUNNING ALLOCATION AGENT")
    print("==============================")

    result = crew.kickoff()

    print("\n==============================")
    print("ALLOCATION AGENT RESULT")
    print("==============================")

    # CrewAI exposes structured output through result.pydantic when the task
    # uses output_pydantic.
    if getattr(result, "pydantic", None) is not None:
        print(result.pydantic.model_dump())
    else:
        print(result)


if __name__ == "__main__":
    main()
