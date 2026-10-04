from dataclasses import dataclass


@dataclass
class Site:
    id: int
    name: str
    location: str


@dataclass
class Tank:
    id: int
    site_id: int
    capacity: float
    current_level: float


@dataclass
class Consumption:
    id: int
    site_id: int
    amount: float
    timestamp: str


@dataclass
class Supplier:
    id: int
    name: str
    capacity: float
    available: bool


@dataclass
class Alert:
    id: int
    site_id: int
    message: str
    severity: str
    timestamp: str


@dataclass
class DeliveryRequest:
    id: int
    site_id: int
    supplier_id: int
    quantity: float
    status: str


@dataclass
class AgentRun:
    id: int
    agent_name: str
    status: str
    timestamp: str


@dataclass
class Approval:
    id: int
    delivery_id: int
    approved: bool
    approved_by: str


@dataclass
class Verification:
    id: int
    delivery_id: int
    expected_quantity: float
    actual_quantity: float
    status: str