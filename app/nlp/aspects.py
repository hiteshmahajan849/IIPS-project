"""Keyword-based aspect tagging (FR-10).

Maps free-text comment tokens to one or more of the five feedback aspects
used throughout the system (Chapter 6 wireframes, schema CHECK constraint on
ratings.aspect). Kept as simple keyword sets so it is trivially replaceable
by a smarter classifier later without touching callers.
"""
import re

ASPECT_KEYWORDS: dict[str, set[str]] = {
    "teaching": {
        "teaching", "teacher", "teachers", "lecture", "lectures", "explain",
        "explains", "explained", "explanation", "faculty", "sir", "madam",
        "professor", "pedagogy", "clarity", "concepts",
    },
    "labs": {
        "lab", "labs", "practical", "practicals", "experiment", "experiments",
        "hands-on", "hardware", "software", "coding",
    },
    "infrastructure": {
        "wifi", "wi-fi", "projector", "classroom", "classrooms", "library",
        "infrastructure", "internet", "ac", "furniture", "building", "lights",
        "fan", "fans",
    },
    "content": {
        "syllabus", "content", "curriculum", "topics", "notes", "material",
        "materials", "course", "subject", "books",
    },
    "assessment": {
        "exam", "exams", "assignment", "assignments", "marks", "test", "tests",
        "grading", "evaluation", "quiz", "quizzes", "paper",
    },
}

ASPECT_NAMES = tuple(ASPECT_KEYWORDS.keys())

_TOKEN_RE = re.compile(r"[a-zA-Z]+")


def tag_aspects(text: str) -> list[str]:
    """Returns the list of aspects whose keywords appear in `text`."""
    tokens = set(_TOKEN_RE.findall((text or "").lower()))
    return [aspect for aspect, keywords in ASPECT_KEYWORDS.items() if tokens & keywords]
