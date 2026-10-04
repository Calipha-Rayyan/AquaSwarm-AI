from backend.services import (
    load_tanks,
    load_suppliers,
    load_consumption,
    detect_alerts,
    find_available_suppliers,
    rank_suppliers
)


print("AquaSwarm Services Test")
print("------------------------")

print("\nTanks:")
print(load_tanks())

print("\nSuppliers:")
print(load_suppliers())

print("\nConsumption:")
print(load_consumption())

print("\nAlerts:")
print(detect_alerts())

print("\nAvailable Suppliers:")
print(find_available_suppliers())

print("\nRanked Suppliers:")
print(rank_suppliers())

print("\nServices working successfully!")