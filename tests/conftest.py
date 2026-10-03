import os
import tempfile

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.repository import db as db_module


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    TestConfig.DATABASE_PATH = db_path

    flask_app = create_app(TestConfig)
    with flask_app.app_context():
        db_module.init_db()
        _seed_minimal(flask_app)

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


def _seed_minimal(app):
    """A tiny, deterministic dataset for tests: 2 faculty, 1 hod, 1 admin,
    3 students, 2 courses, 1 open cycle, 1 closed cycle."""
    with app.app_context():
        conn = db_module.get_db()

        def user(name, email, password, role, roll_no=None):
            cur = conn.execute(
                "INSERT INTO users(name, email, password_hash, role, roll_no) VALUES (?,?,?,?,?)",
                (name, email, generate_password_hash(password), role, roll_no),
            )
            return cur.lastrowid

        global_ids = {}
        global_ids["admin"] = user("Admin", "admin@test.local", "admin123", "admin")
        global_ids["hod"] = user("HOD", "hod@test.local", "hod123", "hod")
        global_ids["fac1"] = user("Faculty One", "fac1@test.local", "fac123", "faculty")
        global_ids["fac2"] = user("Faculty Two", "fac2@test.local", "fac123", "faculty")
        global_ids["student1"] = user("Student One", "student1@test.local", "stu123", "student", "R1")
        global_ids["student2"] = user("Student Two", "student2@test.local", "stu123", "student", "R2")
        global_ids["student3"] = user("Student Three", "student3@test.local", "stu123", "student", "R3")

        c1 = conn.execute(
            "INSERT INTO courses(code, name, semester, faculty_id) VALUES (?,?,?,?)",
            ("TC-101", "Test Course One", 9, global_ids["fac1"]),
        ).lastrowid
        c2 = conn.execute(
            "INSERT INTO courses(code, name, semester, faculty_id) VALUES (?,?,?,?)",
            ("TC-102", "Test Course Two", 9, global_ids["fac2"]),
        ).lastrowid
        global_ids["course1"] = c1
        global_ids["course2"] = c2

        for sid in (global_ids["student1"], global_ids["student2"], global_ids["student3"]):
            conn.execute("INSERT INTO enrollments(user_id, course_id) VALUES (?,?)", (sid, c1))
            conn.execute("INSERT INTO enrollments(user_id, course_id) VALUES (?,?)", (sid, c2))

        open_cycle = conn.execute(
            "INSERT INTO feedback_cycles(semester, start_date, end_date, status) VALUES (9, '2026-01-01', '2026-12-31', 'open')"
        ).lastrowid
        closed_cycle = conn.execute(
            "INSERT INTO feedback_cycles(semester, start_date, end_date, status) VALUES (9, '2025-01-01', '2025-01-10', 'closed')"
        ).lastrowid
        global_ids["open_cycle"] = open_cycle
        global_ids["closed_cycle"] = closed_cycle

        conn.commit()
        app.config["SEED_IDS"] = global_ids


def login(client, email, password):
    resp = client.get("/login")
    token = _extract_csrf(resp.data)
    return client.post("/login", data={"email": email, "password": password, "csrf_token": token},
                        follow_redirects=True)


def _extract_csrf(html_bytes: bytes) -> str:
    html = html_bytes.decode("utf-8")
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    end = html.index('"', start)
    return html[start:end]
