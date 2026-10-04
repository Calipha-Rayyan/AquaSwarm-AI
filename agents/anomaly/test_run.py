from crewai import Crew, Process

from agents.anomaly.agent import create_anomaly_agent
from agents.anomaly.task import create_anomaly_task
from models.schemas import WaterData, DemandResult


def build_sample_inputs():
    """Return consistent sample inputs for a smoke test."""
    water_data = WaterData(
        tank_id="TANK-001",
        current_level=3000,
        capacity=10000,
        daily_demand=2500,
        inflow=500,
        timestamp="2026-10-04T10:00:00+00:00",
    )

    demand_result = DemandResult(
        tank_id="TANK-001",
        estimated_demand=2500,
        shortage=2000,
        priority="HIGH",
        reasoning="Expected demand exceeds available water for the operating period.",
    )

    return water_data, demand_result


def main():
    water_data, demand_result = build_sample_inputs()

    # Explicitly validate task construction before calling CrewAI.
    agent = create_anomaly_agent()
    task = create_anomaly_task(water_data, demand_result)

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    print("\n==============================")
    print("ANOMALY AGENT RESULT")
    print("==============================")

    if getattr(result, "pydantic", None) is not None:
        print(result.pydantic.model_dump())
    else:
        print(result)


if __name__ == "__main__":
    main()
