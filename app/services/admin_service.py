"""AdminService: user/course/cycle management and comment moderation
(FR-02, FR-03, FR-11). Thin wrapper over repositories so controllers never
call the Data Access Layer directly (Chapter 7 layering rule).
"""
from __future__ import annotations

from ..repository import course_repo, cycle_repo, feedback_repo, user_repo
from ..utils.validators import ValidationError, is_valid_email


def create_user(name: str, email: str, password: str, role: str,
                 roll_no: str | None = None, department: str | None = None) -> int:
    if not name or not name.strip():
        raise ValidationError("Name is required.")
    if not is_valid_email(email):
        raise ValidationError("A valid email is required.")
    if not password or len(password) < 6:
        raise ValidationError("Password must be at least 6 characters.")
    if role not in ("student", "faculty", "hod", "admin"):
        raise ValidationError("Invalid role.")
    if user_repo.find_by_email(email):
        raise ValidationError("A user with this email already exists.")
    return user_repo.create(name.strip(), email.strip().lower(), password, role, roll_no, department)


def list_users(role: str | None = None):
    return user_repo.list_all(role)


def create_course(code: str, name: str, semester: int, faculty_id: int) -> int:
    if not code or not name:
        raise ValidationError("Course code and name are required.")
    faculty = user_repo.find_by_id(faculty_id)
    if not faculty or faculty["role"] != "faculty":
        raise ValidationError("Selected user is not a faculty member.")
    return course_repo.create(code.strip(), name.strip(), int(semester), faculty_id)


def list_courses():
    return course_repo.list_all()


def enroll_student(user_id: int, course_id: int) -> None:
    user = user_repo.find_by_id(user_id)
    if not user or user["role"] != "student":
        raise ValidationError("Selected user is not a student.")
    if not course_repo.find_by_id(course_id):
        raise ValidationError("Course not found.")
    user_repo.enroll(user_id, course_id)


def create_cycle(semester: int, start_date: str, end_date: str) -> int:
    if not start_date or not end_date:
        raise ValidationError("Start and end dates are required.")
    if start_date > end_date:
        raise ValidationError("Start date must be before end date.")
    return cycle_repo.create(int(semester), start_date, end_date)


def close_cycle(cycle_id: int) -> None:
    cycle_repo.close(cycle_id)


def list_cycles():
    return cycle_repo.list_all()


def flagged_comments():
    return feedback_repo.flagged_comments()


def moderate(feedback_id: int, decision: str) -> None:
    if decision not in ("approve", "remove"):
        raise ValidationError("Decision must be 'approve' or 'remove'.")
    new_status = "published" if decision == "approve" else "rejected"
    feedback_repo.set_feedback_status(feedback_id, new_status)
