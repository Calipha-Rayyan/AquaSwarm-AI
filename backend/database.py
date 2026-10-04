import sqlite3

DATABASE_NAME = "aquaswarm.db"


def get_connection():
    return sqlite3.connect(DATABASE_NAME)


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tanks (
            id INTEGER PRIMARY KEY,
            site_id INTEGER NOT NULL,
            capacity REAL NOT NULL,
            current_level REAL NOT NULL,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consumption (
            id INTEGER PRIMARY KEY,
            site_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            capacity REAL NOT NULL,
            available INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY,
            site_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            severity TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_requests (
            id INTEGER PRIMARY KEY,
            site_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY,
            agent_name TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY,
            delivery_id INTEGER NOT NULL,
            approved INTEGER NOT NULL,
            approved_by TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verifications (
            id INTEGER PRIMARY KEY,
            delivery_id INTEGER NOT NULL,
            expected_quantity REAL NOT NULL,
            actual_quantity REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()