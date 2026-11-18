"""Privacy / anonymity tests (FR-07, NFR-04). Covers TC-06: inspect the
dashboard and export output for any trace of student identity."""
import csv
import io
import runpy
from pathlib import Path

from tests.conftest import login

IDENTIFYING_STRINGS = ["Student One", "Student Two", "Student Three", "R1", "R2", "R3",
                        "student1@test.local", "student2@test.local", "student3@test.local"]


def _submit_feedback(client, course_id, csrf_token, comment):
    return client.post(f"/feedback/{course_id}", data={
        "csrf_token": csrf_token,
        "teaching": "2", "content": "2", "labs": "2", "infrastructure": "2", "assessment": "2",
        "comment": comment,
    })


def test_tc06_faculty_dashboard_has_no_student_identity(app, client):
    ids = app.config["SEED_IDS"]
    login(client, "student1@test.local", "stu123")
    resp = client.get(f"/feedback/{ids['course1']}")
    html = resp.data.decode("utf-8")
    token = html.split('name="csrf_token" value="')[1].split('"')[0]
    _submit_feedback(client, ids["course1"], token, "Teaching was accha, projector bekar.")
    client.post("/logout", data={"csrf_token": token})

    login(client, "fac1@test.local", "fac123")
    resp = client.get(f"/dashboard/faculty?course_id={ids['course1']}")
    html = resp.data.decode("utf-8")
    for marker in IDENTIFYING_STRINGS:
        assert marker not in html, f"Student identity leaked in faculty dashboard: {marker}"


def test_tc06_csv_export_has_no_student_identity(app, client):
    ids = app.config["SEED_IDS"]
    login(client, "student2@test.local", "stu123")
    resp = client.get(f"/feedback/{ids['course1']}")
    token = resp.data.decode("utf-8").split('name="csrf_token" value="')[1].split('"')[0]
    _submit_feedback(client, ids["course1"], token, "Labs were helpful but bekar wifi.")
    client.post("/logout", data={"csrf_token": token})

    login(client, "fac1@test.local", "fac123")
    resp = client.get(f"/export?format=csv&course_id={ids['course1']}")
    assert resp.status_code == 200
    text = resp.data.decode("utf-8")
    for marker in IDENTIFYING_STRINGS:
        assert marker not in text

    rows = list(csv.reader(io.StringIO(text)))
    assert len(rows) > 0


def test_feedback_table_has_no_user_id_column(app):
    """Schema-level guarantee backing the privacy design: `feedback` has no
    user_id / student reference column at all."""
    from app.repository.db import get_db
    with app.app_context():
        cols = {row[1] for row in get_db().execute("PRAGMA table_info(feedback)").fetchall()}
    assert "user_id" not in cols
    assert "student_id" not in cols


def test_submission_log_has_no_timestamp_column(app):
    from app.repository.db import get_db
    with app.app_context():
        cols = {row[1] for row in get_db().execute("PRAGMA table_info(submission_log)").fetchall()}
    assert "submitted_at" not in cols


def test_run_py_only_enables_debug_for_explicit_one(monkeypatch):
    observed = {}

    def fake_run(self, **kwargs):
        observed.update(kwargs)

    from flask import Flask
    monkeypatch.setattr(Flask, "run", fake_run)
    monkeypatch.setenv("FLASK_DEBUG", "0")
    runpy.run_path(str(Path(__file__).parents[1] / "run.py"), run_name="__main__")
    assert observed["debug"] is False


def test_faculty_pdf_escapes_comment_markup(app, client):
    ids = app.config["SEED_IDS"]
    login(client, "student3@test.local", "stu123")
    resp = client.get(f"/feedback/{ids['course1']}")
    token = resp.data.decode("utf-8").split('name="csrf_token" value="')[1].split('"')[0]
    comment = "<b>good but a < b & c"
    response = _submit_feedback(client, ids["course1"], token, comment)
    assert response.status_code == 302
    client.post("/logout", data={"csrf_token": token})

    login(client, "fac1@test.local", "fac123")
    response = client.get(f"/export?format=pdf&course_id={ids['course1']}")
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_faculty_csv_escapes_formula_comments(app, client):
    ids = app.config["SEED_IDS"]
    login(client, "student1@test.local", "stu123")
    resp = client.get(f"/feedback/{ids['course1']}")
    token = resp.data.decode("utf-8").split('name="csrf_token" value="')[1].split('"')[0]
    comment = '=HYPERLINK("http://evil","x")'
    response = _submit_feedback(client, ids["course1"], token, comment)
    assert response.status_code == 302
    client.post("/logout", data={"csrf_token": token})

    login(client, "fac1@test.local", "fac123")
    response = client.get(f"/export?format=csv&course_id={ids['course1']}")
    assert response.status_code == 200
    rows = list(csv.reader(io.StringIO(response.data.decode("utf-8"))))
    assert ["'" + comment, "neutral", "0.0"] in rows
