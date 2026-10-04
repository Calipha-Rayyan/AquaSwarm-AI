from crewai import Crew, Process

from agents.supply.agent import create_supply_agent
from agents.supply.task import create_supply_task


def main():
    # Standalone smoke-test data. The production workflow should normally pass
    # supplier records from the AquaSwarm backend.
    water_data = {
        "tank_id": "TANK-001",
        "current_level": 3000,
        "capacity": 10000,
        "daily_demand": 2500,
        "inflow": 500,
        "timestamp": "2026-10-04T10:00:00+00:00",
    }

    demand_result = {
        "tank_id": "TANK-001",
        "estimated_demand": 2500,
        "shortage": 2000,
        "priority": "HIGH",
        "reasoning": "Current tank level is insufficient for the stated demand.",
    }

    suppliers = [
        {
            "supplier_code": "S-001",
            "name": "Water Tanker A",
            "capacity": 8000,
            "available": 1,
            "distance_km": 15,
            "estimated_cost": 500,
            "eta_minutes": 40,
        },
        {
            "supplier_code": "S-002",
            "name": "Water Tanker B",
            "capacity": 12000,
            "available": 1,
            "distance_km": 20,
            "estimated_cost": 600,
            "eta_minutes": 50,
        },
        {
            "supplier_code": "S-003",
            "name": "Water Tanker C",
            "capacity": 10000,
            "available": 0,
            "distance_km": 5,
            "estimated_cost": 350,
            "eta_minutes": 25,
        },
    ]

    # SimpleNamespace keeps this smoke test independent of the exact Pydantic
    # model implementation while providing the attributes expected by the task.
    from types import SimpleNamespace

    water_data_obj = SimpleNamespace(**water_data)
    demand_result_obj = SimpleNamespace(**demand_result)

    agent = create_supply_agent()
    task = create_supply_task(
        water_data=water_data_obj,
        demand_result=demand_result_obj,
        suppliers=suppliers,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\n==============================")
    print("RUNNING SUPPLY AGENT")
    print("==============================")

    result = crew.kickoff()

    print("\n==============================")
    print("SUPPLY AGENT RESULT")
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
