"""
database.py
------------
SQLite connection management + helper functions for the prototype.

This is intentionally kept as raw sqlite3 (no ORM) to keep the
hackathon prototype simple and easy to inspect/debug.
"""

import sqlite3
import os
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "knee_prototype.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "..", "database", "schema.sql")


def init_db():
    """Create tables from schema.sql if they do not already exist."""
    with get_connection() as conn:
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())
        conn.commit()
        _seed_placeholder_implants(conn)


def _seed_placeholder_implants(conn):
    """
    Insert a small set of PLACEHOLDER implant sizing rows so the
    /implant-recommendation endpoint has something to match against
    out of the box.

    IMPORTANT: These dimensions are NOT sourced from any real
    manufacturer. They exist only so the matching pipeline can be
    demonstrated end-to-end. Replace via POST /implant-database
    with validated dimensions before any real use.
    """
    cur = conn.execute("SELECT COUNT(*) AS c FROM implants")
    count = cur.fetchone()["c"]
    if count > 0:
        return

    placeholder_rows = [
        # (system, component_type, size, femoral_width, femoral_ap, tibial_width, tibial_ap)
        ("PLACEHOLDER-System", "femoral", "S", 60.0, 55.0, None, None),
        ("PLACEHOLDER-System", "femoral", "M", 65.0, 60.0, None, None),
        ("PLACEHOLDER-System", "femoral", "L", 70.0, 65.0, None, None),
        ("PLACEHOLDER-System", "femoral", "XL", 75.0, 70.0, None, None),
        ("PLACEHOLDER-System", "tibial", "S", None, None, 65.0, 42.0),
        ("PLACEHOLDER-System", "tibial", "M", None, None, 70.0, 45.0),
        ("PLACEHOLDER-System", "tibial", "L", None, None, 75.0, 48.0),
        ("PLACEHOLDER-System", "tibial", "XL", None, None, 80.0, 51.0),
    ]
    conn.executemany(
        """
        INSERT INTO implants
            (implant_system, component_type, size,
             femoral_width, femoral_ap, tibial_width, tibial_ap, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'PLACEHOLDER data - replace with validated implant specs')
        """,
        [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in placeholder_rows],
    )
    conn.commit()


def _dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = _dict_factory
    try:
        yield conn
    finally:
        conn.close()