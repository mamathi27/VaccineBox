import sqlite3

DATABASE = "database/vaccinebox.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Temperature Table
# -----------------------------
def create_table():

    conn = get_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS temperature_readings (

        reading_id INTEGER PRIMARY KEY AUTOINCREMENT,

        box_id TEXT NOT NULL,

        temperature_c REAL NOT NULL,

        breach_flag TEXT NOT NULL,

        location TEXT NOT NULL,

        recorded_at TEXT NOT NULL

    )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# Vaccine Inventory Table
# -----------------------------
def create_vaccine_table():

    conn = get_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS vaccines (

        vaccine_id INTEGER PRIMARY KEY AUTOINCREMENT,

        vaccine_name TEXT NOT NULL,

        manufacturer TEXT NOT NULL,

        batch_number TEXT NOT NULL,

        stock INTEGER NOT NULL,

        expiry_date TEXT NOT NULL

    )
    """)

    conn.commit()
    conn.close()