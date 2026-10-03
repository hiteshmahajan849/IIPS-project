"""Lightweight entity classes (Chapter 4.3 class diagram).

These are plain dataclasses used to give typed shape to rows coming back from
the repository layer in services/templates; they are not an ORM and do not
touch the database themselves (that rule belongs to the Data Access Layer).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    user_id: int
    name: str
    email: str
    role: str
    roll_no: Optional[str] = None
    department: Optional[str] = None

    @property
    def is_student(self) -> bool:
        return self.role == "student"

    @property
    def is_faculty(self) -> bool:
        return self.role == "faculty"

    @property
    def is_hod(self) -> bool:
        return self.role == "hod"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @classmethod
    def from_row(cls, row) -> "User":
        return cls(
            user_id=row["user_id"], name=row["name"], email=row["email"],
            role=row["role"], roll_no=row["roll_no"], department=row["department"],
        )


@dataclass
class Course:
    course_id: int
    code: str
    name: str
    semester: int
    faculty_id: int


@dataclass
class FeedbackCycle:
    cycle_id: int
    semester: int
    start_date: str
    end_date: str
    status: str

    def is_open(self) -> bool:
        return self.status == "open"


@dataclass
class Rating:
    aspect: str
    score: int


@dataclass
class SentimentResult:
    label: str
    score: float
    confidence: float
    aspects: list[str] = field(default_factory=list)
    is_abusive: bool = False


@dataclass
class Feedback:
    feedback_id: int
    course_id: int
    cycle_id: int
    comment: str
    status: str
    created_at: datetime
    ratings: list[Rating] = field(default_factory=list)
    sentiment: Optional[SentimentResult] = None


@dataclass
class Alert:
    alert_id: int
    course_id: int
    cycle_id: int
    reason: str
    acknowledged: bool
