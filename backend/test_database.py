import os
from pathlib import Path
import sqlite3

import pytest

os.environ.setdefault(
    "PYTHONPATH",
    str(Path(__file__).resolve().parents[1])
)

from backend import database


def test_database_initialization():
    database.initialize_database()

    assert database.DATABASE_PATH.exists()

    expected_counts = {
        "sites": 5,
        "tanks": 5,
        "consumption": 5,
        "suppliers": 3,
    }

    for table, expected in expected_counts.items():
        row = database.query_one(
            f"SELECT COUNT(*) AS count FROM {table}"
        )

        assert row["count"] == expected


def test_tank_site_relationships():
    rows = database.query_all(
        """
        SELECT
            tanks.tank_code,
            sites.name AS site_name
        FROM tanks
        JOIN sites
            ON tanks.site_id = sites.id
        ORDER BY tanks.id
        """
    )

    assert len(rows) == 5
    assert all(row["site_name"] for row in rows)


def test_consumption_has_valid_tanks():
    rows = database.query_all(
        """
        SELECT COUNT(*) AS count
        FROM consumption
        WHERE tank_id NOT IN (
            SELECT id FROM tanks
        )
        """
    )

    assert rows[0]["count"] == 0


if __name__ == "__main__":
    database.initialize_database()
    database.validate_database()
    print("AquaSwarm database smoke test passed.")
