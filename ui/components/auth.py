from __future__ import annotations

import hmac
import os
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


def authenticate(email: str, password: str) -> bool:
    """Authenticate the prototype manager session from environment settings."""
    expected_email = os.getenv(
        "AQUASWARM_DEMO_EMAIL",
        "demo@aquaswarm.ai",
    ).strip().lower()
    expected_password = os.getenv(
        "AQUASWARM_DEMO_PASSWORD",
        "AquaSwarm@123",
    )

    return (
        hmac.compare_digest(email.strip().lower(), expected_email)
        and hmac.compare_digest(password, expected_password)
    )


def get_tank_options() -> list[str]:
    """Load tank codes from the backend and fall back to data/tanks.csv."""
    backend_url = os.getenv(
        "AQUASWARM_API_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    try:
        from backend.client import BackendClient

        from config.settings import AQUASWARM_BACKEND_TIMEOUT

        rows = BackendClient(
            base_url=backend_url,
            timeout=AQUASWARM_BACKEND_TIMEOUT,
        ).get_tanks()
        values = [
            str(row["tank_code"])
            for row in rows
            if row.get("tank_code")
        ]
        if values:
            return list(dict.fromkeys(values))
    except Exception:
        pass

    path = DATA_DIR / "tanks.csv"
    if not path.exists():
        return []

    data = pd.read_csv(path)

    if "tank_code" in data.columns:
        return (
            data["tank_code"].astype(str).dropna().drop_duplicates().tolist()
        )

    if "id" in data.columns:
        return [
            f"TANK-{int(value):03d}"
            for value in data["id"].dropna().drop_duplicates()
        ]

    return []