from pydantic import BaseModel, Field
from typing import List, Optional


class WaterData(BaseModel):
    tank_id: str
    current_level: float = Field(ge=0)
    capacity: float = Field(gt=0)
    daily_demand: float = Field(ge=0)
    inflow: float = Field(ge=0)
    timestamp: str


class DemandResult(BaseModel):
    tank_id: str
    estimated_demand: float
    shortage: float
    priority: str
    reasoning: str


class AnomalyResult(BaseModel):
    tank_id: str
    anomaly_detected: bool
    anomaly_type: Optional[str] = None
    severity: str
    reasoning: str


class SupplyOption(BaseModel):
    supplier_id: str
    available_quantity: float
    distance_km: float
    estimated_cost: float


class SupplyResult(BaseModel):
    tank_id: str
    suppliers: List[SupplyOption]
    recommended_supplier: Optional[str] = None
    reasoning: str


class AllocationResult(BaseModel):
    tank_id: str
    allocated_quantity: float
    supplier_id: str
    priority: str
    reasoning: str


class DeliveryResult(BaseModel):
    tank_id: str
    supplier_id: str
    quantity: float
    status: str
    estimated_arrival: str


class VerificationResult(BaseModel):
    tank_id: str
    delivered_quantity: float
    verified: bool
    discrepancy: float
    status: str
    reasoning: str


class ManagerApprovalResult(BaseModel):
    tank_id: str
    approved: bool
    manager_decision: str
    reasoning: str


class ReplanningResult(BaseModel):
    tank_id: str
    action: str
    reason: str