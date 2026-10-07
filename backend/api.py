from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.security import cors_origins, docs_enabled, require_api_key
from backend.database import (
    initialize_database,
    query_all,
    query_one,
    execute,
    execute_returning_id,
)

_DOCS = docs_enabled()

app = FastAPI(
    title="AquaSwarm AI Backend",
    description="Water operations and multi-agent data API",
    version="1.1.0",
    # Every route except /health requires the X-API-Key header.
    dependencies=[Depends(require_api_key)],
    # Interactive docs are off unless AQUASWARM_ENABLE_DOCS=true.
    docs_url="/docs" if _DOCS else None,
    redoc_url=None,
    openapi_url="/openapi.json" if _DOCS else None,
)

# Origins come from AQUASWARM_CORS_ORIGINS (no wildcard).
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["X-API-Key", "Content-Type"],
)

initialize_database()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# REQUEST MODELS
# ============================================================

class DeliveryRequestIn(BaseModel):
    site_id: int
    tank_code: str
    supplier_code: str
    quantity: float = Field(gt=0)
    estimated_arrival: Optional[str] = None
    notes: str = ""


class ApprovalIn(BaseModel):
    delivery_request_id: int
    approved: bool
    approved_by: str = Field(min_length=1)
    decision_note: str = ""


class VerificationIn(BaseModel):
    delivery_request_id: int
    expected_quantity: float = Field(ge=0)
    actual_quantity: float = Field(ge=0)
    note: str = ""


class DeliveryStatusIn(BaseModel):
    status: str
    actual_quantity: Optional[float] = Field(
        default=None,
        ge=0,
    )
    notes: str = ""


class AgentRunIn(BaseModel):
    agent_name: str = Field(min_length=1)
    status: str = Field(min_length=1)
    operation_run_id: str = Field(min_length=1)
    input_summary: str = ""
    output_summary: str = ""


class AlertIn(BaseModel):
    site_id: int
    tank_code: Optional[str] = None
    alert_type: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    message: str = Field(min_length=1)


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "AquaSwarm Backend",
        "timestamp": now(),
    }


# ============================================================
# SITES
# ============================================================

@app.get("/sites")
def get_sites():
    return query_all(
        "SELECT * FROM sites ORDER BY id"
    )


# ============================================================
# TANKS
# ============================================================

@app.get("/tanks")
def get_tanks(
    site_id: Optional[int] = None,
):
    sql = """
        SELECT
            tanks.*,
            sites.name AS site_name,
            sites.location
        FROM tanks
        JOIN sites
            ON tanks.site_id = sites.id
    """

    if site_id is not None:
        sql += """
            WHERE tanks.site_id = ?
            ORDER BY tanks.id
        """
        return query_all(
            sql,
            (site_id,),
        )

    sql += " ORDER BY tanks.id"
    return query_all(sql)


# ============================================================
# CONSUMPTION
# ============================================================

@app.get("/consumption")
def get_consumption(
    site_id: Optional[int] = None,
    tank_code: Optional[str] = None,
    limit: int = 100,
):
    limit = max(1, min(limit, 1000))

    sql = """
        SELECT
            consumption.*,
            tanks.tank_code,
            sites.name AS site_name
        FROM consumption
        JOIN tanks
            ON consumption.tank_id = tanks.id
        JOIN sites
            ON consumption.site_id = sites.id
        WHERE 1 = 1
    """

    params = []

    if site_id is not None:
        sql += " AND consumption.site_id = ?"
        params.append(site_id)

    if tank_code:
        sql += " AND tanks.tank_code = ?"
        params.append(tank_code)

    sql += """
        ORDER BY consumption.timestamp DESC
        LIMIT ?
    """

    params.append(limit)

    return query_all(
        sql,
        params,
    )


# ============================================================
# SUPPLIERS
# ============================================================

@app.get("/suppliers")
def get_suppliers(
    available_only: bool = False,
):
    sql = "SELECT * FROM suppliers"

    if available_only:
        sql += " WHERE available = 1"

    sql += " ORDER BY id"

    return query_all(sql)


# ============================================================
# ALERTS
# ============================================================

