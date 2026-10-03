"""Seeds the database with demo users, courses, enrollments, a feedback
cycle and sample feedback so the prototype can be demoed immediately.

Run with:  python seed.py   (after `flask --app run.py init-db`)
"""
import random
import sqlite3
from datetime import date, timedelta

from app import create_app
from app.nlp.analyzer import get_analyzer
from app.repository import db

SAMPLE_COMMENTS = [
    # (comment, teaching, content, labs, infra, assessment)
    ("Teaching accha tha but projector kaam nahi karta thha.", 5, 4, 4, 2, 4),
    ("Lectures are clear but the lab equipment is often broken.", 5, 4, 2, 2, 4),
    ("Bahut badiya explanation, concepts clear ho gaye.", 5, 5, 4, 4, 4),
    ("Syllabus is too heavy and exams are badly scheduled.", 3, 2, 3, 3, 2),
    ("Lectures are bakwas and boring, nothing is explained properly.", 1, 2, 2, 3, 2),
    ("Average course, kuch khas nahi, thoda boring tha.", 3, 3, 3, 3, 3),
    ("Labs were very helpful, practicals clear karaye gaye achhe se.", 4, 4, 5, 4, 4),
    ("Infrastructure is bad, wifi never works in classroom.", 4, 4, 3, 1, 3),
    ("Zabardast teaching style, examples were very helpful.", 5, 5, 4, 4, 5),
    ("Assignments bohot mushkil hote hai aur marks kam milte hai.", 3, 3, 3, 3, 2),
    ("Ghatiya experience, library mein books nahi milti.", 2, 2, 2, 1, 2),
    ("Faculty explains topics nicely, notes bhi detailed hai.", 5, 5, 3, 3, 4),
    ("", 4, 4, 4, 4, 4),
    ("This teacher is an idiot and wastes our time every lecture.", 1, 1, 2, 2, 1),
    ("Projector issue every lecture, otherwise theek hai.", 4, 4, 4, 2, 4),
]

ASPECT_ORDER = ("teaching", "content", "labs", "infrastructure", "assessment")


def run():
    app = create_app()
    with app.app_context():
        db.init_db()
        conn = db.get_db()
        analyzer = get_analyzer("vader")

        def insert_user(name, email, password, role, roll_no=None, department="IIPS"):
            from werkzeug.security import generate_password_hash
            cur = conn.execute(
                "INSERT INTO users(name, email, password_hash, role, roll_no, department) VALUES (?,?,?,?,?,?)",
                (name, email, generate_password_hash(password), role, roll_no, department),
            )
            return cur.lastrowid

        admin_id = insert_user("System Admin", "admin@iips.edu", "admin123", "admin")
        hod_id = insert_user("Dr. Rajesh Verma", "hod@iips.edu", "hod123", "hod")
        fac1 = insert_user("Dr. A Sharma", "faculty1@iips.edu", "faculty123", "faculty")
        fac2 = insert_user("Dr. B Mehta", "faculty2@iips.edu", "faculty123", "faculty")
        fac3 = insert_user("Dr. C Iyer", "faculty3@iips.edu", "faculty123", "faculty")

        student_ids = []
        for i in range(1, 41):
            sid = insert_user(f"Student {i}", f"student{i}@iips.edu", "student123", "student",
                               roll_no=f"IC2301{i:02d}")
            student_ids.append(sid)

        c1 = conn.execute(
            "INSERT INTO courses(code, name, semester, faculty_id) VALUES (?,?,?,?)",
            ("IC-909A", "IT and Project Management", 9, fac1),
        ).lastrowid
        c2 = conn.execute(
            "INSERT INTO courses(code, name, semester, faculty_id) VALUES (?,?,?,?)",
            ("IC-912B", "Object Oriented Analysis and Design", 9, fac2),
        ).lastrowid
        c3 = conn.execute(
            "INSERT INTO courses(code, name, semester, faculty_id) VALUES (?,?,?,?)",
            ("IC-905A", "Data Mining", 9, fac3),
        ).lastrowid
        conn.commit()
        courses = [c1, c2, c3]

        for sid in student_ids:
            for cid in courses:
                conn.execute("INSERT OR IGNORE INTO enrollments(user_id, course_id) VALUES (?,?)", (sid, cid))
        conn.commit()

        past_cycle = conn.execute(
            "INSERT INTO feedback_cycles(semester, start_date, end_date, status) VALUES (?,?,?,?)",
            (8, (date.today() - timedelta(days=180)).isoformat(),
             (date.today() - timedelta(days=170)).isoformat(), "closed"),
        ).lastrowid
        open_cycle = conn.execute(
            "INSERT INTO feedback_cycles(semester, start_date, end_date, status) VALUES (?,?,?,?)",
            (9, date.today().isoformat(), (date.today() + timedelta(days=10)).isoformat(), "open"),
        ).lastrowid
        conn.commit()

        rng = random.Random(42)

        def submit_sample_feedback(course_id, cycle_id, student_pool, bias=0):
            for i, sid in enumerate(student_pool):
                comment, *scores = rng.choice(SAMPLE_COMMENTS)
                conn.execute(
                    "INSERT INTO submission_log(user_id, course_id, cycle_id, submitted_at) VALUES (?,?,?,datetime('now'))",
                    (sid, course_id, cycle_id),
                )
                fid = conn.execute(
                    "INSERT INTO feedback(course_id, cycle_id, comment, status) VALUES (?,?,?, 'submitted')",
                    (course_id, cycle_id, comment),
                ).lastrowid
                adj_scores = [max(1, min(5, s + bias)) for s in scores]
                conn.executemany(
                    "INSERT INTO ratings(feedback_id, aspect, score) VALUES (?,?,?)",
                    [(fid, aspect, score) for aspect, score in zip(ASPECT_ORDER, adj_scores)],
                )
                result = analyzer.analyze(comment)
                status = "flagged" if result["is_abusive"] else "published"
                conn.execute(
                    """INSERT OR REPLACE INTO sentiment_results
                       (feedback_id, label, score, confidence, aspects, is_abusive)
                       VALUES (?,?,?,?,?,?)""",
                    (fid, result["label"], result["score"], result["confidence"],
                     ",".join(result["aspects"]), int(result["is_abusive"])),
                )
                conn.execute("UPDATE feedback SET status = ? WHERE feedback_id = ?", (status, fid))
            conn.commit()

        # Closed cycle (semester 8): moderate results, for trend history.
        submit_sample_feedback(c1, past_cycle, student_ids[:25], bias=0)
        submit_sample_feedback(c2, past_cycle, student_ids[:20], bias=-1)
        submit_sample_feedback(c3, past_cycle, student_ids[:22], bias=1)

        # Open cycle (semester 9): c2 deliberately skewed negative to trigger an alert.
        submit_sample_feedback(c1, open_cycle, student_ids[:30], bias=0)
        submit_sample_feedback(c2, open_cycle, student_ids[:28], bias=-2)
        submit_sample_feedback(c3, open_cycle, student_ids[:20], bias=1)

        from app.services import alert_service
        alert_service.check_threshold(c2, open_cycle)

        print("Seed complete.")
        print(f"  Admin:   admin@iips.edu / admin123")
        print(f"  HOD:     hod@iips.edu / hod123")
        print(f"  Faculty: faculty1@iips.edu / faculty123  (teaches {c1})")
        print(f"  Faculty: faculty2@iips.edu / faculty123  (teaches {c2}, deliberately low scores for alert demo)")
        print(f"  Student: student1@iips.edu / student123 (and student2..student40)")


if __name__ == "__main__":
    run()
