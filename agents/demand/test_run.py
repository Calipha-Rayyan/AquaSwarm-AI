from crewai import Crew, Process

from agents.demand.agent import create_demand_agent
from agents.demand.task import create_demand_task
from models.schemas import WaterData


def build_sample_water_data() -> WaterData:
    """Return a consistent sample record for a demand-agent smoke test."""
    return WaterData(
        tank_id="TANK-001",
        current_level=3000,
        capacity=10000,
        daily_demand=2500,
        inflow=500,
        timestamp="2026-10-04T10:00:00+00:00",
    )


def main():
    water_data = build_sample_water_data()

    agent = create_demand_agent()
    task = create_demand_task(water_data)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\n==============================")
    print("RUNNING DEMAND AGENT")
    print("==============================")

    result = crew.kickoff()

    print("\n==============================")
    print("DEMAND AGENT RESULT")
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
