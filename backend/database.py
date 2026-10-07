from pathlib import Path
import csv
import shutil
import sqlite3
from datetime import datetime, timezone
from typing import Any, Iterable

# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

# Keep the project's existing database filename.
DATABASE_PATH = PROJECT_ROOT / "aquaswarm.db"
DATABASE_NAME = str(DATABASE_PATH)

SITES_CSV = DATA_DIR / "sites.csv"
TANKS_CSV = DATA_DIR / "tanks.csv"
CONSUMPTION_CSV = DATA_DIR / "consumption.csv"
SUPPLIERS_CSV = DATA_DIR / "suppliers.csv"

REQUIRED_COLUMNS = {
    "sites": {"site_id", "site_name", "location"},
    "tanks": {"id", "site_id", "capacity", "current_level"},
    "consumption": {"id", "site_id", "amount", "timestamp"},
    "suppliers": {"id", "name", "capacity", "available"},
}

REQUIRED_SCHEMA = {
    "sites": {
        "id", "name", "location", "manager_name", "created_at"
    },
    "tanks": {
        "id", "tank_code", "site_id", "name", "capacity",
        "current_level", "critical_threshold", "updated_at"
    },
    "consumption": {
        "id", "site_id", "tank_id", "amount", "timestamp", "source"
    },
    "suppliers": {
        "id", "supplier_code", "name", "capacity", "available",
        "distance_km", "estimated_cost", "eta_minutes",
        "phone", "last_updated"
    },
    "alerts": {
        "id", "site_id", "tank_id", "alert_type", "severity",
        "message", "status", "timestamp"
    },
    "delivery_requests": {
        "id", "site_id", "tank_id", "supplier_id", "quantity",
        "status", "estimated_arrival", "requested_at",
        "actual_quantity", "delivered_at", "notes"
    },
    "approvals": {
        "id", "delivery_request_id", "site_id", "tank_id",
        "proposed_quantity", "supplier_id", "status", "approved",
        "approved_by", "decision_timestamp", "decision_note"
    },
    "verifications": {
        "id", "delivery_request_id", "expected_quantity",
        "actual_quantity", "discrepancy", "verification_status",
        "verification_timestamp", "note"
    },
    "agent_runs": {
        "id", "agent_name", "status", "timestamp",
        "operation_run_id", "input_summary", "output_summary"
    },
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ============================================================
# GENERIC DATABASE HELPERS
# ============================================================

def query_all(
    sql: str,
    params: Iterable[Any] = (),
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [dict(row) for row in rows]


def query_one(
    sql: str,
    params: Iterable[Any] = (),
) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(sql, tuple(params)).fetchone()
        return dict(row) if row else None


def execute(
    sql: str,
    params: Iterable[Any] = (),
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(sql, tuple(params))
        conn.commit()
        return cursor.rowcount


def execute_returning_id(
    sql: str,
    params: Iterable[Any] = (),
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(sql, tuple(params))
        conn.commit()
        return int(cursor.lastrowid)


# ============================================================
# HELPERS
# ============================================================

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required data file was not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise ValueError(f"CSV file is empty: {path}")

    return rows


def validate_csv_headers(
    name: str,
    path: Path,
) -> None:
    rows = read_csv(path)
    actual = set(rows[0].keys())
    missing = REQUIRED_COLUMNS[name] - actual

    if missing:
        raise ValueError(
            f"{path.name} is missing required columns: "
            f"{sorted(missing)}"
        )


def normalize_bool(value: Any) -> int:
    return int(
        str(value).strip().lower()
        in {"1", "true", "yes", "available"}
    )


# ============================================================
# SCHEMA
# ============================================================

def create_schema() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        location TEXT NOT NULL,
        manager_name TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tanks (
        id INTEGER PRIMARY KEY,
        tank_code TEXT UNIQUE NOT NULL,
        site_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        capacity REAL NOT NULL CHECK (capacity > 0),
        current_level REAL NOT NULL CHECK (current_level >= 0),
        critical_threshold REAL NOT NULL DEFAULT 20,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (site_id)
            REFERENCES sites(id)
            ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS consumption (
        id INTEGER PRIMARY KEY,
        site_id INTEGER NOT NULL,
        tank_id INTEGER NOT NULL,
        amount REAL NOT NULL CHECK (amount >= 0),
        timestamp TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'CSV_IMPORT',
        FOREIGN KEY (site_id)
            REFERENCES sites(id)
            ON DELETE CASCADE,
        FOREIGN KEY (tank_id)
            REFERENCES tanks(id)
            ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY,
        supplier_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        capacity REAL NOT NULL CHECK (capacity > 0),
        available INTEGER NOT NULL DEFAULT 1,
        distance_km REAL NOT NULL DEFAULT 0,
        estimated_cost REAL NOT NULL DEFAULT 0,
        eta_minutes INTEGER NOT NULL DEFAULT 60,
        phone TEXT,
        last_updated TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL,
        tank_id INTEGER,
        alert_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'OPEN',
        timestamp TEXT NOT NULL,
        FOREIGN KEY (site_id)
            REFERENCES sites(id)
            ON DELETE CASCADE,
        FOREIGN KEY (tank_id)
            REFERENCES tanks(id)
            ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS delivery_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER NOT NULL,
        tank_id INTEGER NOT NULL,
        supplier_id INTEGER NOT NULL,
        quantity REAL NOT NULL CHECK (quantity > 0),
        status TEXT NOT NULL DEFAULT 'PENDING',
        estimated_arrival TEXT,
        requested_at TEXT NOT NULL,
        actual_quantity REAL,
        delivered_at TEXT,
        notes TEXT NOT NULL DEFAULT '',
        FOREIGN KEY (site_id)
            REFERENCES sites(id),
        FOREIGN KEY (tank_id)
            REFERENCES tanks(id),
        FOREIGN KEY (supplier_id)
            REFERENCES suppliers(id)
    );

    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        delivery_request_id INTEGER NOT NULL,
        site_id INTEGER NOT NULL,
        tank_id INTEGER NOT NULL,
        proposed_quantity REAL NOT NULL CHECK (proposed_quantity > 0),
        supplier_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        approved INTEGER,
        approved_by TEXT,
        decision_timestamp TEXT,
        decision_note TEXT NOT NULL DEFAULT '',
        FOREIGN KEY (delivery_request_id)
            REFERENCES delivery_requests(id)
            ON DELETE CASCADE,
        FOREIGN KEY (site_id)
            REFERENCES sites(id),
        FOREIGN KEY (tank_id)
            REFERENCES tanks(id),
        FOREIGN KEY (supplier_id)
            REFERENCES suppliers(id)
    );

    CREATE TABLE IF NOT EXISTS verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        delivery_request_id INTEGER NOT NULL,
        expected_quantity REAL NOT NULL,
        actual_quantity REAL NOT NULL,
        discrepancy REAL NOT NULL,
        verification_status TEXT NOT NULL DEFAULT 'PENDING',
        verification_timestamp TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT '',
        FOREIGN KEY (delivery_request_id)
            REFERENCES delivery_requests(id)
            ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS agent_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT NOT NULL,
        status TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        operation_run_id TEXT NOT NULL,
        input_summary TEXT NOT NULL DEFAULT '',
        output_summary TEXT NOT NULL DEFAULT ''
    );
    """

    with get_connection() as conn:
        conn.executescript(schema)
        conn.commit()


def table_columns(table_name: str) -> set[str]:
    with get_connection() as conn:
        rows = conn.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
        return {row["name"] for row in rows}


def schema_is_compatible() -> bool:
    for table_name, required in REQUIRED_SCHEMA.items():
        columns = table_columns(table_name)

        if not required.issubset(columns):
            return False

    return True


def backup_incompatible_database() -> Path:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = PROJECT_ROOT / (
        f"aquaswarm_legacy_{timestamp}.db"
    )

    shutil.copy2(
        DATABASE_PATH,
        backup_path,
    )

    DATABASE_PATH.unlink()

    return backup_path


# ============================================================
# CSV IMPORT
# ============================================================

def import_sites() -> None:
    rows = read_csv(SITES_CSV)

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO sites
            (id, name, location, manager_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    int(row["site_id"]),
                    row["site_name"].strip(),
                    row["location"].strip(),
                    row.get("manager_name", "").strip() or None,
                    utc_now(),
                )
                for row in rows
            ],
        )
        conn.commit()


def import_tanks() -> None:
    rows = read_csv(TANKS_CSV)

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO tanks
            (id, tank_code, site_id, name,
             capacity, current_level,
             critical_threshold, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    int(row["id"]),
                    f"TANK-{int(row['id']):03d}",
                    int(row["site_id"]),
                    f"Water Tank {int(row['id'])}",
                    float(row["capacity"]),
                    float(row["current_level"]),
                    20.0,
                    utc_now(),
                )
                for row in rows
            ],
        )
        conn.commit()


def import_consumption() -> None:
    rows = read_csv(CONSUMPTION_CSV)

    with get_connection() as conn:
        for row in rows:
            site_id = int(row["site_id"])

            # Current consumption.csv contains site_id but not tank_id.
            # Resolve the site's first tank deterministically.
            tank = conn.execute(
                """
                SELECT id
                FROM tanks
                WHERE site_id = ?
                ORDER BY id
                LIMIT 1
                """,
                (site_id,),
            ).fetchone()

            if tank is None:
                raise ValueError(
                    f"No tank found for site_id={site_id} "
                    f"while importing consumption data."
                )

            conn.execute(
                """
                INSERT INTO consumption
                (id, site_id, tank_id,
                 amount, timestamp, source)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["id"]),
                    site_id,
                    int(tank["id"]),
                    float(row["amount"]),
                    row["timestamp"].strip(),
                    "CSV_IMPORT",
                ),
            )

        conn.commit()


