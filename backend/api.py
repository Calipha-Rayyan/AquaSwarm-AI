import pandas as pd
from datetime import datetime

from backend.database import get_connection, initialize_database


initialize_database()


def get_tanks():
    connection = get_connection()

    data = pd.read_sql_query(
        "SELECT * FROM tanks",
        connection
    )

    connection.close()

    return data.to_dict(orient="records")


def get_consumption():
    connection = get_connection()

    data = pd.read_sql_query(
        "SELECT * FROM consumption",
        connection
    )

    connection.close()

    return data.to_dict(orient="records")


def get_suppliers():
    connection = get_connection()

    data = pd.read_sql_query(
        "SELECT * FROM suppliers",
        connection
    )

    connection.close()

    return data.to_dict(orient="records")


def get_alerts():
    connection = get_connection()

    data = pd.read_sql_query(
        """
        SELECT *
        FROM alerts
        ORDER BY id DESC
        """,
        connection
    )

    connection.close()

    return data.to_dict(orient="records")


def get_events():
    return {
        "event": "AquaSwarm operational event",
        "timestamp": datetime.now().isoformat()
    }


def get_deliveries():
    connection = get_connection()

    data = pd.read_sql_query(
        """
        SELECT *
        FROM delivery_requests
        ORDER BY id DESC
        """,
        connection
    )

    connection.close()

    return data.to_dict(orient="records")


def create_delivery(site_id, supplier_id, quantity):
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO delivery_requests
        (site_id, supplier_id, quantity, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            site_id,
            supplier_id,
            quantity,
            "requested"
        )
    )

    delivery_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return {
        "id": delivery_id,
        "site_id": site_id,
        "supplier_id": supplier_id,
        "quantity": quantity,
        "status": "requested"
    }


def approve_delivery(delivery_id, approved, approved_by):
    connection = get_connection()

    cursor = connection.cursor()

    status = "approved" if approved else "rejected"

    cursor.execute(
        """
        INSERT INTO approvals
        (delivery_id, approved, approved_by)
        VALUES (?, ?, ?)
        """,
        (
            delivery_id,
            int(approved),
            approved_by
        )
    )

    cursor.execute(
        """
        UPDATE delivery_requests
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            delivery_id
        )
    )

    connection.commit()
    connection.close()

    return {
        "delivery_id": delivery_id,
        "status": status,
        "approved_by": approved_by
    }


def update_delivery(delivery_id, status):
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE delivery_requests
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            delivery_id
        )
    )

    connection.commit()
    connection.close()

    return {
        "delivery_id": delivery_id,
        "status": status
    }


def verify_delivery(
    delivery_id,
    expected_quantity,
    actual_quantity
):
    tolerance = expected_quantity * 0.10

    difference = abs(
        expected_quantity - actual_quantity
    )

    if difference <= tolerance:
        status = "passed"
    else:
        status = "exception"

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO verifications
        (
            delivery_id,
            expected_quantity,
            actual_quantity,
            status
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            delivery_id,
            expected_quantity,
            actual_quantity,
            status
        )
    )

    connection.commit()
    connection.close()

    return {
        "delivery_id": delivery_id,
        "expected_quantity": expected_quantity,
        "actual_quantity": actual_quantity,
        "difference": difference,
        "status": status
    }


def get_verifications():
    connection = get_connection()

    data = pd.read_sql_query(
        """
        SELECT *
        FROM verifications
        ORDER BY id DESC
        """,
        connection
    )

    connection.close()

    return data.to_dict(orient="records")


def get_agent_runs():
    connection = get_connection()

    data = pd.read_sql_query(
        """
        SELECT *
        FROM agent_runs
        ORDER BY id DESC
        """,
        connection
    )

    connection.close()

    return data.to_dict(orient="records")


def log_agent_run(agent_name, status):
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO agent_runs
        (agent_name, status, timestamp)
        VALUES (?, ?, ?)
        """,
        (
            agent_name,
            status,
            datetime.now().isoformat()
        )
    )

    connection.commit()
    connection.close()