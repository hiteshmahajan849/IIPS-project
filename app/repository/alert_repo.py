"""Repository for the alerts table."""
from __future__ import annotations

import sqlite3

from .db import get_db


def exists_unacknowledged(course_id: int, cycle_id: int, reason: str) -> bool:
    db = get_db()
    row = db.execute(
        """SELECT 1 FROM alerts
           WHERE course_id = ? AND cycle_id = ? AND reason = ? AND acknowledged = 0""",
        (course_id, cycle_id, reason),
    ).fetchone()
    return row is not None


def create(course_id: int, cycle_id: int, reason: str) -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO alerts(course_id, cycle_id, reason) VALUES (?, ?, ?)",
        (course_id, cycle_id, reason),
    )
    db.commit()
    return cur.lastrowid


def list_all(acknowledged: bool | None = None) -> list[sqlite3.Row]:
    db = get_db()
    query = """SELECT a.*, c.code, c.name AS course_name, u.name AS faculty_name
               FROM alerts a
               JOIN courses c ON c.course_id = a.course_id
               JOIN users u ON u.user_id = c.faculty_id"""
    params: list = []
    if acknowledged is not None:
        query += " WHERE a.acknowledged = ?"
        params.append(int(acknowledged))
    query += " ORDER BY a.created_at DESC"
    return db.execute(query, params).fetchall()


def acknowledge(alert_id: int) -> None:
    db = get_db()
    db.execute("UPDATE alerts SET acknowledged = 1 WHERE alert_id = ?", (alert_id,))
    db.commit()
