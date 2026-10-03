"""Admin controller: users, courses, cycles, moderation (FR-02, FR-03, FR-11)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..services import admin_service
from ..utils.security import get_csrf_token, roles_required, validate_csrf
from ..utils.validators import ValidationError

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/", methods=["GET"])
@roles_required("admin")
def panel():
    return render_template("admin/panel.html",
                            users=admin_service.list_users(),
                            courses=admin_service.list_courses(),
                            cycles=admin_service.list_cycles(),
                            flagged=admin_service.flagged_comments(),
                            csrf_token=get_csrf_token())


@bp.route("/users", methods=["POST"])
@roles_required("admin")
@validate_csrf
def create_user():
    f = request.form
    try:
        admin_service.create_user(f.get("name"), f.get("email"), f.get("password"),
                                   f.get("role"), f.get("roll_no") or None, f.get("department") or None)
        flash("User created.", "success")
    except ValidationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.panel"))


@bp.route("/courses", methods=["POST"])
@roles_required("admin")
@validate_csrf
def create_course():
    f = request.form
    try:
        admin_service.create_course(f.get("code"), f.get("name"), f.get("semester"), f.get("faculty_id", type=int))
        flash("Course created.", "success")
    except ValidationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.panel"))


@bp.route("/enrollments", methods=["POST"])
@roles_required("admin")
@validate_csrf
def enroll():
    f = request.form
    try:
        admin_service.enroll_student(f.get("user_id", type=int), f.get("course_id", type=int))
        flash("Student enrolled.", "success")
    except ValidationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.panel"))


@bp.route("/cycles", methods=["POST"])
@roles_required("admin")
@validate_csrf
def create_cycle():
    f = request.form
    try:
        admin_service.create_cycle(f.get("semester"), f.get("start_date"), f.get("end_date"))
        flash("Feedback cycle opened.", "success")
    except ValidationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.panel"))


@bp.route("/cycles/<int:cycle_id>/close", methods=["POST"])
@roles_required("admin")
@validate_csrf
def close_cycle(cycle_id):
    admin_service.close_cycle(cycle_id)
    flash("Feedback cycle closed.", "success")
    return redirect(url_for("admin.panel"))


@bp.route("/flagged/<int:feedback_id>", methods=["POST"])
@roles_required("admin")
@validate_csrf
def moderate_flagged(feedback_id):
    decision = request.form.get("decision")
    try:
        admin_service.moderate(feedback_id, decision)
        flash("Moderation decision recorded.", "success")
    except ValidationError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.panel"))
