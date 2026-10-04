import pandas as pd

from datetime import datetime, timezone

from crewai.flow import Flow, start, listen

from pydantic import BaseModel


# ============================================================
# MODELS
# ============================================================

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


# ============================================================
# AGENTS
# ============================================================

from agents.demand.agent import create_demand_agent
from agents.demand.task import create_demand_task

from agents.anomaly.agent import create_anomaly_agent
from agents.anomaly.task import create_anomaly_task

from agents.supply.agent import create_supply_agent
from agents.supply.task import create_supply_task

from agents.allocation.agent import create_allocation_agent
from agents.allocation.task import create_allocation_task

from agents.delivery.agent import create_delivery_agent
from agents.delivery.task import create_delivery_task

from agents.replanning.agent import create_replanning_agent
from agents.replanning.task import create_replanning_task

from agents.verification.agent import create_verification_agent
from agents.verification.task import create_verification_task


# ============================================================
# SHARED FLOW STATE
# ============================================================

class AquaSwarmState(BaseModel):
    """State shared across the AquaSwarm workflow."""

    # --------------------------------------------------------
    # OPERATION
    # --------------------------------------------------------

    selected_tank_id: str = "TANK-001"

    operation_status: str = "Pending"

    # --------------------------------------------------------
    # WATER DATA
    # --------------------------------------------------------

    water_data: WaterData | None = None

    # --------------------------------------------------------
    # AI AGENT RESULTS
    # --------------------------------------------------------

    demand_result: DemandResult | None = None

    anomaly_result: AnomalyResult | None = None

    supply_result: SupplyResult | None = None

    allocation_result: AllocationResult | None = None

    # --------------------------------------------------------
    # HUMAN APPROVAL
    # --------------------------------------------------------

    manager_approval_result: ManagerApprovalResult | None = None

    approval_required: bool = False

    approval_decided_by: str | None = None

    approval_decision_time: str | None = None

    approval_reason: str = ""

    # --------------------------------------------------------
    # DOWNSTREAM RESULTS
    # --------------------------------------------------------

    replanning_result: ReplanningResult | None = None

    delivery_result: DeliveryResult | None = None

    verification_result: VerificationResult | None = None


# ============================================================
# AQUASWARM FLOW
# ============================================================

