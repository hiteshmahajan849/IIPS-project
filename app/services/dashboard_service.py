"""DashboardService: aggregation for Faculty and HOD views (FR-12, FR-13).

Every query here goes through feedback_repo's aggregate functions, none of
which ever select a student identifier -- anonymity is enforced structurally
by the schema (feedback has no user_id), not by filtering it out here.
"""
from __future__ import annotations

from ..repository import alert_repo, course_repo, cycle_repo, feedback_repo


def faculty_course_view(course_id: int, cycle_id: int | None = None) -> dict:
    ratings = {row["aspect"]: round(row["avg_score"], 2) for row in
               feedback_repo.aggregate_ratings_by_aspect(course_id, cycle_id)}
    sentiment = {row["label"]: row["n"] for row in feedback_repo.sentiment_breakdown(course_id, cycle_id)}
    total_sentiment = sum(sentiment.values()) or 1
    sentiment_pct = {
        label: round(100.0 * sentiment.get(label, 0) / total_sentiment, 1)
        for label in ("positive", "neutral", "negative")
    }
    avg_overall = feedback_repo.overall_average(course_id, cycle_id)
    return {
        "ratings_by_aspect": ratings,
        "sentiment_counts": sentiment,
        "sentiment_pct": sentiment_pct,
        "avg_overall": round(avg_overall, 2) if avg_overall is not None else None,
        "responses": feedback_repo.response_count(course_id, cycle_id),
    }


def faculty_comments(course_id: int, cycle_id: int | None = None, label: str | None = None):
    return feedback_repo.recent_comments(course_id, cycle_id, label)


def department_view(semester: int | None = None, course_id: int | None = None,
                     faculty_id: int | None = None, aspect: str | None = None) -> dict:
    rows = feedback_repo.department_summary(semester, course_id, faculty_id)
    courses = []
    for row in rows:
        responses = row["responses"] or 0
        negative_pct = round(100.0 * (row["negative_count"] or 0) / responses, 1) if responses else 0.0
        courses.append({
            "course_id": row["course_id"],
            "code": row["code"],
            "name": row["name"],
            "semester": row["semester"],
            "faculty_name": row["faculty_name"],
            "avg_rating": round(row["avg_rating"], 2) if row["avg_rating"] is not None else None,
            "negative_pct": negative_pct,
            "responses": responses,
        })
    trend = [
        {"semester": r["semester"], "positive": r["positive"], "neutral": r["neutral"], "negative": r["negative"]}
        for r in feedback_repo.sentiment_trend_by_semester(aspect)
    ]
    return {
        "courses": courses,
        "trend": trend,
        "semesters": cycle_repo.list_semesters_with_data(),
        "all_courses": course_repo.list_all(),
    }


def alerts_view():
    return alert_repo.list_all(acknowledged=False)
