"""Auth helpers shared by controllers: login/role enforcement and CSRF.

NFR-03: role-based authorization on every endpoint, server-side session,
parameterized SQL (handled in the repository layer), CSRF protection.
"""
from __future__ import annotations

import secrets
from functools import wraps

from flask import abort, flash, redirect, request, session, url_for


def current_user_id() -> int | None:
    return session.get("user_id")


def current_role() -> str | None:
    return session.get("role")


def login_required(role: str | None = None):
    """Decorator: requires an authenticated session, optionally restricted
    to a single role. Use `roles_required` for more than one allowed role."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "error")
                return redirect(url_for("auth.login", next=request.path))
            if role and session.get("role") != role:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


def roles_required(*roles: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "error")
                return redirect(url_for("auth.login", next=request.path))
            if session.get("role") not in roles:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


def get_csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_hex(16)
        session["csrf_token"] = token
    return token


def validate_csrf(view_func):
    """Decorator for state-changing (POST) routes: compares the hidden
    `csrf_token` form field against the one stored server-side in session."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        if not expected or not secrets.compare_digest(sent, expected):
            abort(400, "Invalid or missing CSRF token.")
        return view_func(*args, **kwargs)
    return wrapped
