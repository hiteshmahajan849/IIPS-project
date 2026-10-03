"""AlertService: threshold checks and HOD notifications (FR-14).

Observer pattern: `FeedbackService` calls `check_threshold` after every new
submission is analyzed, without AlertService needing to know anything about
how/when feedback is submitted — it only reacts.
"""
from __future__ import annotations

from flask import current_app

from ..repository import alert_repo, feedback_repo


def check_threshold(course_id: int, cycle_id: int) -> None:
    min_responses = current_app.config["MIN_RESPONSES_FOR_ALERT"]
    neg_threshold = current_app.config["NEGATIVE_PCT_ALERT_THRESHOLD"]
    avg_threshold = current_app.config["AVG_RATING_ALERT_THRESHOLD"]

    total = feedback_repo.response_count(course_id, cycle_id)
    if total < min_responses:
        return

    breakdown = {row["label"]: row["n"] for row in feedback_repo.sentiment_breakdown(course_id, cycle_id)}
    analyzed_total = sum(breakdown.values()) or 1
    negative_pct = 100.0 * breakdown.get("negative", 0) / analyzed_total

    if negative_pct >= neg_threshold:
        reason = f"Negative sentiment at {negative_pct:.0f}% (threshold {neg_threshold:.0f}%)"
        _raise_once(course_id, cycle_id, reason)

    avg_rating = feedback_repo.overall_average(course_id, cycle_id)
    if avg_rating is not None and avg_rating <= avg_threshold:
        reason = f"Average rating {avg_rating:.1f} at or below threshold {avg_threshold:.1f}"
        _raise_once(course_id, cycle_id, reason)


def _raise_once(course_id: int, cycle_id: int, reason: str) -> None:
    if not alert_repo.exists_unacknowledged(course_id, cycle_id, reason):
        alert_repo.create(course_id, cycle_id, reason)


def list_alerts(acknowledged: bool | None = None):
    return alert_repo.list_all(acknowledged)


def acknowledge(alert_id: int) -> None:
    alert_repo.acknowledge(alert_id)
