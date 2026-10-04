import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FOLDER = PROJECT_ROOT / "data"


def load_tanks():
    return pd.read_csv(DATA_FOLDER / "tanks.csv")


def load_suppliers():
    return pd.read_csv(DATA_FOLDER / "suppliers.csv")


def load_consumption():
    return pd.read_csv(DATA_FOLDER / "consumption.csv")


def calculate_tank_percentage(current_level, capacity):
    if capacity <= 0:
        return 0

    return (current_level / capacity) * 100


def calculate_average_consumption(consumption, site_id):
    site_data = consumption[
        consumption["site_id"] == site_id
    ]

    if site_data.empty:
        return 0

    return site_data["amount"].mean()


def calculate_time_to_empty(current_level, average_consumption):
    if average_consumption <= 0:
        return None

    return current_level / average_consumption


def detect_alerts():
    tanks = load_tanks()
    consumption = load_consumption()

    alerts = []

    for _, tank in tanks.iterrows():
        site_id = int(tank["site_id"])
        capacity = float(tank["capacity"])
        current_level = float(tank["current_level"])

        percentage = calculate_tank_percentage(
            current_level,
            capacity
        )

        average_consumption = calculate_average_consumption(
            consumption,
            site_id
        )

        if percentage <= 20:
            severity = "CRITICAL"
        elif percentage <= 35:
            severity = "HIGH"
        else:
            continue

        alerts.append({
            "site_id": site_id,
            "message": f"Tank level is {percentage:.1f}%",
            "severity": severity
        })

    return alerts


def find_available_suppliers():
    suppliers = load_suppliers()

    return suppliers[
        suppliers["available"] == 1
    ].to_dict(orient="records")


def rank_suppliers():
    suppliers = load_suppliers()

    available = suppliers[
        suppliers["available"] == 1
    ].copy()

    if available.empty:
        return []

    available["score"] = (
        available["capacity"] /
        available["capacity"].max()
    )

    available = available.sort_values(
        by="score",
        ascending=False
    )

    return available.to_dict(orient="records")