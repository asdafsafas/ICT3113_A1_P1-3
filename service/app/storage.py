"""SQLite storage. Baseline: a new connection per call, plain LIKE search, no indexes beyond the key."""

import sqlite3

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    narrative   TEXT NOT NULL,
    category    TEXT NOT NULL,
    model       TEXT NOT NULL,
    request_id  TEXT NOT NULL,
    created_at  TEXT NOT NULL
)
"""


def connect():
    conn = sqlite3.connect(config.DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(SCHEMA)


def insert_ticket(narrative, category, model, request_id, created_at):
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO tickets (narrative, category, model, request_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (narrative, category, model, request_id, created_at),
        )
        return cur.lastrowid


def search(query, limit):
    pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, category, created_at, narrative FROM tickets "
            "WHERE narrative LIKE ? ESCAPE '\\' ORDER BY id DESC LIMIT ?",
            (pattern, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def counts_by_category():
    with connect() as conn:
        rows = conn.execute("SELECT category, COUNT(*) AS n FROM tickets GROUP BY category").fetchall()
    return {r["category"]: r["n"] for r in rows}
