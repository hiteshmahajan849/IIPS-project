"""Alert service tests (FR-14). Covers TC-07: negative share crossing the
threshold creates an alert for the HOD."""
from app.repository import alert_repo, feedback_repo
from app.services import alert_service


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
