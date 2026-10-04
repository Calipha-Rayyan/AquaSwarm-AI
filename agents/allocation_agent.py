def allocate_water(required_quantity, suppliers):
    remaining = float(required_quantity)
    allocations = []

    for supplier in suppliers:
        if remaining <= 0:
            break

        if not supplier["available"]:
            continue

        capacity = float(supplier["capacity"])

        quantity = min(
            remaining,
            capacity
        )

        allocations.append({
            "supplier_id": supplier["id"],
            "supplier_name": supplier["name"],
            "quantity": quantity
        })

        remaining -= quantity

    return {
        "requested": float(required_quantity),
        "allocated": float(required_quantity - remaining),
        "remaining": float(remaining),
        "allocations": allocations,
        "fully_allocated": remaining <= 0
    }