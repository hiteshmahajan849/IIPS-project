"""Alert service tests (FR-14). Covers TC-07: negative share crossing the
threshold creates an alert for the HOD."""
from app.repository import alert_repo, feedback_repo
from app.repository.db import get_db
from app.services import alert_service
from app.services import dashboard_service


def _add_feedback(app, course_id, cycle_id, comment, label):
    with app.app_context():
        fid = feedback_repo.create_feedback(course_id, cycle_id, comment)
        feedback_repo.add_ratings(fid, {"teaching": 2, "content": 2, "labs": 2, "infrastructure": 2, "assessment": 2})
        feedback_repo.save_sentiment(fid, label, -0.8 if label == "negative" else 0.0, 0.8, [], False)


def test_tc07_negative_share_crossing_threshold_creates_alert(app):
    ids = app.config["SEED_IDS"]
    course_id, cycle_id = ids["course2"], ids["open_cycle"]

    # 4 negative, 1 positive => 80% negative, well above the default 40% threshold,
    # and above MIN_RESPONSES_FOR_ALERT (3).
    for _ in range(4):
        _add_feedback(app, course_id, cycle_id, "This was a terrible and useless course.", "negative")
    _add_feedback(app, course_id, cycle_id, "It was fine overall.", "positive")

    with app.app_context():
        alert_service.check_threshold(course_id, cycle_id)
        alerts = alert_repo.list_all(acknowledged=False)

    assert any(a["course_id"] == course_id and a["cycle_id"] == cycle_id for a in alerts)


def test_no_alert_below_minimum_responses(app):
    ids = app.config["SEED_IDS"]
    course_id, cycle_id = ids["course1"], ids["open_cycle"]

    _add_feedback(app, course_id, cycle_id, "Terrible course.", "negative")

    with app.app_context():
        alert_service.check_threshold(course_id, cycle_id)
        alerts = alert_repo.list_all(acknowledged=False)

    assert not any(a["course_id"] == course_id and a["cycle_id"] == cycle_id for a in alerts)


def test_alert_acknowledge_removes_from_unacknowledged_list(app):
    ids = app.config["SEED_IDS"]
    course_id, cycle_id = ids["course1"], ids["open_cycle"]
    for _ in range(4):
        _add_feedback(app, course_id, cycle_id, "Absolutely terrible and useless.", "negative")

    with app.app_context():
        alert_service.check_threshold(course_id, cycle_id)
        alerts = alert_repo.list_all(acknowledged=False)
        assert alerts, "expected an alert to have been raised"
        alert_service.acknowledge(alerts[0]["alert_id"])
        remaining = alert_repo.list_all(acknowledged=False)

    assert alerts[0]["alert_id"] not in [a["alert_id"] for a in remaining]


def test_dashboard_aggregates_only_published_feedback(app):
    ids = app.config["SEED_IDS"]
    with app.app_context():
        db = get_db()
        published_id = db.execute(
            "INSERT INTO feedback(course_id, cycle_id, comment, status) VALUES (?, ?, ?, 'published')",
            (ids["course1"], ids["open_cycle"], "published"),
        ).lastrowid
        rejected_id = db.execute(
            "INSERT INTO feedback(course_id, cycle_id, comment, status) VALUES (?, ?, ?, 'rejected')",
            (ids["course1"], ids["open_cycle"], "rejected"),
        ).lastrowid
        for feedback_id, score, label in ((published_id, 5, "positive"), (rejected_id, 1, "negative")):
            db.executemany(
                "INSERT INTO ratings(feedback_id, aspect, score) VALUES (?, ?, ?)",
                [(feedback_id, aspect, score) for aspect in feedback_repo.ASPECT_NAMES],
            )
            db.execute(
                """INSERT INTO sentiment_results
                   (feedback_id, label, score, confidence, aspects, is_abusive)
                   VALUES (?, ?, ?, ?, ?, 0)""",
                (feedback_id, label, 0.8 if label == "positive" else -0.8, 0.8, ""),
            )
        db.commit()

        assert feedback_repo.response_count(ids["course1"], ids["open_cycle"]) == 1
        assert feedback_repo.overall_average(ids["course1"], ids["open_cycle"]) == 5
        assert feedback_repo.aggregate_ratings_by_aspect(ids["course1"], ids["open_cycle"])[0]["avg_score"] == 5
        summary = feedback_repo.department_summary(course_id=ids["course1"])[0]
        assert summary["avg_rating"] == 5
        assert summary["responses"] == 1
        assert summary["negative_count"] == 0
        assert dashboard_service.department_view(course_id=ids["course1"])["trend"] == [
            {"semester": 9, "positive": 1, "neutral": 0, "negative": 0}
        ]
