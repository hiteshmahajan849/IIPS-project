"""Repository for the feedback_cycles table."""
from __future__ import annotations

import sqlite3
from typing import Optional

from .db import get_db


def find_by_id(cycle_id: int) -> Optional[sqlite3.Row]:
    db = get_db()
    return db.execute("SELECT * FROM feedback_cycles WHERE cycle_id = ?", (cycle_id,)).fetchone()


def current_open_cycle() -> Optional[sqlite3.Row]:
    db = get_db()
    return db.execute(
        "SELECT * FROM feedback_cycles WHERE status = 'open' ORDER BY cycle_id DESC LIMIT 1"
    ).fetchone()


def list_all() -> list[sqlite3.Row]:
    db = get_db()
    return db.execute("SELECT * FROM feedback_cycles ORDER BY cycle_id DESC").fetchall()


def list_semesters_with_data() -> list[int]:
    db = get_db()
    rows = db.execute("SELECT DISTINCT semester FROM feedback_cycles ORDER BY semester").fetchall()
    return [r["semester"] for r in rows]


def create(semester: int, start_date: str, end_date: str) -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO feedback_cycles(semester, start_date, end_date, status) VALUES (?, ?, ?, 'open')",
        (semester, start_date, end_date),
    )
    db.commit()
    return cur.lastrowid


def close(cycle_id: int) -> None:
    db = get_db()
    db.execute("UPDATE feedback_cycles SET status = 'closed' WHERE cycle_id = ?", (cycle_id,))
    db.commit()
