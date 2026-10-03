"""Data Access Layer: single point of contact with SQLite.

Only this module (and the repository modules that use it) is allowed to run
SQL. Services and controllers must go through repositories, never sqlite3
directly, per the layered architecture rule in Chapter 7 of the SRS.

The connection is request-scoped via flask.g (one physical connection is
opened per request and reused by every repository call within it, closed on
teardown) which gives us the "load once, reuse" Singleton behaviour described
in Chapter 8 without holding one connection across threads.
"""
import sqlite3
from pathlib import Path

import click
from flask import current_app, g


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db_path = Path(current_app.config["DATABASE_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path = Path(current_app.root_path).parent / "schema.sql"
    db = get_db()
    db.executescript(schema_path.read_text(encoding="utf-8"))
    db.commit()


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


@click.command("init-db")
def init_db_command():
    """Flask CLI command: `flask --app run.py init-db`."""
    init_db()
    click.echo("Initialized the database.")
