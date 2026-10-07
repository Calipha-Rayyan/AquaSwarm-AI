from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from crewai import Crew, Process
from crewai.flow import Flow, listen, router, start
from pydantic import BaseModel, Field

from agents.allocation.task import create_allocation_task
from agents.anomaly.task import create_anomaly_task
from agents.approval.task import create_manager_approval_task
from agents.delivery.task import create_delivery_task
from agents.demand.task import create_demand_task
from agents.replanning.task import create_replanning_task
from agents.supply.task import _load_suppliers, create_supply_task
from agents.verification.task import (
    QUANTITY_TOLERANCE,
    create_verification_task,
)
from backend.client import BackendClient, BackendUnavailable
from config.settings import (
    AQUASWARM_BACKEND_ENABLED,
    AQUASWARM_BACKEND_MODE,
    AQUASWARM_BACKEND_TIMEOUT,
    AQUASWARM_BACKEND_URL,
    AQUASWARM_DEFAULT_INFLOW,
)
from models.schemas import (
    AllocationResult,
    AnomalyResult,
    DeliveryResult,
    DemandResult,
    ManagerApprovalResult,
    ReplanningResult,
    SupplyOption,
    SupplyResult,
    VerificationResult,
    WaterData,
)
from tools.water_tools import assess_tank, default_policy, rank_suppliers

# Order shown in the dashboard pipeline. "Replanning" is added on demand.
STAGE_ORDER = [
    "Demand",
    "Anomaly",
    "Supply",
    "Allocation",
    "Approval",
    "Delivery",
    "Verification",
]

# What-if scenarios change only the in-memory reading. They never write to
# the backend, so simulated water can never reach the real tank levels.
SCENARIOS: Dict[str, str] = {
    "LIVE": "Live backend data",
    "DEMAND_SURGE": "Demand surge (demand x2.5)",
    "LOW_LEVEL": "Low tank level (28% fill)",
    "CRITICAL_LOW": "Critical shortage (8% fill, demand x1.5)",
}

