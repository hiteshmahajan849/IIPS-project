"""Role-based access control tests (FR-01, NFR-03). Covers TC-04: a faculty
member must not be able to view or export another faculty member's course."""
from tests.conftest import login


def test_tc04_faculty_cannot_export_another_facultys_course(app, client):
    ids = app.config["SEED_IDS"]
    login(client, "fac1@test.local", "fac123")  # fac1 teaches course1, not course2
    resp = client.get(f"/export?format=csv&course_id={ids['course2']}")
    assert resp.status_code == 403


def test_faculty_dashboard_only_shows_own_courses(app, client):
    ids = app.config["SEED_IDS"]
    login(client, "fac1@test.local", "fac123")
    resp = client.get("/dashboard/faculty")
    html = resp.data.decode("utf-8")
    assert "TC-101" in html
    assert "TC-102" not in html


def test_student_cannot_access_admin_panel(client):
    login(client, "student1@test.local", "stu123")
    resp = client.get("/admin/")
    assert resp.status_code == 403


def test_student_cannot_access_hod_dashboard(client):
    login(client, "student1@test.local", "stu123")
    resp = client.get("/dashboard/department")
    assert resp.status_code == 403


def test_unauthenticated_redirected_to_login(client):
    resp = client.get("/courses", follow_redirects=True)
    assert resp.status_code == 200
    assert b"IIPS Feedback System" in resp.data
    assert b"Login" in resp.data or b"login" in resp.data


def test_hod_can_access_department_dashboard(client):
    login(client, "hod@test.local", "hod123")
    resp = client.get("/dashboard/department")
    assert resp.status_code == 200


def test_admin_can_access_admin_panel(client):
    login(client, "admin@test.local", "admin123")
    resp = client.get("/admin/")
    assert resp.status_code == 200


def test_invalid_login_rejected(client):
    resp = client.get("/login")
    from tests.conftest import _extract_csrf
    token = _extract_csrf(resp.data)
    resp = client.post("/login", data={"email": "nobody@test.local", "password": "wrong", "csrf_token": token},
                        follow_redirects=True)
    assert b"Invalid email or password" in resp.data