@app.get("/alerts")
def get_alerts(
    status: Optional[str] = None,
):
    sql = """
        SELECT
            alerts.*,
            sites.name AS site_name,
            tanks.tank_code
        FROM alerts
        JOIN sites
            ON alerts.site_id = sites.id
        LEFT JOIN tanks
            ON alerts.tank_id = tanks.id
        WHERE 1 = 1
    """

    params = []

    if status:
        sql += " AND alerts.status = ?"
        params.append(status.upper())

    sql += " ORDER BY alerts.timestamp DESC"

    return query_all(
        sql,
        params,
    )


@app.post("/alerts")
def create_alert(
    payload: AlertIn,
):
    site = query_one(
        "SELECT id FROM sites WHERE id = ?",
        (payload.site_id,),
    )

    if not site:
        raise HTTPException(
            status_code=404,
            detail="Site not found",
        )

    tank_id = None

    if payload.tank_code:
        tank = query_one(
            """
            SELECT id, site_id
            FROM tanks
            WHERE tank_code = ?
            """,
            (payload.tank_code,),
        )

        if not tank:
            raise HTTPException(
                status_code=404,
                detail="Tank not found",
            )

        if tank["site_id"] != payload.site_id:
            raise HTTPException(
                status_code=400,
                detail="Tank does not belong to the selected site",
            )

        tank_id = tank["id"]

    alert_id = execute_returning_id(
        """
        INSERT INTO alerts
        (site_id, tank_id, alert_type,
         severity, message, status, timestamp)
        VALUES (?, ?, ?, ?, ?, 'OPEN', ?)
        """,
        (
            payload.site_id,
            tank_id,
            payload.alert_type,
            payload.severity.upper(),
            payload.message,
            now(),
        ),
    )

    return query_one(
        "SELECT * FROM alerts WHERE id = ?",
        (alert_id,),
    )


# ============================================================
# EVENTS
# ============================================================

@app.get("/events")
def get_events(
    limit: int = 100,
):
    limit = max(1, min(limit, 1000))

    return query_all(
        """
        SELECT
            id,
            'AGENT_RUN' AS event_type,
            agent_name AS title,
            status,
            timestamp,
            operation_run_id
        FROM agent_runs

        UNION ALL

        SELECT
            id,
            'ALERT' AS event_type,
            message AS title,
            severity AS status,
            timestamp,
            NULL AS operation_run_id
        FROM alerts

        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,),
    )


# ============================================================
# DELIVERY REQUESTS
# ============================================================

@app.post("/delivery-requests")
def create_delivery_request(
    payload: DeliveryRequestIn,
):
    tank = query_one(
        """
        SELECT id, site_id
        FROM tanks
        WHERE tank_code = ?
        """,
        (payload.tank_code,),
    )

    if not tank:
        raise HTTPException(
            status_code=404,
            detail="Tank not found",
        )

    if tank["site_id"] != payload.site_id:
        raise HTTPException(
            status_code=400,
            detail="Tank does not belong to the selected site",
        )

    supplier = query_one(
        """
        SELECT id, capacity, available
        FROM suppliers
        WHERE supplier_code = ?
        """,
        (payload.supplier_code,),
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    if not supplier["available"]:
        raise HTTPException(
            status_code=400,
            detail="Supplier is unavailable",
        )

    if payload.quantity > supplier["capacity"]:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds supplier capacity",
        )

    request_id = execute_returning_id(
        """
        INSERT INTO delivery_requests
        (site_id, tank_id, supplier_id,
         quantity, status,
         estimated_arrival, requested_at, notes)
        VALUES (?, ?, ?, ?, 'PENDING', ?, ?, ?)
        """,
        (
            payload.site_id,
            tank["id"],
            supplier["id"],
            payload.quantity,
            payload.estimated_arrival,
            now(),
            payload.notes,
        ),
    )

    return query_one(
        """
        SELECT
            dr.*,
            tanks.tank_code,
            sites.name AS site_name,
            suppliers.supplier_code,
            suppliers.name AS supplier_name
        FROM delivery_requests dr
        JOIN tanks
            ON dr.tank_id = tanks.id
        JOIN sites
            ON dr.site_id = sites.id
        JOIN suppliers
            ON dr.supplier_id = suppliers.id
        WHERE dr.id = ?
        """,
        (request_id,),
    )


@app.get("/delivery-requests")
def get_delivery_requests():
    return query_all(
        """
        SELECT
            dr.*,
            tanks.tank_code,
            sites.name AS site_name,
            suppliers.supplier_code,
            suppliers.name AS supplier_name
        FROM delivery_requests dr
        JOIN tanks
            ON dr.tank_id = tanks.id
        JOIN sites
            ON dr.site_id = sites.id
        JOIN suppliers
            ON dr.supplier_id = suppliers.id
        ORDER BY dr.requested_at DESC
        """
    )


# ============================================================
# MANAGER APPROVAL
# ============================================================

@app.post("/approvals")
def create_approval(
    payload: ApprovalIn,
):
    delivery = query_one(
        """
        SELECT *
        FROM delivery_requests
        WHERE id = ?
        """,
        (payload.delivery_request_id,),
    )

    if not delivery:
        raise HTTPException(
            status_code=404,
            detail="Delivery request not found",
        )

    if delivery["status"] != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Only pending delivery requests can be approved or rejected",
        )

    decision = (
        "APPROVED"
        if payload.approved
        else "REJECTED"
    )

    approval_id = execute_returning_id(
        """
        INSERT INTO approvals
        (delivery_request_id, site_id, tank_id,
         proposed_quantity, supplier_id,
         status, approved,
         approved_by, decision_timestamp,
         decision_note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            delivery["id"],
            delivery["site_id"],
            delivery["tank_id"],
            delivery["quantity"],
            delivery["supplier_id"],
            decision,
            int(payload.approved),
            payload.approved_by,
            now(),
            payload.decision_note,
        ),
    )

    execute(
        """
        UPDATE delivery_requests
        SET status = ?
        WHERE id = ?
        """,
        (
            decision,
            delivery["id"],
        ),
    )

    return query_one(
        "SELECT * FROM approvals WHERE id = ?",
        (approval_id,),
    )


