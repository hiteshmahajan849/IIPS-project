"""Repository for the users table. Isolates SQL from business logic."""
from __future__ import annotations

import sqlite3
from typing import Optional

from werkzeug.security import generate_password_hash

from .db import get_db


def find_by_email(email: str) -> Optional[sqlite3.Row]:
    db = get_db()
    return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def find_by_id(user_id: int) -> Optional[sqlite3.Row]:
    db = get_db()
    return db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()


def list_all(role: Optional[str] = None) -> list[sqlite3.Row]:
    db = get_db()
    if role:
        return db.execute(
            "SELECT * FROM users WHERE role = ? ORDER BY name", (role,)
        ).fetchall()
    return db.execute("SELECT * FROM users ORDER BY role, name").fetchall()


def create(name: str, email: str, password: str, role: str,
           roll_no: Optional[str] = None, department: Optional[str] = None) -> int:
    db = get_db()
    cur = db.execute(
        """INSERT INTO users(name, email, password_hash, role, roll_no, department)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, email, generate_password_hash(password), role, roll_no, department),
    )
    db.commit()
    return cur.lastrowid


def enroll(user_id: int, course_id: int) -> None:
    db = get_db()
    db.execute(
        "INSERT OR IGNORE INTO enrollments(user_id, course_id) VALUES (?, ?)",
        (user_id, course_id),
    )
    db.commit()


def enrolled_courses(user_id: int) -> list[sqlite3.Row]:
    db = get_db()
    return db.execute(
        """SELECT c.* FROM courses c
           JOIN enrollments e ON e.course_id = c.course_id
           WHERE e.user_id = ?
           ORDER BY c.code""",
        (user_id,),
    ).fetchall()
