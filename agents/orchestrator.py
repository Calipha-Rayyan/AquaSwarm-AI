from agents.demand_agent import predict_shortage
from agents.anomaly_agent import detect_anomaly
from agents.supply_agent import evaluate_suppliers
from agents.allocation_agent import allocate_water


def run_operational_analysis(
    tanks,
    consumption,
    suppliers,
    spike_site=None
):
    results = []

    for _, tank in tanks.iterrows():

        site_id = int(tank["site_id"])

        site_consumption = consumption[
            consumption["site_id"] == site_id
        ]

        if site_consumption.empty:
            average = 0
        else:
            average = float(
                site_consumption["amount"].mean()
            )

        spike_factor = 1.0

        if spike_site == site_id:
            spike_factor = 2.0

        prediction = predict_shortage(
            tank,
            average,
            spike_factor
        )

        anomaly = detect_anomaly(
            average,
            average * spike_factor
        )

        required_quantity = max(
            0,
            float(tank["capacity"]) * 0.80
            - float(tank["current_level"])
        )

        supplier_results = evaluate_suppliers(
            suppliers,
            required_quantity
        )

        allocation = allocate_water(
            required_quantity,
            supplier_results
        )

        results.append({
            "site_id": site_id,
            "prediction": prediction,
            "anomaly": anomaly,
            "suppliers": supplier_results,
            "allocation": allocation
        })

    return results