@app.get("/approvals")
def get_approvals():
    return query_all(
        """
        SELECT
            approvals.*,
            tanks.tank_code,
            sites.name AS site_name,
            suppliers.supplier_code,
            suppliers.name AS supplier_name
        FROM approvals
        JOIN tanks
            ON approvals.tank_id = tanks.id
        JOIN sites
            ON approvals.site_id = sites.id
        JOIN suppliers
            ON approvals.supplier_id = suppliers.id
        ORDER BY approvals.id DESC
        """
    )


# ============================================================
# DELIVERY STATUS
# ============================================================

@app.patch("/delivery-requests/{request_id}/status")
def update_delivery_status(
    request_id: int,
    payload: DeliveryStatusIn,
):
    allowed_statuses = {
        "DISPATCHED",
        "DELIVERED",
        "CANCELLED",
        "DELIVERY_EXCEPTION",
    }

    status = payload.status.strip().upper()

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid delivery status. "
                "Allowed: DISPATCHED, DELIVERED, "
                "CANCELLED, DELIVERY_EXCEPTION"
            ),
        )

    delivery = query_one(
        """
        SELECT *
        FROM delivery_requests
        WHERE id = ?
        """,
        (request_id,),
    )

    if not delivery:
        raise HTTPException(
            status_code=404,
            detail="Delivery request not found",
        )

    current_status = delivery["status"].upper()

    valid_transitions = {
        "APPROVED": {"DISPATCHED", "CANCELLED"},
        "DISPATCHED": {
            "DELIVERED",
            "CANCELLED",
            "DELIVERY_EXCEPTION",
        },
        "DELIVERED": {
            "DELIVERY_EXCEPTION",
        },
    }

    if status not in valid_transitions.get(
        current_status,
        set(),
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid transition from "
                f"{current_status} to {status}"
            ),
        )

    if (
        status in {"DELIVERED", "DELIVERY_EXCEPTION"}
        and payload.actual_quantity is None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Actual quantity is required when "
                "delivery is completed"
            ),
        )

    timestamp = now()

    execute(
        """
        UPDATE delivery_requests
        SET
            status = ?,
            actual_quantity = COALESCE(
                ?,
                actual_quantity
            ),
            delivered_at =
                CASE
                    WHEN ? IN (
                        'DELIVERED',
                        'DELIVERY_EXCEPTION'
                    )
                    THEN ?
                    ELSE delivered_at
                END,
            notes = ?
        WHERE id = ?
        """,
        (
            status,
            payload.actual_quantity,
            status,
            timestamp,
            payload.notes,
            request_id,
        ),
    )

    return query_one(
        "SELECT * FROM delivery_requests WHERE id = ?",
        (request_id,),
    )


