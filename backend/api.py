from database import initialize_database

initialize_database()


def get_tanks():
    return {"message": "Tanks endpoint ready"}


def get_consumption():
    return {"message": "Consumption endpoint ready"}


def get_suppliers():
    return {"message": "Suppliers endpoint ready"}


def get_alerts():
    return {"message": "Alerts endpoint ready"}


def get_events():
    return {"message": "Events endpoint ready"}


def create_delivery():
    return {"message": "Delivery endpoint ready"}


def approve_delivery():
    return {"message": "Approval endpoint ready"}


def verify_delivery():
    return {"message": "Verification endpoint ready"}


def get_agent_runs():
    return {"message": "Agent runs endpoint ready"}