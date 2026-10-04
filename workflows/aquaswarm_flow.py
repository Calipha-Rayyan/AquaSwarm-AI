from crewai.flow.flow import Flow, start, listen, router
from pydantic import BaseModel

from models.schemas import (
    WaterData,
    DemandResult,
    AnomalyResult,
    SupplyResult,
    AllocationResult,
    ManagerApprovalResult,
    DeliveryResult,
    ReplanningResult,
    VerificationResult,
)

from agents.demand.agent import create_demand_agent
from agents.demand.task import create_demand_task

from agents.anomaly.agent import create_anomaly_agent
from agents.anomaly.task import create_anomaly_task

from agents.supply.agent import create_supply_agent
from agents.supply.task import create_supply_task

from agents.allocation.agent import create_allocation_agent
from agents.allocation.task import create_allocation_task

from agents.approval.agent import create_manager_approval_agent
from agents.approval.task import create_manager_approval_task

from agents.delivery.agent import create_delivery_agent
from agents.delivery.task import create_delivery_task

from agents.replanning.agent import create_replanning_agent
from agents.replanning.task import create_replanning_task

from agents.verification.agent import create_verification_agent
from agents.verification.task import create_verification_task


class AquaSwarmState(BaseModel):
    """State shared across the AquaSwarm workflow."""

    water_data: WaterData | None = None
    demand_result: DemandResult | None = None
    anomaly_result: AnomalyResult | None = None
    supply_result: SupplyResult | None = None
    allocation_result: AllocationResult | None = None
    manager_approval_result: ManagerApprovalResult | None = None
    replanning_result: ReplanningResult | None = None
    delivery_result: DeliveryResult | None = None
    verification_result: VerificationResult | None = None


class AquaSwarmFlow(Flow[AquaSwarmState]):

    @start()
    def initialize(self):
        """Initialize the workflow with water tank data."""

        self.state.water_data = WaterData(
            tank_id="TANK-001",
            current_level=30,
            capacity=100,
            daily_demand=80,
            inflow=10,
            timestamp="2026-10-03T18:00:00",
        )

        print("\n==============================")
        print("AQUASWARM FLOW STARTED")
        print("==============================")

        print(f"Tank ID: {self.state.water_data.tank_id}")
        print(f"Current Level: {self.state.water_data.current_level}")
        print(f"Daily Demand: {self.state.water_data.daily_demand}")
        print(f"Inflow: {self.state.water_data.inflow}")

    @listen(initialize)
    def analyze_demand(self):
        """Run the Demand Agent."""

        agent = create_demand_agent()
        task = create_demand_task()

        task.agent = agent

        from crewai import Crew, Process

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        self.state.demand_result = result.pydantic

        print("\nDemand Result:")
        print(self.state.demand_result)

    @listen(analyze_demand)
    def analyze_anomaly(self):
        """Run the Anomaly Agent."""

        agent = create_anomaly_agent()
        task = create_anomaly_task(
            self.state.water_data,
            self.state.demand_result,
        )

        task.agent = agent

        from crewai import Crew, Process

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        self.state.anomaly_result = result.pydantic

        print("\nAnomaly Result:")
        print(self.state.anomaly_result)

    @listen(analyze_anomaly)
    def analyze_supply(self):
        """Run the Supply Agent."""

        agent = create_supply_agent()
        task = create_supply_task(
            self.state.water_data,
            self.state.demand_result,
        )

        task.agent = agent

        from crewai import Crew, Process

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        self.state.supply_result = result.pydantic

        print("\nSupply Result:")
        print(self.state.supply_result)

    @listen(analyze_supply)
    def allocate_water(self):
        """Run the Allocation Agent."""

        agent = create_allocation_agent()
        task = create_allocation_task(
            self.state.demand_result,
            self.state.supply_result,
        )

        task.agent = agent

        from crewai import Crew, Process

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        self.state.allocation_result = result.pydantic

        print("\nAllocation Result:")
        print(self.state.allocation_result)

    @listen(allocate_water)
    def manager_approval(self):
        """Run the Manager Approval Agent."""

        agent = create_manager_approval_agent()
        task = create_manager_approval_task(
            self.state.allocation_result,
        )

        task.agent = agent

        from crewai import Crew, Process

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        self.state.manager_approval_result = result.pydantic

        print("\nManager Approval Result:")
        print(self.state.manager_approval_result)

    @router(manager_approval)
    def route_after_approval(self):
        """Route the workflow based on the manager's decision."""

        if self.state.manager_approval_result.approved:
            return "approved"

        return "rejected"

    @listen("approved")
    def arrange_delivery(self):
        """Run the Delivery Agent after Manager Approval."""

        agent = create_delivery_agent()
        task = create_delivery_task(
            self.state.allocation_result,
        )

        task.agent = agent

        from crewai import Crew, Process

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        self.state.delivery_result = result.pydantic

        print("\nDelivery Result:")
        print(self.state.delivery_result)

    @listen("rejected")
    def replan_water(self):
        """Run the Replanning Agent after Manager Rejection."""

        agent = create_replanning_agent()
        task = create_replanning_task(
            self.state.allocation_result,
            self.state.manager_approval_result,
        )

        task.agent = agent

        from crewai import Crew, Process

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        self.state.replanning_result = result.pydantic

        print("\nReplanning Result:")
        print(self.state.replanning_result)

    @listen(arrange_delivery)
    def verify_delivery(self):
        """Run the Verification Agent."""

        agent = create_verification_agent()
        task = create_verification_task(
            self.state.allocation_result,
            self.state.delivery_result,
        )

        task.agent = agent

        from crewai import Crew, Process

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        self.state.verification_result = result.pydantic

        print("\nVerification Result:")
        print(self.state.verification_result)

        print("\n==============================")
        print("AQUASWARM FLOW COMPLETED")
        print("==============================")


if __name__ == "__main__":
    flow = AquaSwarmFlow()
    flow.kickoff()