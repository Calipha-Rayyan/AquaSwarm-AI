VALID_STATUSES = [
    "requested",
    "approved",
    "dispatched",
    "delivered",
    "rejected",
    "exception"
]


def next_delivery_status(current_status):
    transitions = {
        "requested": "approved",
        "approved": "dispatched",
        "dispatched": "delivered"
    }

    return transitions.get(current_status)


def delivery_summary(delivery):
    return {
        "delivery_id": delivery["id"],
        "site_id": delivery["site_id"],
        "supplier_id": delivery["supplier_id"],
        "quantity": delivery["quantity"],
        "status": delivery["status"]
    }