# ============================================================
# DELIVERY VERIFICATION
# ============================================================

@app.post("/verifications")
def create_verification(
    payload: VerificationIn,
):
    delivery = query_one(
        """
        SELECT *
        FROM delivery_requests
        WHERE id = ?
        """,
        (payload.delivery_request_id,),
    )

    if not delivery:
        raise HTTPException(
            status_code=404,
            detail="Delivery request not found",
        )

    if delivery["status"] != "DELIVERED":
        raise HTTPException(
            status_code=400,
            detail=(
                "Only delivered requests can be verified"
            ),
        )

    discrepancy = (
        payload.expected_quantity
        - payload.actual_quantity
    )

    verified = abs(discrepancy) <= 0.01

    verification_status = (
        "VERIFIED"
        if verified
        else "REVIEW_REQUIRED"
    )

    timestamp = now()

    verification_id = execute_returning_id(
        """
        INSERT INTO verifications
        (delivery_request_id,
         expected_quantity,
         actual_quantity,
         discrepancy,
         verification_status,
         verification_timestamp,
         note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.delivery_request_id,
            payload.expected_quantity,
            payload.actual_quantity,
            discrepancy,
            verification_status,
            timestamp,
            payload.note,
        ),
    )

    if verified:
        execute(
            """
            UPDATE delivery_requests
            SET
                status = 'VERIFIED',
                actual_quantity = ?,
                delivered_at = ?
            WHERE id = ?
            """,
            (
                payload.actual_quantity,
                timestamp,
                delivery["id"],
            ),
        )

        # Add verified water to the tank only after
        # successful quantity verification.
        execute(
            """
            UPDATE tanks
            SET
                current_level = MIN(
                    capacity,
                    current_level + ?
                ),
                updated_at = ?
            WHERE id = ?
            """,
            (
                payload.actual_quantity,
                timestamp,
                delivery["tank_id"],
            ),
        )

    else:
        execute(
            """
            UPDATE delivery_requests
            SET
                status = 'DELIVERY_EXCEPTION',
                actual_quantity = ?,
                delivered_at = ?
            WHERE id = ?
            """,
            (
                payload.actual_quantity,
                timestamp,
                delivery["id"],
            ),
        )

    return query_one(
        """
        SELECT *
        FROM verifications
        WHERE id = ?
        """,
        (verification_id,),
    )


@app.get("/verifications")
def get_verifications():
    return query_all(
        """
        SELECT
            verifications.*,
            tanks.tank_code,
            sites.name AS site_name
        FROM verifications
        JOIN delivery_requests
            ON verifications.delivery_request_id
             = delivery_requests.id
        JOIN tanks
            ON delivery_requests.tank_id
             = tanks.id
        JOIN sites
            ON delivery_requests.site_id
             = sites.id
        ORDER BY verifications.id DESC
        """
    )


# ============================================================
# AGENT RUN HISTORY
# ============================================================

@app.post("/agent-runs")
def create_agent_run(
    payload: AgentRunIn,
):
    run_id = execute_returning_id(
        """
        INSERT INTO agent_runs
        (agent_name, status, timestamp,
         operation_run_id,
         input_summary, output_summary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload.agent_name,
            payload.status.upper(),
            now(),
            payload.operation_run_id,
            payload.input_summary,
            payload.output_summary,
        ),
    )

    return query_one(
        "SELECT * FROM agent_runs WHERE id = ?",
        (run_id,),
    )


@app.get("/agent-runs")
def get_agent_runs(
    limit: int = 200,
):
    limit = max(1, min(limit, 1000))

    return query_all(
        """
        SELECT *
        FROM agent_runs
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,),
    )