_ALLOWED_REPLAN_ACTIONS = {
    "REPLAN_ALLOCATION",
    "REVIEW_SUPPLIER",
    "REVIEW_QUANTITY",
    "REQUEST_NEW_APPROVAL",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_scenario(water: WaterData, scenario: str) -> WaterData:
    """Return the reading adjusted for a what-if scenario (LIVE = unchanged)."""
    scenario = (scenario or "LIVE").upper()
    values = water.model_dump()

    if scenario == "DEMAND_SURGE":
        values["daily_demand"] = round(float(water.daily_demand) * 2.5, 2)
    elif scenario == "LOW_LEVEL":
        values["current_level"] = round(float(water.capacity) * 0.28, 2)
    elif scenario == "CRITICAL_LOW":
        values["current_level"] = round(float(water.capacity) * 0.08, 2)
        values["daily_demand"] = round(float(water.daily_demand) * 1.5, 2)
    elif scenario != "LIVE":
        raise ValueError(f"Unknown scenario: {scenario!r}")

    return WaterData(**values)


class StageRecord(BaseModel):
    # pending | running | active | done | skipped | blocked | rejected | error
    status: str = "pending"
    detail: str = ""
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_s: Optional[float] = None


def _default_stages() -> Dict[str, StageRecord]:
    return {name: StageRecord() for name in STAGE_ORDER}


class AquaSwarmState(BaseModel):
    """State shared across one AquaSwarm operation."""

    selected_tank_id: str = "TANK-001"
    scenario: str = "LIVE"
    operation_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    operation_status: str = "Pending"
    error_message: str = ""

    site_id: Optional[int] = None
    water_data: Optional[WaterData] = None
    assessment: Optional[Dict[str, Any]] = None

    demand_result: Optional[DemandResult] = None
    anomaly_result: Optional[AnomalyResult] = None
    supply_result: Optional[SupplyResult] = None
    supply_ranking: List[str] = Field(default_factory=list)
    allocation_result: Optional[AllocationResult] = None

    approval_recommendation: Optional[ManagerApprovalResult] = None
    manager_approval_result: Optional[ManagerApprovalResult] = None
    approval_required: bool = False
    approval_decided_by: Optional[str] = None
    approval_decision_time: Optional[str] = None
    approval_reason: str = ""

    delivery_request_id: Optional[int] = None
    delivery_result: Optional[DeliveryResult] = None
    verification_result: Optional[VerificationResult] = None
    replanning_result: Optional[ReplanningResult] = None
    updated_level: Optional[float] = None

    stages: Dict[str, StageRecord] = Field(default_factory=_default_stages)
    activity: List[Dict[str, str]] = Field(default_factory=list)
    sync_warnings: List[str] = Field(default_factory=list)
    llm_warnings: List[str] = Field(default_factory=list)

    data_source: str = "Pending"
    # Kept so older UI code that reads it keeps working; always empty now
    # because there is no CSV fallback to report.
    backend_sync_error: str = ""


class AquaSwarmFlow(Flow[AquaSwarmState]):

    # ------------------------------------------------------------------
    # Infrastructure
    # ------------------------------------------------------------------

    def _backend(self) -> BackendClient:
        client = getattr(self, "_client_cache", None)
        if client is None:
            if not AQUASWARM_BACKEND_ENABLED:
                raise BackendUnavailable(
                    "The backend is disabled (AQUASWARM_BACKEND_ENABLED=false). "
                    "The pipeline reads tanks and suppliers from the backend."
                )
            client = BackendClient(
                base_url=AQUASWARM_BACKEND_URL,
                timeout=AQUASWARM_BACKEND_TIMEOUT,
                mode=AQUASWARM_BACKEND_MODE,
            )
            self._client_cache = client
        return client

    def _persist(self) -> bool:
        """Only live operations write to the backend."""
        return self.state.scenario == "LIVE"

    def _log(self, agent: str, message: str, level: str = "info") -> None:
        self.state.activity.append(
            {
                "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                "agent": agent,
                "message": message,
                "level": level,
            }
        )
        del self.state.activity[:-80]

    def _warn(self, message: str) -> None:
        self.state.sync_warnings.append(message[:300])
        self._log("System", message, "warn")

    def _record_run(self, agent: str, status: str, summary_in: str, summary_out: str) -> None:
        """Best-effort audit trail in the backend (/agent-runs)."""
        if not self._persist():
            return
        try:
            self._backend().create_agent_run(
                {
                    "agent_name": agent,
                    "status": status,
                    "operation_run_id": self.state.operation_id,
                    "input_summary": summary_in[:500],
                    "output_summary": summary_out[:500],
                }
            )
        except Exception as exc:
            self._warn(f"Agent-run log failed for {agent}: {exc}")

    @contextmanager
    def _stage(self, name: str, detail: str = ""):
        record = self.state.stages.get(name)
        if record is None:
            record = StageRecord()
            self.state.stages[name] = record

        record.status = "running"
        record.detail = detail
        record.started_at = _now_iso()
        record.finished_at = None
        started = time.monotonic()
        self._log(name, detail or "Started")

        try:
            yield record
        except Exception as exc:
            record.status = "error"
            record.detail = str(exc)[:300]
            self.state.error_message = f"{name}: {exc}"
            self.state.operation_status = "Pipeline Error"
            self._log(name, f"Failed — {exc}", "error")
            raise
        else:
            # Callers may leave a stage "active" (waiting on a human or on the
            # physical delivery) or mark it blocked/skipped/rejected.
            if record.status == "running":
                record.status = "done"
        finally:
            record.duration_s = round(time.monotonic() - started, 2)
            if record.status not in {"active"}:
                record.finished_at = _now_iso()

    def _skip(self, names: List[str], reason: str, status: str = "skipped") -> None:
        for name in names:
            record = self.state.stages.get(name)
            if record is None:
                record = StageRecord()
                self.state.stages[name] = record
            if record.status in {"pending", "running"}:
                record.status = status
                record.detail = reason

    def _try_run(self, task, label: str):
        """Run one agent. Returns (structured_result | None, error_text)."""
        try:
            result = Crew(
                agents=[task.agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False,
            ).kickoff()
            structured = getattr(result, "pydantic", None)
            if structured is None:
                raise RuntimeError("the agent did not return a structured result")
            return structured, ""
        except Exception as exc:
            message = f"{label}: {type(exc).__name__}: {exc}"
            self.state.llm_warnings.append(message[:300])
            self._log(
                label,
                "AI response unavailable — deterministic result used",
                "warn",
            )
            return None, message

    @staticmethod
    def _normalise_tank_code(value) -> str:
        """Normalize numeric ids and API tank codes to TANK-###."""
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

    # ------------------------------------------------------------------
    # 0. Observe (backend only, no CSV fallback)
    # ------------------------------------------------------------------

    @start()
    def initialize(self):
        selected = self._normalise_tank_code(self.state.selected_tank_id)
        self.state.selected_tank_id = selected
        self.state.operation_status = "Initializing"
        self._log("Observe", f"Loading {selected} from the backend")

        try:
            client = self._backend()
            tanks = client.get_tanks()
            tank = next(
                (
                    row
                    for row in tanks
                    if self._normalise_tank_code(row.get("tank_code")) == selected
                ),
                None,
            )
            if tank is None:
                known = ", ".join(sorted(str(t.get("tank_code")) for t in tanks)) or "none"
                raise ValueError(
                    f"Tank {selected} was not found in the backend (known: {known})."
                )

            consumption = client.get_consumption(tank_code=selected, limit=1)
            if consumption:
                daily_demand = float(consumption[0]["amount"])
            else:
                daily_demand = 0.0
                self._warn(
                    f"No consumption record exists for {selected}; demand assumed 0."
                )

            reading = WaterData(
                tank_id=selected,
                current_level=float(tank["current_level"]),
                capacity=float(tank["capacity"]),
                daily_demand=daily_demand,
                inflow=AQUASWARM_DEFAULT_INFLOW,
                timestamp=_now_iso(),
            )
            self.state.site_id = int(tank["site_id"])
            self.state.data_source = f"BACKEND API · {client.mode_label}"

        except Exception as exc:
            self.state.operation_status = "Pipeline Error"
            self.state.error_message = f"Backend data unavailable — {exc}"
            self._log("Observe", self.state.error_message, "error")
            raise

        self.state.water_data = apply_scenario(reading, self.state.scenario)
        if self.state.scenario != "LIVE":
            self._log(
                "Observe",
                f"SIMULATION: {SCENARIOS[self.state.scenario]} (no backend writes)",
                "warn",
            )
        return self.state

    # ------------------------------------------------------------------
    # 1. Demand
    # ------------------------------------------------------------------

    @listen(initialize)
    def analyze_demand(self):
        water = self.state.water_data
        if water is None:
            raise RuntimeError("Water data is unavailable.")

        with self._stage("Demand", "Computing shortage, cover days and priority") as stage:
            task = create_demand_task(water)
            llm_result, _ = self._try_run(task, "Demand Agent")

            a = assess_tank(
                water.current_level,
                water.capacity,
                water.daily_demand,
                water.inflow,
                default_policy(),
            )
            self.state.assessment = {
                "fill_percentage": a.fill_percentage,
                "days_of_cover": a.days_of_cover,
                "cover_label": a.cover_label,
                "net_daily_change": a.net_daily_change,
                "target_level": a.target_level,
                "shortage": a.shortage,
                "priority": a.priority,
            }

            reasoning = (getattr(llm_result, "reasoning", "") or "").strip() or (
                f"{water.tank_id} is {a.fill_percentage:.0f}% full with "
                f"{a.cover_label} of cover against a target reserve of "
                f"{a.target_level:g} units; shortage {a.shortage:g} units."
            )

            # Deterministic values are authoritative: the model only explains.
            self.state.demand_result = DemandResult(
                tank_id=water.tank_id,
                estimated_demand=a.estimated_demand,
                shortage=a.shortage,
                priority=a.priority,
                reasoning=reasoning,
            )
            stage.detail = f"{a.priority} priority · shortage {a.shortage:g} units"
            self.state.operation_status = "Demand Analyzed"

        self._record_run(
            "Demand Agent", "COMPLETED",
            f"{water.tank_id} level={water.current_level:g} demand={water.daily_demand:g}",
            stage.detail,
        )

    # ------------------------------------------------------------------
    # 2. Anomaly (always runs: a healthy tank can still be abnormal)
    # ------------------------------------------------------------------

    @listen(analyze_demand)
    def analyze_anomaly(self):
        water, demand = self.state.water_data, self.state.demand_result
        if water is None or demand is None:
            raise RuntimeError("Water or demand result is unavailable.")

        with self._stage("Anomaly", "Checking tank behaviour for anomalies") as stage:
            task = create_anomaly_task(water, demand)
            llm_result, _ = self._try_run(task, "Anomaly Agent")

            if llm_result is not None:
                detected = bool(llm_result.anomaly_detected)
                a_type = (llm_result.anomaly_type or "NONE").strip().upper()
                severity = str(llm_result.severity).strip().upper()
                reasoning = llm_result.reasoning
            else:
                a_info = self.state.assessment or {}
                fill = float(a_info.get("fill_percentage", 100))
                cover = a_info.get("days_of_cover")
                detected = fill <= 30 or (cover is not None and cover < 3)
                a_type = (
                    "RAPID_DEPLETION"
                    if cover is not None and cover < 3
                    else "LOW_WATER_LEVEL"
                ) if detected else "NONE"
                severity = demand.priority if detected else "LOW"
                reasoning = (
                    "Deterministic check (AI response unavailable): "
                    + (
                        f"{fill:.0f}% fill with {a_info.get('cover_label')} of cover."
                        if detected
                        else "fill level and days of cover are within limits."
                    )
                )

            if severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
                severity = "MEDIUM" if detected else "LOW"
            if not detected:
                a_type, severity = "NONE", "LOW"

            self.state.anomaly_result = AnomalyResult(
                tank_id=water.tank_id,
                anomaly_detected=detected,
                anomaly_type=a_type,
                severity=severity,
                reasoning=reasoning or "No reasoning supplied.",
            )
            stage.detail = (
                f"{a_type.replace('_', ' ').title()} · {severity}"
                if detected else "No anomaly detected"
            )

        if (
            self._persist()
            and detected
            and severity in {"HIGH", "CRITICAL"}
            and self.state.site_id is not None
        ):
            try:
                self._backend().create_alert(
                    {
                        "site_id": self.state.site_id,
                        "tank_code": water.tank_id,
                        "alert_type": a_type,
                        "severity": severity,
                        "message": f"{water.tank_id}: {reasoning}"[:480],
                    }
                )
            except Exception as exc:
                self._warn(f"Alert could not be recorded: {exc}")

        self._record_run("Anomaly Agent", "COMPLETED", water.tank_id, stage.detail)

    @router(analyze_anomaly)
    def route_after_anomaly(self):
        if self.state.demand_result is None:
            raise RuntimeError("Demand result is unavailable.")
        if self.state.demand_result.shortage > 0:
            return "replenishment_required"
        return "no_replenishment"

    @listen("no_replenishment")
    def no_replenishment_required(self):
        self.state.operation_status = "No Replenishment Required"
        self._skip(
            ["Supply", "Allocation", "Approval", "Delivery", "Verification"],
            "Not required — reserve is sufficient",
        )
        self._log("Pipeline", "Reserve sufficient; procurement not required")
        return self.state

    # ------------------------------------------------------------------
    # 3. Supply
    # ------------------------------------------------------------------

    def _get_supplier_records(self) -> List[dict]:
        rows = self._backend().get_suppliers(available_only=False)
        if not rows:
            raise RuntimeError("The backend returned no supplier records.")
        return rows

    @listen("replenishment_required")
    def analyze_supply(self):
        water, demand = self.state.water_data, self.state.demand_result
        if water is None or demand is None:
            raise RuntimeError("Water or demand result is unavailable.")

        self.state.operation_status = "Replenishment Required"

        with self._stage("Supply", "Filtering and ranking suppliers") as stage:
            records = self._get_supplier_records()
            task = create_supply_task(water, demand, suppliers=records)
            llm_result, _ = self._try_run(task, "Supply Agent")

            normalised = _load_suppliers(records)
            required = float(demand.shortage)
            eligible = [
                s for s in normalised
                if s["available"] and s["available_quantity"] >= required
            ]
            ranked = rank_suppliers(eligible)
            recommended = ranked[0]["supplier_id"] if ranked else None

            default_reason = (
                f"{recommended} is the lowest-cost eligible supplier for "
                f"{required:g} units."
                if recommended
                else f"No available supplier can deliver {required:g} units."
            )
            reasoning = (getattr(llm_result, "reasoning", "") or "").strip()
            # The model must not contradict the deterministic ranking.
            if recommended and recommended not in reasoning:
                reasoning = default_reason
            reasoning = reasoning or default_reason

            self.state.supply_ranking = [s["supplier_id"] for s in ranked]
            self.state.supply_result = SupplyResult(
                tank_id=water.tank_id,
                suppliers=[
                    SupplyOption(
                        supplier_id=s["supplier_id"],
                        available_quantity=s["available_quantity"],
                        distance_km=s["distance_km"],
                        estimated_cost=s["estimated_cost"],
                        name=s["name"],
                        available=bool(s["available"]),
                        eta_minutes=s["eta_minutes"],
                    )
                    for s in normalised
                ],
                recommended_supplier=recommended,
                reasoning=reasoning,
            )

            if recommended is None:
                largest = max(
                    (s["available_quantity"] for s in normalised if s["available"]),
                    default=0.0,
                )
                stage.status = "blocked"
                stage.detail = (
                    f"No supplier covers {required:g} units "
                    f"(largest available: {largest:g})"
                )
                self.state.operation_status = "No Eligible Supplier"
                self._skip(
                    ["Allocation", "Approval", "Delivery", "Verification"],
                    "Blocked — no eligible supplier",
                    status="blocked",
                )
            else:
                stage.detail = f"{recommended} recommended · {len(ranked)} eligible"

        self._record_run("Supply Agent", "COMPLETED", f"need {demand.shortage:g}", stage.detail)

    # ------------------------------------------------------------------
    # 4. Allocation
    # ------------------------------------------------------------------

    @listen(analyze_supply)
    def allocate_water(self):
        demand, supply = self.state.demand_result, self.state.supply_result
        if demand is None or supply is None:
            raise RuntimeError("Demand or supply result is unavailable.")
        if supply.recommended_supplier is None:
            return  # pipeline already marked blocked

        with self._stage("Allocation", "Sizing the delivery") as stage:
            task = create_allocation_task(demand, supply)
            llm_result, _ = self._try_run(task, "Allocation Agent")

            chosen = next(
                s for s in supply.suppliers
                if s.supplier_id == supply.recommended_supplier
            )
            # Safe upper bound is computed deterministically.
            quantity = min(float(demand.shortage), float(chosen.available_quantity))

            reasoning = (getattr(llm_result, "reasoning", "") or "").strip() or (
                f"Allocate {quantity:g} units from {chosen.supplier_id} to cover "
                f"the {demand.shortage:g}-unit shortage."
            )
            self.state.allocation_result = AllocationResult(
                tank_id=demand.tank_id,
                allocated_quantity=quantity,
                supplier_id=chosen.supplier_id,
                priority=demand.priority,
                reasoning=reasoning,
            )
            stage.detail = f"{quantity:g} units from {chosen.supplier_id}"

        self._record_run("Allocation Agent", "COMPLETED", f"need {demand.shortage:g}", stage.detail)

    # ------------------------------------------------------------------
    # 5. Approval: AI review (advisory) then the human gate
    # ------------------------------------------------------------------

    @listen(allocate_water)
    def request_manager_approval(self):
        allocation = self.state.allocation_result
        if allocation is None:
            return

        self.state.manager_approval_result = None
        self.state.delivery_request_id = None
        self.state.delivery_result = None
        self.state.verification_result = None
        self.state.replanning_result = None

        with self._stage("Approval", "AI reviewer checking the allocation") as stage:
            try:
                review_task = create_manager_approval_task(allocation)
                review, _ = self._try_run(review_task, "Approval Review Agent")
            except ValueError as exc:
                review = None
                self._warn(f"AI approval review skipped: {exc}")

            if review is not None:
                self.state.approval_recommendation = ManagerApprovalResult(
                    tank_id=allocation.tank_id,
                    approved=bool(review.approved),
                    manager_decision=str(review.manager_decision),
                    reasoning=review.reasoning,
                )

            # Persist a pending request so the human decision is recorded
            # against a real operational record. Fail closed on errors.
            if self._persist():
                response = self._backend().create_delivery_request(
                    {
                        "site_id": self.state.site_id,
                        "tank_code": allocation.tank_id,
                        "supplier_code": allocation.supplier_id,
                        "quantity": allocation.allocated_quantity,
                        "notes": f"AquaSwarm operation {self.state.operation_id}; awaiting human approval.",
                    }
                )
                self.state.delivery_request_id = int(response["id"])

            self.state.approval_required = True
            self.state.operation_status = "Awaiting Manager Approval"
            stage.status = "active"
            stage.detail = "Awaiting manager decision"

        self._record_run(
            "Approval Review Agent", "COMPLETED",
            f"{allocation.allocated_quantity:g} units / {allocation.supplier_id}",
            "AI recommendation: "
            + (self.state.approval_recommendation.manager_decision
               if self.state.approval_recommendation else "not available"),
        )
        return self.state

    def manager_decision(self, approved: bool, decided_by: str, reason: str = ""):
        """Record the final human decision and continue the correct branch."""
        if not self.state.approval_required:
            raise ValueError("No manager approval is currently pending.")
        if self.state.allocation_result is None:
            raise ValueError("No allocation is available for approval.")

        decided_by = str(decided_by).strip()
        if not decided_by:
            raise ValueError("Manager identity is required.")

        final_reason = str(reason).strip() or (
            "Approved by the water operations manager."
            if approved
            else "Rejected by the water operations manager."
        )

        # Record the decision in the backend first; never act on an
        # unrecorded approval.
        if self.state.delivery_request_id is not None:
            self._backend().create_approval(
                {
                    "delivery_request_id": self.state.delivery_request_id,
                    "approved": approved,
                    "approved_by": decided_by,
                    "decision_note": final_reason,
                }
            )

        self.state.manager_approval_result = ManagerApprovalResult(
            tank_id=self.state.allocation_result.tank_id,
            approved=approved,
            manager_decision="APPROVED" if approved else "REJECTED",
            reasoning=final_reason,
        )
        self.state.approval_required = False
        self.state.approval_decided_by = decided_by
        self.state.approval_decision_time = _now_iso()
        self.state.approval_reason = final_reason

        approval_stage = self.state.stages["Approval"]
        approval_stage.status = "done" if approved else "rejected"
        approval_stage.detail = f"{'Approved' if approved else 'Rejected'} by {decided_by}"
        approval_stage.finished_at = _now_iso()
        self._log("Approval", approval_stage.detail)
        self._record_run(
            "Manager", "COMPLETED", self.state.allocation_result.tank_id,
            approval_stage.detail,
        )

        if approved:
            self.state.operation_status = "Manager Approved"
            self.arrange_delivery()
        else:
            self.state.operation_status = "Manager Rejected"
            self._skip(["Delivery", "Verification"], "Allocation rejected")
            self.replan_water()

        return self.state

    # ------------------------------------------------------------------
    # 6. Delivery
    # ------------------------------------------------------------------

    def arrange_delivery(self):
        approval = self.state.manager_approval_result
        allocation = self.state.allocation_result
        if approval is None or not approval.approved:
            raise ValueError("Delivery cannot be arranged without human approval.")
        if allocation is None:
            raise ValueError("No allocation is available.")

        eta_minutes = None
        if self.state.supply_result is not None:
            for option in self.state.supply_result.suppliers:
                if option.supplier_id == allocation.supplier_id:
                    eta_minutes = option.eta_minutes
                    break

        with self._stage("Delivery", "Dispatching the approved delivery") as stage:
            task = create_delivery_task(
                allocation_result=allocation,
                eta_minutes=eta_minutes,
                approval_confirmed=True,
            )
            self._try_run(task, "Delivery Agent")

            arrival = (
                (datetime.now(timezone.utc) + timedelta(minutes=int(eta_minutes))).isoformat()
                if eta_minutes is not None
                else "UNKNOWN"
            )
            self.state.delivery_result = DeliveryResult(
                tank_id=allocation.tank_id,
                supplier_id=allocation.supplier_id,
                quantity=float(allocation.allocated_quantity),
                status="DISPATCHED",
                estimated_arrival=arrival,
            )

            if self.state.delivery_request_id is not None:
                self._backend().update_delivery_status(
                    self.state.delivery_request_id,
                    {"status": "DISPATCHED"},
                )

            self.state.operation_status = "Delivery Dispatched"
            stage.status = "active"
            stage.detail = (
                f"In transit · ETA {int(eta_minutes)} min"
                if eta_minutes is not None
                else "In transit"
            )

        self._skip(["Verification"], "Waiting for delivery", status="pending")
        self._record_run("Delivery Agent", "COMPLETED", allocation.supplier_id, stage.detail)

    def complete_delivery(self, actual_quantity: float):
        """Record the physical receipt, then run verification."""
        approval = self.state.manager_approval_result
        if approval is None or not approval.approved:
            raise ValueError("Delivery completion requires a human-approved allocation.")
        if self.state.delivery_result is None:
            raise ValueError("No dispatched delivery exists.")
        if actual_quantity < 0:
            raise ValueError("Actual delivered quantity cannot be negative.")

        if self.state.delivery_request_id is not None:
            self._backend().update_delivery_status(
                self.state.delivery_request_id,
                {"status": "DELIVERED", "actual_quantity": float(actual_quantity)},
            )

        self.state.delivery_result = DeliveryResult(
            tank_id=self.state.delivery_result.tank_id,
            supplier_id=self.state.delivery_result.supplier_id,
            quantity=float(actual_quantity),
            status="DELIVERED",
            estimated_arrival=self.state.delivery_result.estimated_arrival,
        )

        delivery_stage = self.state.stages["Delivery"]
        delivery_stage.status = "done"
        delivery_stage.detail = f"Received {float(actual_quantity):g} units"
        delivery_stage.finished_at = _now_iso()
        self._log("Delivery", delivery_stage.detail)

        self.verify_delivery()
        return self.state

    # ------------------------------------------------------------------
    # 7. Verification
    # ------------------------------------------------------------------

    def verify_delivery(self):
        allocation, delivery = self.state.allocation_result, self.state.delivery_result
        if allocation is None:
            raise ValueError("No allocation exists for verification.")
        if delivery is None:
            raise ValueError("Verification requires a delivery result.")
        if delivery.status != "DELIVERED":
            self.state.operation_status = "Delivery In Progress"
            raise ValueError("Verification cannot run until the delivery is DELIVERED.")

        with self._stage("Verification", "Comparing delivered and approved quantity") as stage:
            task = create_verification_task(allocation, delivery)
            llm_result, _ = self._try_run(task, "Verification Agent")

            expected = float(allocation.allocated_quantity)
            received = float(delivery.quantity)
            discrepancy = expected - received
            verified = (
                abs(discrepancy) <= QUANTITY_TOLERANCE
                and str(delivery.supplier_id) == str(allocation.supplier_id)
                and delivery.status == "DELIVERED"
            )
            status = "VERIFIED" if verified else "REVIEW_REQUIRED"
            reasoning = (getattr(llm_result, "reasoning", "") or "").strip() or (
                f"Received {received:g} of {expected:g} approved units "
                f"(discrepancy {discrepancy:.2f})."
            )

            self.state.verification_result = VerificationResult(
                tank_id=allocation.tank_id,
                delivered_quantity=received,
                verified=verified,
                discrepancy=round(discrepancy, 2),
                status=status,
                reasoning=reasoning,
            )

            # Close the loop: a verified delivery raises the tank level in the
            # backend, so the next run sees the new operating condition.
            if self.state.delivery_request_id is not None:
                try:
                    client = self._backend()
                    client.create_verification(
                        {
                            "delivery_request_id": self.state.delivery_request_id,
                            "expected_quantity": expected,
                            "actual_quantity": received,
                            "note": reasoning[:300],
                        }
                    )
                    tank = next(
                        (
                            t for t in client.get_tanks()
                            if self._normalise_tank_code(t.get("tank_code"))
                            == allocation.tank_id
                        ),
                        None,
                    )
                    if tank is not None:
                        self.state.updated_level = float(tank["current_level"])
                except Exception as exc:
                    self._warn(f"Verification could not be recorded in the backend: {exc}")

            if verified:
                stage.detail = "Delivery verified"
                self.state.operation_status = "Delivery Verified"
            else:
                stage.status = "blocked"
                stage.detail = f"Review required · discrepancy {discrepancy:.2f}"
                self.state.operation_status = "Verification Review Required"

        self._record_run("Verification Agent", "COMPLETED", allocation.tank_id, stage.detail)

        if not self.state.verification_result.verified:
            self._replan_after_verification()
        return self.state

    # ------------------------------------------------------------------
    # Replanning
    # ------------------------------------------------------------------

    def _run_replanning(self, allocation: AllocationResult, rejection: ManagerApprovalResult):
        with self._stage("Replanning", "Choosing a recovery action") as stage:
            task = create_replanning_task(allocation, rejection)
            llm_result, _ = self._try_run(task, "Replanning Agent")

            action = str(getattr(llm_result, "action", "")).strip().upper()
            if action not in _ALLOWED_REPLAN_ACTIONS:
                action = "REPLAN_ALLOCATION"
            reason = (getattr(llm_result, "reason", "") or "").strip() or rejection.reasoning

            self.state.replanning_result = ReplanningResult(
                tank_id=allocation.tank_id,
                action=action,
                reason=reason,
            )
            stage.detail = action.replace("_", " ").title()

    def _replan_after_verification(self):
        """A failed verification triggers a recovery recommendation."""
        allocation, verification = self.state.allocation_result, self.state.verification_result
        if allocation is None or verification is None:
            return

        recovery = ManagerApprovalResult(
            tank_id=allocation.tank_id,
            approved=False,
            manager_decision="REJECTED",
            reasoning=f"Delivery verification failed: {verification.reasoning}",
        )
        self._run_replanning(allocation, recovery)

    def replan_water(self):
        """Run replanning after an actual manager rejection."""
        approval = self.state.manager_approval_result
        if approval is None:
            raise ValueError("No manager decision exists.")
        if approval.approved:
            raise ValueError("Replanning is only allowed after rejection.")
        if self.state.allocation_result is None:
            raise ValueError("No allocation exists.")

        self._run_replanning(self.state.allocation_result, approval)
        self.state.operation_status = "Replanning Required"
        return self.state


if __name__ == "__main__":
    flow = AquaSwarmFlow()
    flow.state.selected_tank_id = "TANK-001"
    flow.state.scenario = "LOW_LEVEL"
    flow.kickoff()

    print("\n==============================")
    print("FLOW STATUS:", flow.state.operation_status)
    for name, rec in flow.state.stages.items():
        print(f"  {name:<13} {rec.status:<9} {rec.detail}")