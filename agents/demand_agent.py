def predict_shortage(tank, average_consumption, spike_factor=1.0):
    current_level = float(tank["current_level"])
    capacity = float(tank["capacity"])

    adjusted_consumption = average_consumption * spike_factor

    if adjusted_consumption <= 0:
        hours_to_empty = None
    else:
        hours_to_empty = current_level / adjusted_consumption

    level_percent = (current_level / capacity) * 100

    if hours_to_empty is not None and hours_to_empty <= 6:
        risk = "CRITICAL"
    elif hours_to_empty is not None and hours_to_empty <= 12:
        risk = "HIGH"
    elif hours_to_empty is not None and hours_to_empty <= 24:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return {
        "site_id": int(tank["site_id"]),
        "level_percent": round(level_percent, 1),
        "average_consumption": round(adjusted_consumption, 2),
        "hours_to_empty": (
            round(hours_to_empty, 1)
            if hours_to_empty is not None
            else None
        ),
        "risk": risk,
    }