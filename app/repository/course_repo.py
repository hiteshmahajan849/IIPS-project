"""Repository for the courses table."""
from __future__ import annotations

import sqlite3
from typing import Optional

from .db import get_db


def find_by_id(course_id: int) -> Optional[sqlite3.Row]:
    db = get_db()
    return db.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,)).fetchone()


def list_all() -> list[sqlite3.Row]:
    db = get_db()
    return db.execute(
        """SELECT c.*, u.name AS faculty_name FROM courses c
           JOIN users u ON u.user_id = c.faculty_id
           ORDER BY c.semester, c.code"""
    ).fetchall()


def list_by_faculty(faculty_id: int) -> list[sqlite3.Row]:
    db = get_db()
    return db.execute(
        "SELECT * FROM courses WHERE faculty_id = ? ORDER BY code", (faculty_id,)
    ).fetchall()


def create(code: str, name: str, semester: int, faculty_id: int) -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO courses(code, name, semester, faculty_id) VALUES (?, ?, ?, ?)",
        (code, name, semester, faculty_id),
    )
    db.commit()
    return cur.lastrowid


def is_owned_by_faculty(course_id: int, faculty_id: int) -> bool:
    row = find_by_id(course_id)
    return bool(row) and row["faculty_id"] == faculty_id
