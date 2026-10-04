from crewai import Task

from agents.orchestrator.agent import create_orchestrator_agent


def create_orchestrator_task() -> Task:
    agent = create_orchestrator_agent()

    return Task(
        description="""
        Coordinate the following AquaSwarm water management situation.

        Tank ID: TANK-001

        Demand Analysis:
        - Estimated demand: 80 units
        - Shortage: 40 units
        - Priority: High

        Anomaly Analysis:
        - Anomaly detected: Yes
        - Anomaly type: Insufficient water level relative to demand
        - Severity: High

        Supply Analysis:
        - Recommended supplier: S-001
        - Available quantity: 100 units
        - Distance: 15 km
        - Estimated cost: 500

        Allocation:
        - Allocated quantity: 40 units
        - Supplier: S-001
        - Priority: High

        Delivery:
        - Quantity: 40 units
        - Status: In Transit

        Verification:
        - Delivered quantity: 40 units
        - Verified: True
        - Discrepancy: 0 units
        - Status: Verified

        Based on all the information above:

        1. Summarize the overall situation.
        2. Determine the current workflow status.
        3. Identify whether further action is required.
        4. If further action is required, describe the next action.
        5. Explain the reasoning briefly.

        The workflow should move from analysis to allocation, delivery,
        verification, and finally determine whether replanning is necessary.
        """,
        expected_output="""
        A concise orchestration decision containing:
        - overall situation
        - workflow status
        - next action
        - whether replanning is required
        - reasoning
        """,
        agent=agent,
    )