from dataclasses import dataclass
from typing import Optional


@dataclass
class Site:
    id: int
    name: str
    location: str
    manager_name: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class Tank:
    id: int
    tank_code: str
    site_id: int
    name: str
    capacity: float
    current_level: float
    critical_threshold: float = 20.0
    updated_at: Optional[str] = None


@dataclass
class Consumption:
    id: int
    site_id: int
    tank_id: int
    amount: float
    timestamp: str
    source: str = "CSV_IMPORT"


@dataclass
class Supplier:
    id: int
    supplier_code: str
    name: str
    capacity: float
    available: bool
    distance_km: float = 0.0
    estimated_cost: float = 0.0
    eta_minutes: int = 60
    phone: Optional[str] = None
    last_updated: Optional[str] = None


@dataclass
class Alert:
    id: int
    site_id: int
    tank_id: Optional[int]
    alert_type: str
    severity: str
    message: str
    status: str
    timestamp: str


@dataclass
class DeliveryRequest:
    id: int
    site_id: int
    tank_id: int
    supplier_id: int
    quantity: float
    status: str
    estimated_arrival: Optional[str]
    requested_at: str
    actual_quantity: Optional[float] = None
    delivered_at: Optional[str] = None
    notes: str = ""


@dataclass
class Approval:
    id: int
    delivery_request_id: int
    site_id: int
    tank_id: int
    proposed_quantity: float
    supplier_id: int
    status: str
    approved: Optional[bool]
    approved_by: Optional[str]
    decision_timestamp: Optional[str] = None
    decision_note: str = ""


@dataclass
class Verification:
    id: int
    delivery_request_id: int
    expected_quantity: float
    actual_quantity: float
    discrepancy: float
    verification_status: str
    verification_timestamp: str
    note: str = ""


@dataclass
class AgentRun:
    id: int
    agent_name: str
    status: str
    timestamp: str
    operation_run_id: str
    input_summary: str = ""
    output_summary: str = ""
