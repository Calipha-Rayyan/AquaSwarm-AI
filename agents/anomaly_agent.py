def detect_anomaly(normal_consumption, current_consumption):
    normal = float(normal_consumption)
    current = float(current_consumption)

    if normal <= 0:
        return {
            "is_anomaly": False,
            "deviation_percent": 0,
            "severity": "NORMAL",
            "reason": "No reliable baseline is available."
        }

    deviation = ((current - normal) / normal) * 100

    if deviation >= 50:
        severity = "CRITICAL"
        is_anomaly = True
    elif deviation >= 30:
        severity = "HIGH"
        is_anomaly = True
    elif deviation >= 15:
        severity = "MEDIUM"
        is_anomaly = True
    else:
        severity = "NORMAL"
        is_anomaly = False

    return {
        "is_anomaly": is_anomaly,
        "deviation_percent": round(deviation, 1),
        "severity": severity,
        "reason": (
            f"Consumption is {deviation:.1f}% "
            f"above the normal baseline."
        )
    }