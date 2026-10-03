"""Repository for feedback, ratings, sentiment_results and submission_log.

Anonymity by design (FR-07, NFR-04): `feedback` and `ratings` never store a
user_id. `submission_log` records who-submitted-what only to block duplicate
submissions (FR-06) and is never joined against `feedback` by any query in
this module or in the dashboard/report services.
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from .db import get_db

ASPECT_NAMES = ("teaching", "content", "labs", "infrastructure", "assessment")


class DuplicateSubmissionError(Exception):
    """Raised when a student has already submitted feedback for this course+cycle."""


def has_submitted(user_id: int, course_id: int, cycle_id: int) -> bool:
    db = get_db()
    row = db.execute(
        "SELECT 1 FROM submission_log WHERE user_id = ? AND course_id = ? AND cycle_id = ?",
        (user_id, course_id, cycle_id),
    ).fetchone()
    return row is not None


def record_submission(user_id: int, course_id: int, cycle_id: int) -> None:
    """Logs that this student has submitted for this course+cycle.

    The composite primary key (user_id, course_id, cycle_id) is what actually
    enforces "one submission per student per course per cycle" (FR-06) even
    under concurrent requests; the has_submitted() pre-check above is only a
    fast, friendly path for the common case.
    """
    db = get_db()
    try:
        db.execute(
            "INSERT INTO submission_log(user_id, course_id, cycle_id, submitted_at) "
            "VALUES (?, ?, ?, datetime('now'))",
            (user_id, course_id, cycle_id),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        raise DuplicateSubmissionError() from exc


def create_feedback(course_id: int, cycle_id: int, comment: str) -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO feedback(course_id, cycle_id, comment, status) VALUES (?, ?, ?, 'submitted')",
        (course_id, cycle_id, comment),
    )
    db.commit()
    return cur.lastrowid


def add_ratings(feedback_id: int, scores: dict[str, int]) -> None:
    db = get_db()
    db.executemany(
        "INSERT INTO ratings(feedback_id, aspect, score) VALUES (?, ?, ?)",
        [(feedback_id, aspect, scores[aspect]) for aspect in ASPECT_NAMES if aspect in scores],
    )
    db.commit()


def save_sentiment(feedback_id: int, label: str, score: float, confidence: float,
                    aspects: list[str], is_abusive: bool) -> None:
    db = get_db()
    db.execute(
        """INSERT OR REPLACE INTO sentiment_results
           (feedback_id, label, score, confidence, aspects, is_abusive)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (feedback_id, label, score, confidence, ",".join(aspects), int(is_abusive)),
    )
    new_status = "flagged" if is_abusive else "published"
    db.execute("UPDATE feedback SET status = ? WHERE feedback_id = ?", (new_status, feedback_id))
    db.commit()


def mark_analysis_failed(feedback_id: int) -> None:
    """NFR-06: keep the feedback row even if sentiment analysis fails, so it
    can be retried later; nothing submitted by the student is ever lost."""
    db = get_db()
    db.execute("UPDATE feedback SET status = 'submitted' WHERE feedback_id = ?", (feedback_id,))
    db.commit()


def pending_analysis() -> list[sqlite3.Row]:
    db = get_db()
    return db.execute("SELECT * FROM feedback WHERE status = 'submitted'").fetchall()


# ---- Aggregation for dashboards (no student identity ever selected) ----

def aggregate_ratings_by_aspect(course_id: int, cycle_id: Optional[int] = None) -> list[sqlite3.Row]:
    db = get_db()
    params: list = [course_id]
    cycle_clause = ""
    if cycle_id:
        cycle_clause = "AND f.cycle_id = ?"
        params.append(cycle_id)
    return db.execute(
        f"""SELECT r.aspect, AVG(r.score) AS avg_score, COUNT(*) AS n
            FROM ratings r
            JOIN feedback f ON f.feedback_id = r.feedback_id
            WHERE f.course_id = ? {cycle_clause}
            GROUP BY r.aspect""",
        params,
    ).fetchall()


def sentiment_breakdown(course_id: int, cycle_id: Optional[int] = None) -> list[sqlite3.Row]:
    db = get_db()
    params: list = [course_id]
    cycle_clause = ""
    if cycle_id:
        cycle_clause = "AND f.cycle_id = ?"
        params.append(cycle_id)
    return db.execute(
        f"""SELECT s.label, COUNT(*) AS n
            FROM sentiment_results s
            JOIN feedback f ON f.feedback_id = s.feedback_id
            WHERE f.course_id = ? {cycle_clause} AND f.status = 'published'
            GROUP BY s.label""",
        params,
    ).fetchall()


def overall_average(course_id: int, cycle_id: Optional[int] = None) -> Optional[float]:
    db = get_db()
    params: list = [course_id]
    cycle_clause = ""
    if cycle_id:
        cycle_clause = "AND f.cycle_id = ?"
        params.append(cycle_id)
    row = db.execute(
        f"""SELECT AVG(r.score) AS avg_score
            FROM ratings r JOIN feedback f ON f.feedback_id = r.feedback_id
            WHERE f.course_id = ? {cycle_clause}""",
        params,
    ).fetchone()
    return row["avg_score"] if row and row["avg_score"] is not None else None