def _csv_float(row: dict, key: str, default: float) -> float:
    try:
        value = str(row.get(key, "")).strip()
        return float(value) if value else default
    except ValueError:
        return default


def import_suppliers() -> None:
    rows = read_csv(SUPPLIERS_CSV)

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO suppliers
            (id, supplier_code, name, capacity,
             available, distance_km,
             estimated_cost, eta_minutes,
             phone, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    int(row["id"]),
                    f"S-{int(row['id']):03d}",
                    row["name"].strip(),
                    float(row["capacity"]),
                    normalize_bool(row["available"]),
                    # Optional logistics columns; defaults keep old CSVs valid.
                    _csv_float(row, "distance_km", 0.0),
                    _csv_float(row, "estimated_cost", 0.0),
                    int(_csv_float(row, "eta_minutes", 60)),
                    (row.get("phone") or "").strip() or None,
                    utc_now(),
                )
                for row in rows
            ],
        )
        conn.commit()


def refresh_supplier_logistics() -> None:
    """Fill distance/cost/ETA from suppliers.csv for databases that were
    seeded before those columns existed (all-zero logistics only)."""
    rows = read_csv(SUPPLIERS_CSV)
    if not any(
        _csv_float(r, "distance_km", 0) or _csv_float(r, "estimated_cost", 0)
        for r in rows
    ):
        return

    stale = query_one(
        "SELECT COUNT(*) AS count FROM suppliers "
        "WHERE distance_km > 0 OR estimated_cost > 0"
    )["count"]
    if stale:
        return

    with get_connection() as conn:
        for row in rows:
            conn.execute(
                "UPDATE suppliers SET distance_km = ?, estimated_cost = ?, "
                "eta_minutes = ?, last_updated = ? WHERE id = ?",
                (
                    _csv_float(row, "distance_km", 0.0),
                    _csv_float(row, "estimated_cost", 0.0),
                    int(_csv_float(row, "eta_minutes", 60)),
                    utc_now(),
                    int(row["id"]),
                ),
            )
        conn.commit()


