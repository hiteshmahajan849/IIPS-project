"""FeedbackService: the core business rules behind Submit Feedback
(FR-04 to FR-11, sequence diagram in Chapter 4.5).
"""
from __future__ import annotations

from flask import current_app

from ..nlp.analyzer import get_analyzer
from ..repository import course_repo, cycle_repo, feedback_repo, user_repo
from ..utils.validators import clean_comment, parse_ratings
from . import alert_service


class CycleClosedError(Exception):
    pass


class NotEnrolledError(Exception):
    pass


DuplicateSubmissionError = feedback_repo.DuplicateSubmissionError


def open_cycle_courses(student_id: int):
    """FR-04: courses the student is enrolled in that belong to the
    currently open feedback cycle's semester, excluding ones already
    submitted."""
    cycle = cycle_repo.current_open_cycle()
    if not cycle:
        return None, []
    courses = [
        c for c in user_repo.enrolled_courses(student_id) if c["semester"] == cycle["semester"]
    ]
    pending = [c for c in courses if not feedback_repo.has_submitted(student_id, c["course_id"], cycle["cycle_id"])]
    return cycle, pending


def submit(student_id: int, course_id: int, form) -> dict:
    """Validates, stores anonymously, analyzes sentiment, and triggers the
    alert check. Returns the sentiment result for the thank-you page."""
    cycle = cycle_repo.current_open_cycle()
    if not cycle:
        raise CycleClosedError("There is no open feedback cycle right now.")

    course = course_repo.find_by_id(course_id)
    enrolled_ids = {c["course_id"] for c in user_repo.enrolled_courses(student_id)}
    if not course or course_id not in enrolled_ids or course["semester"] != cycle["semester"]:
        raise NotEnrolledError("You are not enrolled in this course for the open cycle.")

    if feedback_repo.has_submitted(student_id, course_id, cycle["cycle_id"]):
        raise DuplicateSubmissionError()

    scores = parse_ratings(form)  # raises ValidationError on bad input
    comment = clean_comment(form.get("comment"))

    # Identity is written ONLY to submission_log, never to `feedback` (FR-07).
    feedback_repo.record_submission(student_id, course_id, cycle["cycle_id"])

    feedback_id = feedback_repo.create_feedback(course_id, cycle["cycle_id"], comment)
    feedback_repo.add_ratings(feedback_id, scores)

    analyzer = get_analyzer(current_app.config["SENTIMENT_ANALYZER"])
    try:
        result = analyzer.analyze(comment) if comment else {
            "label": "neutral", "score": 0.0, "confidence": 0.0, "aspects": [], "is_abusive": False,
        }
        feedback_repo.save_sentiment(
            feedback_id, result["label"], result["score"], result["confidence"],
            result["aspects"], result["is_abusive"],
        )
    except Exception:
        # NFR-06: never lose submitted feedback if analysis fails; it stays
        # at status 'submitted' for a later retry pass.
        feedback_repo.mark_analysis_failed(feedback_id)
        current_app.logger.exception("Sentiment analysis failed for feedback_id=%s", feedback_id)
        result = {"label": "pending", "score": 0.0, "confidence": 0.0, "aspects": [], "is_abusive": False}

    alert_service.check_threshold(course_id, cycle["cycle_id"])
    return result


def retry_pending_analysis() -> int:
    """NFR-06 retry path: re-analyzes any feedback left at status
    'submitted' (e.g. after a transient NLP failure). Returns count retried."""
    analyzer = get_analyzer(current_app.config["SENTIMENT_ANALYZER"])
    rows = feedback_repo.pending_analysis()
    for row in rows:
        result = analyzer.analyze(row["comment"] or "")
        feedback_repo.save_sentiment(
            row["feedback_id"], result["label"], result["score"], result["confidence"],
            result["aspects"], result["is_abusive"],
        )
    return len(rows)
