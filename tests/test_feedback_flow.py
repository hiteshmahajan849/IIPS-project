"""Integration tests for feedback submission (TC-01, TC-05) via the real
Flask routes, using the service layer underneath."""
from app.repository import cycle_repo, feedback_repo
from tests.conftest import login


def _submit(client, course_id, csrf_token, comment="Teaching was accha and clear", **overrides):
    data = {
        "csrf_token": csrf_token,
        "teaching": "4", "content": "4", "labs": "4", "infrastructure": "4", "assessment": "4",
        "comment": comment,
    }
    data.update(overrides)
    return client.post(f"/feedback/{course_id}", data=data, follow_redirects=False)


def _csrf_from(client, url):
    resp = client.get(url)
    html = resp.data.decode("utf-8")
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    end = html.index('"', start)
    return html[start:end]


def test_tc01_duplicate_submission_rejected(app, client):
    ids = app.config["SEED_IDS"]
    login(client, "student1@test.local", "stu123")
    token = _csrf_from(client, f"/feedback/{ids['course1']}")

    first = _submit(client, ids["course1"], token)
    assert first.status_code in (302,)

    # CSRF token is session-scoped, so the same token is still valid; resubmitting
    # must be blocked either by the pending-courses check (403) or the
    # duplicate-submission check itself (409).
    second = _submit(client, ids["course1"], token, comment="trying again")
    assert second.status_code in (403, 409)

    with app.app_context():
        assert feedback_repo.has_submitted(ids["student1"], ids["course1"], ids["open_cycle"])


def test_tc05_submit_after_cycle_closed_rejected(app, client):
    ids = app.config["SEED_IDS"]
    with app.app_context():
        cycle_repo.close(ids["open_cycle"])

    login(client, "student2@test.local", "stu123")
    token = _csrf_from(client, "/courses")
    resp = _submit(client, ids["course1"], token)
    assert resp.status_code == 403


def test_pending_courses_excludes_already_submitted(app, client):
    ids = app.config["SEED_IDS"]
    login(client, "student3@test.local", "stu123")
    token = _csrf_from(client, f"/feedback/{ids['course1']}")
    _submit(client, ids["course1"], token)

    resp = client.get("/courses")
    assert resp.status_code == 200
    with app.app_context():
        from app.services.feedback_service import open_cycle_courses
        _, pending = open_cycle_courses(ids["student3"])
        pending_ids = {c["course_id"] for c in pending}
        assert ids["course1"] not in pending_ids
        assert ids["course2"] in pending_ids
