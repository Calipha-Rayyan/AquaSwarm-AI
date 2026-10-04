def evaluate_suppliers(suppliers, required_quantity):
    available = suppliers[
        suppliers["available"] == 1
    ].copy()

    if available.empty:
        return []

    available["capacity_score"] = (
        available["capacity"] / available["capacity"].max()
    )

    available["feasible"] = (
        available["capacity"] >= required_quantity
    )

    available["score"] = available["capacity_score"]

    available = available.sort_values(
        by=["feasible", "score"],
        ascending=[False, False]
    )

    results = []

    for _, supplier in available.iterrows():
        results.append({
            "id": int(supplier["id"]),
            "name": supplier["name"],
            "capacity": float(supplier["capacity"]),
            "available": True,
            "feasible": bool(supplier["feasible"]),
            "score": round(float(supplier["score"]), 2)
        })

    return results