"""Auth controller: /login, /logout (FR-01)."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..services import auth_service
from ..utils.security import get_csrf_token, validate_csrf

bp = Blueprint("auth", __name__)

ROLE_HOME = {
    "student": "feedback.courses",
    "faculty": "dashboard.faculty_home",
    "hod": "dashboard.hod_home",
    "admin": "admin.panel",
}


@bp.route("/", methods=["GET"])
def index():
    if "user_id" in session:
        return redirect(url_for(ROLE_HOME[session["role"]]))
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET"])
def login():
    if "user_id" in session:
        return redirect(url_for(ROLE_HOME[session["role"]]))
    return render_template("login.html", csrf_token=get_csrf_token())


@bp.route("/login", methods=["POST"])
@validate_csrf
def login_submit():
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    user = auth_service.authenticate(email, password)
    if not user:
        flash("Invalid email or password.", "error")
        return redirect(url_for("auth.login"))

    session.clear()
    session["user_id"] = user["user_id"]
    session["name"] = user["name"]
    session["role"] = user["role"]
    flash(f"Welcome, {user['name']}.", "success")
    return redirect(url_for(ROLE_HOME[user["role"]]))


@bp.route("/logout", methods=["POST"])
@validate_csrf
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
