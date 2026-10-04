from crewai import Crew, Process

from agents.orchestrator.agent import create_orchestrator_agent
from agents.orchestrator.task import create_orchestrator_task


def main():
    # Representative upstream results for a smoke test.
    demand_result = {
        "tank_id": "TANK-001",
        "estimated_demand": 2500,
        "shortage": 2000,
        "priority": "HIGH",
        "reasoning": "Current water level is insufficient for the stated demand.",
    }

    anomaly_result = {
        "tank_id": "TANK-001",
        "anomaly_detected": True,
        "anomaly_type": "LOW_WATER_LEVEL",
        "severity": "HIGH",
        "reasoning": "Tank is operating at a low fill percentage.",
    }

    supply_result = {
        "recommended_supplier": "S-001",
        "available_quantity": 5000,
        "distance_km": 15,
        "estimated_cost": 500,
    }

    allocation_result = {
        "tank_id": "TANK-001",
        "allocated_quantity": 2000,
        "supplier_id": "S-001",
        "priority": "HIGH",
        "reasoning": "Allocation covers the reported shortage.",
    }

    approval_result = {
        "tank_id": "TANK-001",
        "approved": True,
        "manager_decision": "APPROVE",
        "reasoning": "Allocation is consistent with the supplied shortage.",
    }

    delivery_result = {
        "tank_id": "TANK-001",
        "supplier_id": "S-001",
        "quantity": 2000,
        "status": "DISPATCHED",
        "estimated_arrival": "2026-10-04T16:45:00+00:00",
    }

    verification_result = None

    agent = create_orchestrator_agent()
    task = create_orchestrator_task(
        demand_result=demand_result,
        anomaly_result=anomaly_result,
        supply_result=supply_result,
        allocation_result=allocation_result,
        approval_result=approval_result,
        delivery_result=delivery_result,
        verification_result=verification_result,
        workflow_status="DELIVERY_IN_PROGRESS",
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    print("\n==============================")
    print("RUNNING ORCHESTRATOR AGENT")
    print("==============================")

    result = crew.kickoff()

    print("\n==============================")
    print("ORCHESTRATOR AGENT RESULT")
    print("==============================")
    print(result)


if __name__ == "__main__":
    main()
