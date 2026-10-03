# IIPS AI-Based Student Feedback & Sentiment Analysis System

A web-based system for collecting anonymous student feedback on courses and
faculty, automatically classifying free-text comments (English and Hinglish)
by sentiment and aspect, and surfacing the results to Faculty, HOD and Admin
through role-specific dashboards, alerts and exportable reports.

Built as the running prototype for the IC 912 B (OOAD Lab) project
*"IIPS AI-Based Student Feedback & Sentiment Analysis System"*.

## Features

- **Role-based access**: Student, Faculty, HOD, Admin — enforced on every route.
- **Anonymous feedback**: ratings + comments for 5 aspects (Teaching, Course
  Content, Labs, Infrastructure, Assessment) on a 1–5 scale; student identity
  is recorded only to block duplicate submissions and is never joined against
  feedback, dashboards, analytics or exports (structural anonymity — the
  `feedback` table has no student/user column at all).
- **Feedback cycles**: Admin opens/closes a cycle per semester; students only
  see courses enrolled in the open cycle's semester, and only once.
- **Duplicate-submission prevention**: enforced by a composite primary key
  `(user_id, course_id, cycle_id)` on `submission_log`.
- **English + Hinglish sentiment analysis**: VADER extended with a Hinglish
  lexicon (accha, badiya, mast, bakwas, ghatiya, …), label + confidence score.
- **Aspect detection**: keyword-based tagging of which aspect(s) a comment is about.
- **Abusive-comment moderation**: profanity/personal-insult detector routes
  flagged comments to an Admin approve/reject queue, kept separate from
  ordinary negative sentiment.
- **Faculty dashboard**: avg rating, sentiment split, per-aspect ratings,
  filterable anonymous comment feed.
- **HOD department dashboard**: filter by semester/course/faculty/aspect,
  course comparison, sentiment trend over semesters, active alerts.
- **Alerts**: auto-raised when a course's negative-sentiment share or average
  rating crosses a configurable threshold.
- **PDF and CSV report export** for Faculty and HOD (reportlab + stdlib csv).
- **Responsive UI** (works down to phone width), Chart.js visualizations.
- **25 automated tests** covering the SDD test plan (duplicate submission,
  sentiment labels, access control, cycle-closed, privacy, alert threshold).

## Architecture

Strict layered architecture — each layer depends only on the one below it:

```
Presentation (Jinja templates, static CSS/JS, Chart.js)
      ↓
Controllers (Flask blueprints: auth, feedback, dashboard, admin — routing,
             role checks, CSRF, input validation)
      ↓
Services (FeedbackService, DashboardService, AlertService, ReportService,
          AdminService, AuthService — business rules)
      ↓
NLP (SentimentAnalyzer interface, VaderAnalyzer, aspect tagger, moderation)
      ↓
Repository / Data Access (user_repo, course_repo, cycle_repo, feedback_repo,
                           alert_repo — the only layer that touches SQL)
      ↓
Database (SQLite for the prototype; schema is portable to PostgreSQL)
```

**Design patterns used**: Strategy (`SentimentAnalyzer` interface),
Factory + Singleton (`get_analyzer()` caches the loaded VADER+Hinglish
lexicon), Observer (`FeedbackService` triggers `AlertService` after each
submission), Repository (SQL isolated per entity), MVC (Flask routes /
Jinja templates / dataclass entities).

## Tech stack

Python 3.12, Flask 3, SQLite, vaderSentiment (open-source, no paid APIs),
reportlab (PDF), Chart.js (CDN), plain HTML/CSS/JS with Jinja templates.

## Project structure

