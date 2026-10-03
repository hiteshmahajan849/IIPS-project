-- IIPS AI-Based Student Feedback & Sentiment Analysis System
-- Relational schema (SQLite for demo; portable to PostgreSQL for production)

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS sentiment_results;
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS submission_log;
DROP TABLE IF EXISTS feedback_cycles;
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('student','faculty','hod','admin')),
  roll_no TEXT,
  department TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses (
  course_id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  semester INTEGER NOT NULL,
  faculty_id INTEGER NOT NULL REFERENCES users(user_id)
);

CREATE TABLE enrollments (
  user_id INTEGER NOT NULL REFERENCES users(user_id),
  course_id INTEGER NOT NULL REFERENCES courses(course_id),
  PRIMARY KEY (user_id, course_id)
);

CREATE TABLE feedback_cycles (
  cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
  semester INTEGER NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed'))
);

-- Identity used ONLY to block duplicate submissions (FR-06, FR-07, NFR-04).
-- Shares no key with `feedback`, so a comment can never be traced to a student.
CREATE TABLE submission_log (
  user_id INTEGER NOT NULL REFERENCES users(user_id),
  course_id INTEGER NOT NULL REFERENCES courses(course_id),
  cycle_id INTEGER NOT NULL REFERENCES feedback_cycles(cycle_id),
  submitted_at DATETIME NOT NULL,
  PRIMARY KEY (user_id, course_id, cycle_id)
);

CREATE TABLE feedback (
  feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL REFERENCES courses(course_id),
  cycle_id INTEGER NOT NULL REFERENCES feedback_cycles(cycle_id),
  comment TEXT,
  status TEXT NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted','analyzing','analyzed','flagged','published','rejected')),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ratings (
  rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
  feedback_id INTEGER NOT NULL REFERENCES feedback(feedback_id),
  aspect TEXT NOT NULL CHECK (aspect IN ('teaching','content','labs','infrastructure','assessment')),
  score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5)
);

CREATE TABLE sentiment_results (
  feedback_id INTEGER PRIMARY KEY REFERENCES feedback(feedback_id),
  label TEXT NOT NULL CHECK (label IN ('positive','neutral','negative')),
  score REAL NOT NULL,
  confidence REAL NOT NULL,
  aspects TEXT,
  is_abusive INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE alerts (
  alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL REFERENCES courses(course_id),
  cycle_id INTEGER NOT NULL REFERENCES feedback_cycles(cycle_id),
  reason TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  acknowledged INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_feedback_course_cycle ON feedback(course_id, cycle_id);
CREATE INDEX idx_ratings_feedback ON ratings(feedback_id);
CREATE INDEX idx_courses_faculty ON courses(faculty_id);
CREATE INDEX idx_enrollments_user ON enrollments(user_id);