class AquaSwarmFlow(Flow[AquaSwarmState]):

    # ========================================================
    # INITIALIZE
    # ========================================================

    @start()
    def initialize(self):
        """Load the selected water tank from the CSV dataset."""

        data = pd.read_csv(
            "data/sample_water_data.csv"
        )

        selected_rows = data[
            data["tank_id"]
            == self.state.selected_tank_id
        ]

        if selected_rows.empty:
            raise ValueError(
                f"Tank {self.state.selected_tank_id} "
                "was not found in "
                "data/sample_water_data.csv."
            )

        row = selected_rows.iloc[0]

        self.state.water_data = WaterData(
            tank_id=str(row["tank_id"]),
            current_level=float(
                row["current_level"]
            ),
            capacity=float(
                row["capacity"]
            ),
            daily_demand=float(
                row["daily_demand"]
            ),
            inflow=float(
                row["inflow"]
            ),
            timestamp=str(
                row["timestamp"]
            ),
        )

        print("\n==============================")
        print("AQUASWARM FLOW STARTED")
        print("==============================")

        print(
            f"Selected Tank: "
            f"{self.state.selected_tank_id}"
        )

        print(
            f"Tank ID: "
            f"{self.state.water_data.tank_id}"
        )

        print(
            f"Current Level: "
            f"{self.state.water_data.current_level}"
        )

        print(
            f"Daily Demand: "
            f"{self.state.water_data.daily_demand}"
        )

        print(
            f"Inflow: "
            f"{self.state.water_data.inflow}"
        )

    # ========================================================
    # DEMAND AGENT
    # ========================================================

    @listen(initialize)
    def analyze_demand(self):
        """Run the Demand Agent."""

        agent = create_demand_agent()

        task = create_demand_task(
            self.state.water_data,
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

        self.state.demand_result = (
            result.pydantic
        )

        print("\nDemand Result:")
        print(self.state.demand_result)

    # ========================================================
    # DEMAND ROUTER
    # ========================================================

    from crewai.flow import router

    @router(analyze_demand)
    def route_after_demand(self):
        """
        Decide whether water replenishment
        is required.
        """

        if (
            self.state.demand_result
            and self.state.demand_result.shortage > 0
        ):
            return "replenishment_required"

        return "no_replenishment"

    # ========================================================
    # NO REPLENISHMENT
    # ========================================================

    @listen("no_replenishment")
    def no_replenishment_required(self):
        """
        Stop procurement when the tank has
        sufficient water.
        """

        self.state.operation_status = (
            "No Replenishment Required"
        )

        print("\n==============================")
        print("NO REPLENISHMENT REQUIRED")
        print("==============================")

        print(
            f"Tank "
            f"{self.state.water_data.tank_id} "
            "has sufficient water."
        )

        print(
            f"Current Level: "
            f"{self.state.water_data.current_level}"
        )

        print(
            f"Daily Demand: "
            f"{self.state.water_data.daily_demand}"
        )

        print(
            f"Shortage: "
            f"{self.state.demand_result.shortage}"
        )

    # ========================================================
    # ANOMALY AGENT
    # ========================================================

    @listen("replenishment_required")
    def analyze_anomaly(self):
        """Run the Anomaly Agent."""

        self.state.operation_status = (
            "Replenishment Required"
        )

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

        self.state.anomaly_result = (
            result.pydantic
        )

        print("\nAnomaly Result:")
        print(self.state.anomaly_result)

    # ========================================================
    # SUPPLY AGENT
    # ========================================================

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

        self.state.supply_result = (
            result.pydantic
        )

        print("\nSupply Result:")
        print(self.state.supply_result)

    # ========================================================
    # ALLOCATION AGENT
    # ========================================================

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

        self.state.allocation_result = (
            result.pydantic
        )

        print("\nAllocation Result:")
        print(self.state.allocation_result)

    # ========================================================
    # HUMAN MANAGER APPROVAL
    # ========================================================

    @listen(allocate_water)
    def request_manager_approval(self):
        """
        Pause the operational workflow and wait
        for a real human manager decision.
        """

        self.state.operation_status = (
            "Awaiting Manager Approval"
        )

        self.state.approval_required = True

        self.state.manager_approval_result = None

        self.state.approval_decided_by = None

        self.state.approval_decision_time = None

        self.state.approval_reason = ""

        print("\n==============================")
        print("HUMAN APPROVAL REQUIRED")
        print("==============================")

        print(
            f"Tank: "
            f"{self.state.allocation_result.tank_id}"
        )

        print(
            f"Proposed Quantity: "
            f"{self.state.allocation_result.allocated_quantity}"
        )

        print(
            f"Supplier: "
            f"{self.state.allocation_result.supplier_id}"
        )

        print(
            f"Priority: "
            f"{self.state.allocation_result.priority}"
        )

        print(
            "\nWaiting for manager decision..."
        )

    # ========================================================
    # HUMAN DECISION
    # ========================================================

    def manager_decision(
        self,
        approved: bool,
        decided_by: str,
        reason: str = "",
    ):
        """
        Process the final human manager decision.

        This method is intentionally NOT a CrewAI
        listener. Streamlit will call this method
        after the manager presses Approve or Reject.
        """

        if not self.state.approval_required:
            raise ValueError(
                "No manager approval is currently pending."
            )

        if self.state.allocation_result is None:
            raise ValueError(
                "No allocation is available for approval."
            )

        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        decision_time = (
            datetime.now(timezone.utc)
            .isoformat()
        )

        # ----------------------------------------------------
        # DECISION TEXT
        # ----------------------------------------------------

        decision = (
            "Approved"
            if approved
            else "Rejected"
        )

        default_reason = (
            "Approved by the water operations manager."
            if approved
            else "Rejected by the water operations manager."
        )

        final_reason = (
            reason.strip()
            if reason and reason.strip()
            else default_reason
        )

        # ----------------------------------------------------
        # SAVE HUMAN DECISION
        # ----------------------------------------------------

        self.state.manager_approval_result = (
            ManagerApprovalResult(
                tank_id=(
                    self.state
                    .allocation_result
                    .tank_id
                ),
                approved=approved,
                manager_decision=decision,
                reasoning=final_reason,
            )
        )

        self.state.approval_required = False

        self.state.approval_decided_by = (
            decided_by
        )

        self.state.approval_decision_time = (
            decision_time
        )

        self.state.approval_reason = (
            final_reason
        )

        # ====================================================
        # APPROVED
        # ====================================================

        if approved:

            self.state.operation_status = (
                "Manager Approved"
            )

            print("\n==============================")
            print("MANAGER APPROVED")
            print("==============================")

            print(
                f"Approved By: {decided_by}"
            )

            print(
                f"Decision Time: "
                f"{decision_time}"
            )

            print(
                f"Reason: {final_reason}"
            )

            # ------------------------------------------------
            # DELIVERY
            # ------------------------------------------------

            self.arrange_delivery()

            # ------------------------------------------------
            # VERIFICATION
            # ------------------------------------------------

            self.verify_delivery()

        # ====================================================
        # REJECTED
        # ====================================================

        else:

            self.state.operation_status = (
                "Manager Rejected"
            )

            print("\n==============================")
            print("MANAGER REJECTED")
            print("==============================")

            print(
                f"Rejected By: {decided_by}"
            )

            print(
                f"Decision Time: "
                f"{decision_time}"
            )

            print(
                f"Reason: {final_reason}"
            )

            # ------------------------------------------------
            # REPLANNING
            # ------------------------------------------------

            self.replan_water()

        return self.state

    # ========================================================
    # DELIVERY AGENT
    # ========================================================

    def arrange_delivery(self):
        """
        Run the Delivery Agent only after
        human manager approval.
        """

        if (
            self.state.manager_approval_result
            is None
            or not self.state.manager_approval_result.approved
        ):
            raise ValueError(
                "Delivery cannot be arranged "
                "without human manager approval."
            )

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

        self.state.delivery_result = (
            result.pydantic
        )

        print("\nDelivery Result:")
        print(self.state.delivery_result)

    # ========================================================
    # REPLANNING AGENT
    # ========================================================

    def replan_water(self):
        """
        Run the Replanning Agent after
        human manager rejection.
        """

        if (
            self.state.manager_approval_result
            is None
            or self.state.manager_approval_result.approved
        ):
            raise ValueError(
                "Replanning is only allowed "
                "after manager rejection."
            )

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

        self.state.replanning_result = (
            result.pydantic
        )

        print("\nReplanning Result:")
        print(self.state.replanning_result)

    # ========================================================
    # VERIFICATION AGENT
    # ========================================================

    def verify_delivery(self):
        """
        Run the Verification Agent after
        the Delivery Agent has completed.
        """

        if self.state.delivery_result is None:
            raise ValueError(
                "Verification cannot run because "
                "no delivery result exists."
            )

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

        self.state.verification_result = (
            result.pydantic
        )

        print("\nVerification Result:")
        print(self.state.verification_result)

        print("\n==============================")
        print("AQUASWARM FLOW COMPLETED")
        print("==============================")


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    flow = AquaSwarmFlow()

    flow.kickoff(
        inputs={
            "selected_tank_id": "TANK-001"
        }
    )

    print("\n==============================")
    print("FLOW PAUSED FOR HUMAN APPROVAL")
    print("==============================")

    print(
        "\nCurrent Operation Status:"
    )

    print(
        flow.state.operation_status
    )

    print(
        "\nApproval Required:"
    )

    print(
        flow.state.approval_required
    )