```
IIPS_project/
├── app/
│   ├── __init__.py            # Flask app factory, blueprint registration
│   ├── config.py               # env-driven configuration
│   ├── controllers/            # auth_routes, feedback_routes, dashboard_routes, admin_routes
│   ├── services/                # feedback_service, dashboard_service, alert_service,
│   │                             report_service, admin_service, auth_service
│   ├── nlp/                      # analyzer.py (Strategy/Factory/Singleton), aspects.py,
│   │                              hinglish_lexicon.py, moderation.py
│   ├── repository/                # db.py + user_repo, course_repo, cycle_repo,
│   │                               feedback_repo, alert_repo
│   ├── models/                    # entities.py (typed dataclasses)
│   ├── utils/                     # security.py (auth/CSRF decorators), validators.py
│   ├── templates/                 # base.html + student/, faculty/, hod/, admin/
│   └── static/                    # css/style.css, js/*.js
├── schema.sql                     # relational schema (SQLite)
├── seed.py                        # demo users, courses, cycles, sample feedback
├── run.py                         # entrypoint
├── requirements.txt
├── .env.example
├── .gitignore
├── pytest.ini
├── tests/                         # 25 tests across 4 files
└── README.md
```

## Installation and setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux
# edit .env and set a real SECRET_KEY

# 4. Initialize the database (runs schema.sql against instance/app.db)
set FLASK_APP=run.py           # Windows (cmd)
$env:FLASK_APP="run.py"        # Windows (PowerShell)
# export FLASK_APP=run.py      # macOS/Linux
flask init-db

# 5. Load demo/seed data
python seed.py

# 6. Run the app
python run.py
# or: flask run
```

Visit **http://127.0.0.1:5000**.

### Running tests

```bash
pytest -v
```

25 tests, covering: duplicate-submission blocking (TC-01), Hinglish sentiment
labels (TC-02/TC-03), cross-faculty access denial (TC-04), cycle-closed
rejection (TC-05), absence of student identity in dashboards/exports (TC-06),
and alert creation on threshold breach (TC-07), plus NLP unit tests and an
accuracy sample check.

## Demo credentials

| Role    | Email                  | Password    |
|---------|------------------------|-------------|
| Admin   | admin@iips.edu         | admin123    |
| HOD     | hod@iips.edu            | hod123      |
| Faculty | faculty1@iips.edu       | faculty123  |
| Faculty | faculty2@iips.edu       | faculty123  |
| Student | student1@iips.edu ... student40@iips.edu | student123 |

`student40@iips.edu` is left with no prior submissions in the seed data so
you can demo a live feedback submission end-to-end.

## Privacy / anonymity design

Per the requirements document's strict anonymity rule:

- The `feedback` table has **no student/user identifier column**. It is
  physically impossible to join a comment back to a student from this table.
- `submission_log` records `(user_id, course_id, cycle_id)` **only** to
  enforce "one submission per student per course per cycle." It is never
  joined against `feedback`, `ratings`, or `sentiment_results` by any query
  in the codebase (see `app/repository/feedback_repo.py`).
- Dashboards, analytics, CSV/PDF exports select only aggregated numbers and
  anonymous comment text — verified by automated tests
  (`tests/test_privacy.py`).

## Accuracy note

Per NFR-08, the sentiment analyzer targets **at least 80% agreement with
manual labels on a sample set** — it is not claimed to be 100% accurate.
`tests/test_sentiment.py::test_accuracy_meets_nfr08_target` checks this
against a small hand-labelled sample. VADER + a Hinglish lexicon is a
lexicon/rule-based approach; it will misclassify sarcasm, heavy code-mixing,
or comments outside its lexicon. The `SentimentAnalyzer` interface in
`app/nlp/analyzer.py` is designed to be swapped for a more sophisticated
(e.g. transformer-based) analyzer later without changing any other layer
(NFR-07).

## Known limitations / future work

- Sentiment and abuse detection are lexicon/keyword-based, not transformer
  models — see "Accuracy note" above.
- Single-department scope: HOD dashboard shows all courses (IIPS is treated
  as one department), matching the wireframes in the requirements document.
- No email/SMS delivery for alerts — alerts surface only in the HOD dashboard.
- SQLite is used for the prototype; `app/repository/db.py` is the only module
  that would need to change to target PostgreSQL in production.
- Retry of failed sentiment analysis (NFR-06) is implemented as
  `feedback_service.retry_pending_analysis()` but is not wired to a scheduler;
  it would be invoked by a periodic job or admin action in production.