def response_count(course_id: int, cycle_id: Optional[int] = None) -> int:
    db = get_db()
    params: list = [course_id]
    cycle_clause = ""
    if cycle_id:
        cycle_clause = "AND cycle_id = ?"
        params.append(cycle_id)
    row = db.execute(
        f"SELECT COUNT(*) AS n FROM feedback WHERE course_id = ? {cycle_clause}", params
    ).fetchone()
    return row["n"]


def recent_comments(course_id: int, cycle_id: Optional[int] = None, label: Optional[str] = None,
                     limit: int = 25) -> list[sqlite3.Row]:
    """Anonymous comments only: feedback_id, comment text, label, confidence, aspects, created_at.
    No user identifier is selected — anonymity is structural, not filtered."""
    db = get_db()
    params: list = [course_id]
    clauses = ["f.course_id = ?", "f.status = 'published'", "f.comment IS NOT NULL", "f.comment != ''"]
    if cycle_id:
        clauses.append("f.cycle_id = ?")
        params.append(cycle_id)
    if label:
        clauses.append("s.label = ?")
        params.append(label)
    where = " AND ".join(clauses)
    params.append(limit)
    return db.execute(
        f"""SELECT f.feedback_id, f.comment, f.created_at, s.label, s.confidence, s.aspects
            FROM feedback f LEFT JOIN sentiment_results s ON s.feedback_id = f.feedback_id
            WHERE {where}
            ORDER BY f.created_at DESC LIMIT ?""",
        params,
    ).fetchall()


def department_summary(semester: Optional[int] = None, course_id: Optional[int] = None,
                        faculty_id: Optional[int] = None) -> list[sqlite3.Row]:
    """One row per course: faculty name (not student identity), avg rating,
    negative %, response count. Used by the HOD dashboard."""
    db = get_db()
    clauses = ["1=1"]
    params: list = []
    if semester:
        clauses.append("c.semester = ?")
        params.append(semester)
    if course_id:
        clauses.append("c.course_id = ?")
        params.append(course_id)
    if faculty_id:
        clauses.append("c.faculty_id = ?")
        params.append(faculty_id)
    where = " AND ".join(clauses)
    return db.execute(
        f"""SELECT c.course_id, c.code, c.name, c.semester, u.name AS faculty_name,
                   (SELECT AVG(score) FROM ratings r JOIN feedback f ON f.feedback_id = r.feedback_id
                    WHERE f.course_id = c.course_id) AS avg_rating,
                   (SELECT COUNT(*) FROM feedback f WHERE f.course_id = c.course_id) AS responses,
                   (SELECT COUNT(*) FROM feedback f JOIN sentiment_results s ON s.feedback_id = f.feedback_id
                    WHERE f.course_id = c.course_id AND s.label = 'negative') AS negative_count
            FROM courses c
            JOIN users u ON u.user_id = c.faculty_id
            WHERE {where}
            ORDER BY c.semester, c.code""",
        params,
    ).fetchall()


def sentiment_trend_by_semester(aspect: Optional[str] = None) -> list[sqlite3.Row]:
    db = get_db()
    aspect_join = ""
    params: list = []
    if aspect:
        aspect_join = """JOIN ratings r2 ON r2.feedback_id = f.feedback_id AND r2.aspect = ?"""
        params.append(aspect)
    return db.execute(
        f"""SELECT c.semester,
                   SUM(CASE WHEN s.label = 'positive' THEN 1 ELSE 0 END) AS positive,
                   SUM(CASE WHEN s.label = 'neutral' THEN 1 ELSE 0 END) AS neutral,
                   SUM(CASE WHEN s.label = 'negative' THEN 1 ELSE 0 END) AS negative
            FROM feedback f
            JOIN courses c ON c.course_id = f.course_id
            JOIN sentiment_results s ON s.feedback_id = f.feedback_id
            {aspect_join}
            GROUP BY c.semester
            ORDER BY c.semester""",
        params,
    ).fetchall()


def flagged_comments() -> list[sqlite3.Row]:
    db = get_db()
    return db.execute(
        """SELECT f.feedback_id, f.comment, f.created_at, c.code, c.name AS course_name, s.label, s.confidence
           FROM feedback f
           JOIN sentiment_results s ON s.feedback_id = f.feedback_id
           JOIN courses c ON c.course_id = f.course_id
           WHERE f.status = 'flagged'
           ORDER BY f.created_at DESC"""
    ).fetchall()


def set_feedback_status(feedback_id: int, status: str) -> None:
    db = get_db()
    db.execute("UPDATE feedback SET status = ? WHERE feedback_id = ?", (status, feedback_id))
    db.commit()