def seed_if_needed() -> None:
    """Import any seed table that is empty.

    Each importer is all-or-nothing, so a failed import can never leave a
    half-filled table that blocks every later start (the old behaviour only
    seeded when `sites` was empty, which could leave the backend unusable).
    """
    importers = (
        ("sites", SITES_CSV, import_sites),
        ("tanks", TANKS_CSV, import_tanks),
        ("consumption", CONSUMPTION_CSV, import_consumption),
        ("suppliers", SUPPLIERS_CSV, import_suppliers),
    )

    for table, path, importer in importers:
        count = query_one(f"SELECT COUNT(*) AS count FROM {table}")["count"]
        if count == 0:
            validate_csv_headers(table, path)
            importer()


def import_csv_data() -> None:
    for name, path in (
        ("sites", SITES_CSV),
        ("tanks", TANKS_CSV),
        ("consumption", CONSUMPTION_CSV),
        ("suppliers", SUPPLIERS_CSV),
    ):
        validate_csv_headers(name, path)

    import_sites()
    import_tanks()
    import_consumption()
    import_suppliers()


# ============================================================
# VALIDATION
# ============================================================

def validate_database() -> None:
    for table in ("sites", "tanks", "consumption", "suppliers"):
        row = query_one(f"SELECT COUNT(*) AS count FROM {table}")

        if int(row["count"]) == 0:
            raise RuntimeError(f"{table}: table is empty after seeding.")

    orphan_tanks = query_one(
        """
        SELECT COUNT(*) AS count
        FROM tanks
        WHERE site_id NOT IN (
            SELECT id FROM sites
        )
        """
    )["count"]

    if orphan_tanks:
        raise RuntimeError(
            "Found tanks referencing unknown sites."
        )

    orphan_consumption = query_one(
        """
        SELECT COUNT(*) AS count
        FROM consumption
        WHERE tank_id NOT IN (
            SELECT id FROM tanks
        )
        """
    )["count"]

    if orphan_consumption:
        raise RuntimeError(
            "Found consumption records referencing unknown tanks."
        )


# ============================================================
# INITIALIZATION
# ============================================================

def initialize_database() -> None:
    """
    Create a compatible database and import canonical CSV data.

    Existing legacy aquaswarm.db files are backed up automatically
    and replaced with the current schema because the old prototype
    schema cannot safely satisfy the new API contract.
    """

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if DATABASE_PATH.exists():
        try:
            if not schema_is_compatible():
                backup_incompatible_database()
        except sqlite3.DatabaseError:
            backup_incompatible_database()

    create_schema()
    seed_if_needed()
    refresh_supplier_logistics()
    validate_database()


if __name__ == "__main__":
    initialize_database()

    print("=" * 60)
    print("AquaSwarm Backend Database")
    print("=" * 60)
    print(f"Database : {DATABASE_PATH}")
    print(f"Data     : {DATA_DIR}")
    print()
    print("Database initialized and validated successfully.")

    for table in (
        "sites",
        "tanks",
        "consumption",
        "suppliers",
    ):
        row = query_one(
            f"SELECT COUNT(*) AS count FROM {table}"
        )
        print(f"{table:<15}: {row['count']} rows")