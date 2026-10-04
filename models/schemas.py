from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


def _required_text(value: str, field_name: str) -> str:
    value = str(value).strip()
    if not value:
        raise ValueError(f"{field_name} cannot be empty.")
    return value


def _finite_non_negative(value: float, field_name: str) -> float:
    value = float(value)
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError(f"{field_name} must be finite.")
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative.")
    return value


class WaterData(BaseModel):
    tank_id: str
    current_level: float = Field(ge=0)
    capacity: float = Field(gt=0)
    daily_demand: float = Field(ge=0)
    inflow: float = Field(ge=0)
    timestamp: str

    @field_validator("tank_id", "timestamp")
    @classmethod
    def validate_text(cls, value, info):
        return _required_text(value, info.field_name)

    @field_validator("current_level", "capacity", "daily_demand", "inflow")
    @classmethod
    def validate_finite(cls, value, info):
        return _finite_non_negative(value, info.field_name)

    @model_validator(mode="after")
    def validate_level(self):
        if self.current_level > self.capacity:
            raise ValueError("current_level cannot exceed capacity.")
        return self


class DemandResult(BaseModel):
    tank_id: str
    estimated_demand: float = Field(ge=0)
    shortage: float = Field(ge=0)
    priority: str
    reasoning: str

    @field_validator("tank_id", "priority", "reasoning")
    @classmethod
    def validate_text(cls, value, info):
        return _required_text(value, info.field_name)

    @field_validator("estimated_demand", "shortage")
    @classmethod
    def validate_numbers(cls, value, info):
        return _finite_non_negative(value, info.field_name)


class AnomalyResult(BaseModel):
    tank_id: str
    anomaly_detected: bool
    anomaly_type: Optional[str] = None
    severity: str
    reasoning: str

    @field_validator("tank_id", "severity", "reasoning")
    @classmethod
    def validate_required_text(cls, value, info):
        return _required_text(value, info.field_name)

    @field_validator("anomaly_type")
    @classmethod
    def normalize_anomaly_type(cls, value):
        return None if value is None else str(value).strip().upper()


class SupplyOption(BaseModel):
    supplier_id: str
    available_quantity: float = Field(ge=0)
    distance_km: float = Field(ge=0)
    estimated_cost: float = Field(ge=0)
    name: Optional[str] = None
    available: Optional[bool] = None
    eta_minutes: Optional[int] = Field(default=None, ge=0)

    @field_validator("supplier_id")
    @classmethod
    def validate_supplier_id(cls, value):
        return _required_text(value, "supplier_id")


class SupplyResult(BaseModel):
    tank_id: str
    suppliers: List[SupplyOption]
    recommended_supplier: Optional[str] = None
    reasoning: str

    @field_validator("tank_id", "reasoning")
    @classmethod
    def validate_text(cls, value, info):
        return _required_text(value, info.field_name)

    @field_validator("recommended_supplier")
    @classmethod
    def normalize_recommended_supplier(cls, value):
        return None if value is None else str(value).strip()

    @model_validator(mode="after")
    def validate_recommendation(self):
        ids = {supplier.supplier_id for supplier in self.suppliers}
        if self.recommended_supplier is not None and self.recommended_supplier not in ids:
            raise ValueError(
                "recommended_supplier must refer to a supplier in suppliers."
            )
        return self


class AllocationResult(BaseModel):
    tank_id: str
    allocated_quantity: float = Field(gt=0)
    supplier_id: str
    priority: str
    reasoning: str

    @field_validator("tank_id", "supplier_id", "priority", "reasoning")
    @classmethod
    def validate_text(cls, value, info):
        return _required_text(value, info.field_name)


class DeliveryResult(BaseModel):
    tank_id: str
    supplier_id: str
    quantity: float = Field(ge=0)
    status: str
    estimated_arrival: str

    @field_validator("tank_id", "supplier_id", "status", "estimated_arrival")
    @classmethod
    def validate_text(cls, value, info):
        return _required_text(value, info.field_name)

    @field_validator("status")
    @classmethod
    def normalize_status(cls, value):
        return str(value).strip().upper().replace(" ", "_")


class VerificationResult(BaseModel):
    tank_id: str
    delivered_quantity: float = Field(ge=0)
    verified: bool
    discrepancy: float
    status: str
    reasoning: str

    @field_validator("tank_id", "status", "reasoning")
    @classmethod
    def validate_text(cls, value, info):
        return _required_text(value, info.field_name)

    @field_validator("status")
    @classmethod
    def normalize_status(cls, value):
        return str(value).strip().upper().replace(" ", "_")


class ManagerApprovalResult(BaseModel):
    tank_id: str
    approved: bool
    manager_decision: str
    reasoning: str

    @field_validator("tank_id", "manager_decision", "reasoning")
    @classmethod
    def validate_text(cls, value, info):
        return _required_text(value, info.field_name)

    @field_validator("manager_decision")
    @classmethod
    def normalize_decision(cls, value):
        return str(value).strip().upper()


class ReplanningResult(BaseModel):
    tank_id: str
    action: str
    reason: str

    @field_validator("tank_id", "action", "reason")
    @classmethod
    def validate_text(cls, value, info):
        return _required_text(value, info.field_name)

    @field_validator("action")
    @classmethod
    def normalize_action(cls, value):
        return str(value).strip().upper()
