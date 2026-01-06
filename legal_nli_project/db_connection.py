"""db_connection.py
Try to connect to SQL Server via pyodbc; if unavailable or connection fails,
fall back to a local SQLite database file `legal_rules_fallback.db` with a
minimal `legal_rules` table so tests can run without external dependencies.
"""
import os
import sqlite3

try:
    import pyodbc
except Exception:
    pyodbc = None

FALLBACK_DB = os.path.join(os.path.dirname(__file__), "legal_rules_fallback.db")


def _ensure_fallback_db():
    conn = sqlite3.connect(FALLBACK_DB)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS legal_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            act_name TEXT,
            section TEXT,
            rule_text TEXT,
            risk_level TEXT,
            domain TEXT
        )
        """
    )
    # If table is empty, insert a few sample rows useful for local testing
    cur.execute("SELECT COUNT(1) FROM legal_rules")
    if cur.fetchone()[0] == 0:
        samples = [
            ("Industrial Disputes Act, No. 43 of 1950", "31F", "The Commissioner must investigate and attempt to settle any industrial dispute that exists or may arise.", "MEDIUM", "EMPLOYMENT"),
            ("Industrial Disputes Act, No. 43 of 1950", "32A(a)", "The Commissioner may refer any industrial dispute for conciliation, arbitration, or to a labour tribunal.", "MEDIUM", "EMPLOYMENT"),
            ("Industrial Disputes Act, No. 43 of 1950", "2", "Definitions and scope of the Act.", "LOW", "EMPLOYMENT"),
            ("Industrial Disputes Act, No. 43 of 1950", "11", "Settlement terms and binding effect.", "LOW", "EMPLOYMENT"),
        ]
        cur.executemany("INSERT INTO legal_rules (act_name, section, rule_text, risk_level, domain) VALUES (?, ?, ?, ?, ?)", samples)
        conn.commit()
    return conn


def get_connection():
    """Return a DB connection. Prefer pyodbc/sqlserver; otherwise use SQLite fallback."""
    if pyodbc:
        try:
            conn = pyodbc.connect(
                "DRIVER={ODBC Driver 17 for SQL Server};"
                "SERVER=localhost\\SQLEXPRESS;"
                "DATABASE=LegalComplianceDB;"
                "Trusted_Connection=yes;"
            )
            return conn
        except Exception as e:
            print("Warning: failed to connect via pyodbc, using SQLite fallback:", e)

    # Fallback to SQLite file-based DB
    return _ensure_fallback_db()
