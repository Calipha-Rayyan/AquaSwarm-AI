from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
from crewai import Crew, Process
from crewai.flow import Flow, listen, router, start
from pydantic import BaseModel

from agents.allocation.task import create_allocation_task
from agents.anomaly.task import create_anomaly_task
from agents.delivery.task import create_delivery_task
from agents.demand.task import create_demand_task
from agents.replanning.task import create_replanning_task
from agents.supply.task import create_supply_task
from agents.verification.task import create_verification_task
from models.schemas import (
    AllocationResult,
    AnomalyResult,
    DemandResult,
    DeliveryResult,
    ManagerApprovalResult,
    ReplanningResult,
    SupplyResult,
    VerificationResult,
    WaterData,
)
from config.settings import (
    AQUASWARM_BACKEND_ENABLED,
    AQUASWARM_BACKEND_URL,
    AQUASWARM_BACKEND_TIMEOUT,
    AQUASWARM_DEFAULT_INFLOW,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class AquaSwarmState(BaseModel):
    """State shared across one AquaSwarm operation."""

    selected_tank_id: str = "TANK-001"
    operation_status: str = "Pending"

    water_data: Optional[WaterData] = None
    demand_result: Optional[DemandResult] = None
    anomaly_result: Optional[AnomalyResult] = None
    supply_result: Optional[SupplyResult] = None
    allocation_result: Optional[AllocationResult] = None

    manager_approval_result: Optional[ManagerApprovalResult] = None
    approval_required: bool = False
    approval_decided_by: Optional[str] = None
    approval_decision_time: Optional[str] = None
    approval_reason: str = ""

    delivery_request_id: Optional[int] = None
    delivery_result: Optional[DeliveryResult] = None
    verification_result: Optional[VerificationResult] = None
    replanning_result: Optional[ReplanningResult] = None

    backend_sync_error: str = ""

    data_source: str = "Pending"


class AquaSwarmFlow(Flow[AquaSwarmState]):

    def _backend(self):
        if not AQUASWARM_BACKEND_ENABLED:
            return None

        from backend.client import BackendClient

        return BackendClient(
            base_url=AQUASWARM_BACKEND_URL,
            timeout=AQUASWARM_BACKEND_TIMEOUT,
        )

    @staticmethod
    def _crew_result(result, label: str):
        structured = getattr(result, "pydantic", None)
        if structured is None:
            raise RuntimeError(
                f"{label} did not return a structured Pydantic result."
            )
        return structured

    def _run_task(self, task, label: str):
        result = Crew(
            agents=[task.agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        ).kickoff()
        return self._crew_result(result, label)

    @staticmethod
    def _normalise_tank_code(value) -> str:
        """Normalize numeric CSV ids and API tank codes to TANK-###."""
        raw = str(value).strip()
        if raw.upper().startswith("TANK-"):
            suffix = raw.split("-", 1)[1]
            try:
                return f"TANK-{int(suffix):03d}"
            except ValueError:
                return raw.upper()
        try:
            return f"TANK-{int(float(raw)):03d}"
        except (TypeError, ValueError):
            return raw.upper()

    def _load_local_water_data(self, selected_tank: str) -> WaterData:
        """Load consistent demo data from tanks.csv + consumption.csv.

        This is the primary fallback when the FastAPI service is not running.
        It avoids the old mismatch where the selector used TANK-001 while the
        simulator file stored tank_id=1.
        """
        tanks_path = DATA_DIR / "tanks.csv"
        consumption_path = DATA_DIR / "consumption.csv"

        if tanks_path.exists():
            tanks = pd.read_csv(tanks_path)
            if "id" not in tanks.columns:
                raise ValueError("data/tanks.csv is missing the id column.")

            tank_rows = tanks[
                tanks["id"].apply(self._normalise_tank_code) == selected_tank
            ]
            if tank_rows.empty:
                raise ValueError(f"Tank {selected_tank} was not found in data/tanks.csv.")

            tank_row = tank_rows.iloc[0]
            site_id = int(tank_row["site_id"])
            daily_demand = 0.0

            if consumption_path.exists():
                consumption = pd.read_csv(consumption_path)
                if {"site_id", "amount"}.issubset(consumption.columns):
                    rows = consumption[consumption["site_id"].astype(int) == site_id].copy()
                    if not rows.empty:
                        if "timestamp" in rows.columns:
                            rows = rows.sort_values("timestamp", ascending=False)
                        daily_demand = float(rows.iloc[0]["amount"])

            self.state.data_source = "LOCAL CSV"
            return WaterData(
                tank_id=selected_tank,
                current_level=float(tank_row["current_level"]),
                capacity=float(tank_row["capacity"]),
                daily_demand=daily_demand,
                inflow=AQUASWARM_DEFAULT_INFLOW,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Last-resort compatibility with the simulator file.
        fallback = DATA_DIR / "sample_water_data.csv"
        if not fallback.exists():
            raise FileNotFoundError(
                f"No tank data source is available. Expected {tanks_path} "
                f"or {fallback}."
            )

        data = pd.read_csv(fallback)
        if "tank_id" not in data.columns:
            raise ValueError(f"{fallback} is missing the tank_id column.")
        selected_rows = data[
            data["tank_id"].apply(self._normalise_tank_code) == selected_tank
        ]
        if selected_rows.empty:
            raise ValueError(f"Tank {selected_tank} was not found in {fallback}.")

        row = selected_rows.iloc[0]
        self.state.data_source = "SIMULATOR CSV"
        return WaterData(
            tank_id=selected_tank,
            current_level=float(row["current_level"]),
            capacity=float(row["capacity"]),
            daily_demand=float(row["daily_demand"]),
            inflow=float(row["inflow"]),
            timestamp=str(row["timestamp"]),
        )

    @start()
    def initialize(self):
        """Load the selected tank from the API, with a fast local CSV fallback."""
        selected_tank = self._normalise_tank_code(self.state.selected_tank_id)
        self.state.selected_tank_id = selected_tank

        try:
            client = self._backend()
            if client is None:
                raise RuntimeError("Backend integration disabled.")

            tanks = client.get_tanks()
            tank = next(
                (row for row in tanks if self._normalise_tank_code(row.get("tank_code")) == selected_tank),
                None,
            )
            if tank is None:
                raise ValueError(f"Tank {selected_tank} was not found in the backend.")

            consumption = client.get_consumption(tank_code=selected_tank, limit=1)
            latest_consumption = float(consumption[0]["amount"]) if consumption else 0.0

            self.state.water_data = WaterData(
                tank_id=selected_tank,
                current_level=float(tank["current_level"]),
                capacity=float(tank["capacity"]),
                daily_demand=latest_consumption,
                inflow=AQUASWARM_DEFAULT_INFLOW,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self.state.data_source = "BACKEND API"
            self.state.backend_sync_error = ""

        except Exception as exc:
            # The API is optional for the local/hackathon UI. Fall back quickly
            # and deterministically to the canonical CSV data.
            try:
                self.state.water_data = self._load_local_water_data(selected_tank)
                self.state.backend_sync_error = (
                    "Backend API unavailable — using local CSV data."
                )
            except Exception as fallback_exc:
                raise RuntimeError(
                    f"Unable to load {selected_tank}. Backend error: {exc}. "
                    f"CSV fallback error: {fallback_exc}."
                ) from fallback_exc

        print("\nAquaSwarm initialized:", selected_tank, self.state.data_source)
        return self.state

    @listen(initialize)
    def analyze_demand(self):
        if self.state.water_data is None:
            raise RuntimeError("Water data is unavailable.")

        task = create_demand_task(self.state.water_data)
        self.state.demand_result = self._run_task(task, "Demand Agent")
        print("\nDemand Result:", self.state.demand_result)

    @router(analyze_demand)
    def route_after_demand(self):
        if self.state.demand_result is None:
            raise RuntimeError("Demand result is unavailable.")

        if self.state.demand_result.shortage > 0:
            return "replenishment_required"

        return "no_replenishment"

    @listen("no_replenishment")
    def no_replenishment_required(self):
        self.state.operation_status = "No Replenishment Required"
        print("\nNO REPLENISHMENT REQUIRED")
        return self.state

    @listen("replenishment_required")
    def analyze_anomaly(self):
        if self.state.water_data is None or self.state.demand_result is None:
            raise RuntimeError("Water or demand result is unavailable.")

        self.state.operation_status = "Replenishment Required"
        task = create_anomaly_task(
            self.state.water_data,
            self.state.demand_result,
        )
        self.state.anomaly_result = self._run_task(task, "Anomaly Agent")
        print("\nAnomaly Result:", self.state.anomaly_result)

    def _get_supplier_records(self):
        """Load supplier records from the backend, falling back to data/suppliers.csv."""
        try:
            client = self._backend()
            if client is not None:
                rows = client.get_suppliers(available_only=False)
                if rows:
                    return rows
        except Exception as exc:
            self.state.backend_sync_error = f"Supplier data sync failed: {exc}"

        path = DATA_DIR / "suppliers.csv"
        if not path.exists():
            raise RuntimeError(
                f"No supplier data available. Expected backend data or {path}."
            )

        data = pd.read_csv(path)
        records = data.to_dict(orient="records")

        normalized = []
        for row in records:
            item = dict(row)

            # The CSV uses numeric ids; the backend uses supplier_code values.
            if not item.get("supplier_code"):
                raw_id = item.get("id")
                if raw_id is None:
                    raise ValueError("Supplier row is missing id/supplier_code.")
                item["supplier_code"] = f"S-{int(raw_id):03d}"

            # Current CSV does not contain these logistics fields.
            item.setdefault("distance_km", 0)
            item.setdefault("estimated_cost", 0)
            item.setdefault("eta_minutes", None)
            normalized.append(item)

        if not normalized:
            raise RuntimeError("Supplier data file contains no supplier records.")

        return normalized

    @listen(analyze_anomaly)
    def analyze_supply(self):
        if self.state.water_data is None or self.state.demand_result is None:
            raise RuntimeError("Water or demand result is unavailable.")

        suppliers = self._get_supplier_records()

        task = create_supply_task(
            self.state.water_data,
            self.state.demand_result,
            suppliers=suppliers,
        )
        self.state.supply_result = self._run_task(task, "Supply Agent")
        print("\nSupply Result:", self.state.supply_result)

    @listen(analyze_supply)
    def allocate_water(self):
        if self.state.demand_result is None or self.state.supply_result is None:
            raise RuntimeError("Demand or supply result is unavailable.")

        task = create_allocation_task(
            self.state.demand_result,
            self.state.supply_result,
        )
        self.state.allocation_result = self._run_task(task, "Allocation Agent")
        print("\nAllocation Result:", self.state.allocation_result)

    @listen(allocate_water)
    def request_manager_approval(self):
        if self.state.allocation_result is None:
            raise RuntimeError("Allocation result is unavailable.")

        self.state.operation_status = "Awaiting Manager Approval"
        self.state.approval_required = True
        self.state.manager_approval_result = None
        self.state.delivery_request_id = None
        self.state.delivery_result = None
        self.state.verification_result = None
        self.state.replanning_result = None

        # Create a pending delivery request so the human decision is persisted
        # against an actual operational request when the backend is available.
        try:
            client = self._backend()
            if client is not None:
                response = client.create_delivery_request(
                    {
                        "site_id": self._site_id_for_tank(
                            self.state.allocation_result.tank_id
                        ),
                        "tank_code": self.state.allocation_result.tank_id,
                        "supplier_code": self.state.allocation_result.supplier_id,
                        "quantity": self.state.allocation_result.allocated_quantity,
                        "notes": "Created from AquaSwarm allocation; awaiting human approval.",
                    }
                )
                self.state.delivery_request_id = int(response["id"])
        except Exception as exc:
            self.state.backend_sync_error = f"Backend delivery-request sync failed: {exc}"

        print("\n==============================")
        print("HUMAN APPROVAL REQUIRED")
        print("==============================")
        print(f"Tank: {self.state.allocation_result.tank_id}")
        print(f"Proposed Quantity: {self.state.allocation_result.allocated_quantity}")
        print(f"Supplier: {self.state.allocation_result.supplier_id}")
        print(f"Priority: {self.state.allocation_result.priority}")

        return self.state

    def _site_id_for_tank(self, tank_code: str) -> int:
        client = self._backend()
        if client is None:
            raise RuntimeError("Backend integration is disabled.")

        tanks = client.get_tanks()
        tank = next(
            (row for row in tanks if row.get("tank_code") == tank_code),
            None,
        )
        if tank is None:
            raise ValueError(f"Tank {tank_code} was not found in backend data.")

        return int(tank["site_id"])

    def manager_decision(
        self,
        approved: bool,
        decided_by: str,
        reason: str = "",
    ):
        """Record the final human decision and continue the correct branch."""
        if not self.state.approval_required:
            raise ValueError("No manager approval is currently pending.")

        if self.state.allocation_result is None:
            raise ValueError("No allocation is available for approval.")

        decided_by = str(decided_by).strip()
        if not decided_by:
            raise ValueError("Manager identity is required.")

        decision_time = datetime.now(timezone.utc).isoformat()
        final_reason = (
            str(reason).strip()
            if str(reason).strip()
            else (
                "Approved by the water operations manager."
                if approved
                else "Rejected by the water operations manager."
            )
        )

        self.state.manager_approval_result = ManagerApprovalResult(
            tank_id=self.state.allocation_result.tank_id,
            approved=approved,
            manager_decision="APPROVED" if approved else "REJECTED",
            reasoning=final_reason,
        )

        self.state.approval_required = False
        self.state.approval_decided_by = decided_by
        self.state.approval_decision_time = decision_time
        self.state.approval_reason = final_reason

        if self.state.delivery_request_id is not None:
            try:
                client = self._backend()
                if client is not None:
                    client.create_approval(
                        {
                            "delivery_request_id": self.state.delivery_request_id,
                            "approved": approved,
                            "approved_by": decided_by,
                            "decision_note": final_reason,
                        }
                    )
            except Exception as exc:
                self.state.backend_sync_error = f"Approval sync failed: {exc}"

        if approved:
            self.state.operation_status = "Manager Approved"
            self.arrange_delivery()
        else:
            self.state.operation_status = "Manager Rejected"
            self.replan_water()

        return self.state

    def arrange_delivery(self):
        """Start delivery only after recorded human approval."""
        approval = self.state.manager_approval_result
        allocation = self.state.allocation_result

        if approval is None or not approval.approved:
            raise ValueError("Delivery cannot be arranged without human approval.")
        if allocation is None:
            raise ValueError("No allocation is available.")
        if self.state.delivery_request_id is None:
            # Local-only/demo mode can still continue.
            self.state.operation_status = "Delivery Dispatched"
        else:
            self.state.operation_status = "Delivery Dispatched"

        eta_minutes = None
        if self.state.supply_result is not None:
            for option in self.state.supply_result.suppliers:
                if option.supplier_id == allocation.supplier_id:
                    eta_minutes = option.eta_minutes
                    break

        task = create_delivery_task(
            allocation_result=allocation,
            eta_minutes=eta_minutes,
            approval_confirmed=True,
        )
        self.state.delivery_result = self._run_task(task, "Delivery Agent")

        if self.state.delivery_request_id is not None:
            try:
                client = self._backend()
                if client is not None:
                    client.update_delivery_status(
                        self.state.delivery_request_id,
                        {"status": "DISPATCHED"},
                    )
            except Exception as exc:
                self.state.backend_sync_error = f"Dispatch sync failed: {exc}"

        print("\nDelivery Result:", self.state.delivery_result)

    def complete_delivery(self, actual_quantity: float):
        """
        Record physical delivery completion and then run verification.

        This method is intentionally separate from arrange_delivery so that a
        DISPATCHED delivery is never automatically treated as delivered.
        """
        if self.state.manager_approval_result is None or not self.state.manager_approval_result.approved:
            raise ValueError("Delivery completion requires human-approved allocation.")

        if self.state.delivery_result is None:
            raise ValueError("No dispatched delivery exists.")

        if actual_quantity < 0:
            raise ValueError("Actual delivered quantity cannot be negative.")

        self.state.delivery_result = DeliveryResult(
            tank_id=self.state.delivery_result.tank_id,
            supplier_id=self.state.delivery_result.supplier_id,
            quantity=float(actual_quantity),
            status="DELIVERED",
            estimated_arrival=self.state.delivery_result.estimated_arrival,
        )

        if self.state.delivery_request_id is not None:
            try:
                client = self._backend()
                if client is not None:
                    client.update_delivery_status(
                        self.state.delivery_request_id,
                        {
                            "status": "DELIVERED",
                            "actual_quantity": float(actual_quantity),
                        },
                    )
            except Exception as exc:
                self.state.backend_sync_error = f"Delivery completion sync failed: {exc}"

        self.verify_delivery()
        return self.state

    def verify_delivery(self):
        if self.state.allocation_result is None:
            raise ValueError("No allocation exists for verification.")

        if self.state.delivery_result is None:
            raise ValueError("Verification requires a delivery result.")

        if self.state.delivery_result.status != "DELIVERED":
            self.state.operation_status = "Delivery In Progress"
            raise ValueError(
                "Verification cannot run until the delivery status is DELIVERED."
            )

        task = create_verification_task(
            self.state.allocation_result,
            self.state.delivery_result,
        )
        self.state.verification_result = self._run_task(
            task,
            "Verification Agent",
        )

        if self.state.verification_result.verified:
            self.state.operation_status = "Delivery Verified"
        else:
            self.state.operation_status = "Verification Review Required"

            # A failed verification is a closed-loop trigger for replanning.
            self._replan_after_verification()

        print("\nVerification Result:", self.state.verification_result)
        return self.state

    def _replan_after_verification(self):
        """
        Trigger a recovery recommendation when delivery verification fails.

        The existing ReplanningResult schema requires ManagerApprovalResult,
        so an internal rejected recovery context is created without pretending
        that the original manager rejected the allocation.
        """
        if self.state.allocation_result is None or self.state.verification_result is None:
            return

        recovery_approval = ManagerApprovalResult(
            tank_id=self.state.allocation_result.tank_id,
            approved=False,
            manager_decision="REJECTED",
            reasoning=(
                "Delivery verification failed: "
                f"{self.state.verification_result.reasoning}"
            ),
        )

        task = create_replanning_task(
            self.state.allocation_result,
            recovery_approval,
        )
        self.state.replanning_result = self._run_task(
            task,
            "Replanning Agent",
        )

    def replan_water(self):
        """Run replanning after an actual manager rejection."""
        if self.state.manager_approval_result is None:
            raise ValueError("No manager decision exists.")
        if self.state.manager_approval_result.approved:
            raise ValueError("Replanning is only allowed after rejection.")
        if self.state.allocation_result is None:
            raise ValueError("No allocation exists.")

        task = create_replanning_task(
            self.state.allocation_result,
            self.state.manager_approval_result,
        )
        self.state.replanning_result = self._run_task(
            task,
            "Replanning Agent",
        )
        self.state.operation_status = "Replanning Required"

        print("\nReplanning Result:", self.state.replanning_result)
        return self.state


if __name__ == "__main__":
    flow = AquaSwarmFlow()
    flow.kickoff(inputs={"selected_tank_id": "TANK-001"})

    print("\n==============================")
    print("FLOW REACHED HUMAN APPROVAL")
    print("==============================")
    print("Operation Status:", flow.state.operation_status)
    print("Approval Required:", flow.state.approval_required)
    print("Delivery Request ID:", flow.state.delivery_request_id)
