"""Dashboard controller: Faculty and HOD views, alerts, export
(FR-12 to FR-15)."""
from flask import (Blueprint, abort, flash, redirect, render_template,
                    request, send_file, session, url_for)

from ..repository import course_repo
from ..services import alert_service, dashboard_service, report_service
from ..utils.security import roles_required, validate_csrf

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard/faculty", methods=["GET"])
@roles_required("faculty")
def faculty_home():
    my_courses = course_repo.list_by_faculty(session["user_id"])
    selected_id = request.args.get("course_id", type=int)
    selected = next((c for c in my_courses if c["course_id"] == selected_id), my_courses[0] if my_courses else None)

    view = None
    comments = []
    if selected:
        cycle_id = request.args.get("cycle_id", type=int)
        label_filter = request.args.get("label") or None
        view = dashboard_service.faculty_course_view(selected["course_id"], cycle_id)
        comments = dashboard_service.faculty_comments(selected["course_id"], cycle_id, label_filter)

    return render_template("faculty/dashboard.html", my_courses=my_courses, selected=selected,
                            view=view, comments=comments, label_filter=request.args.get("label"))


@bp.route("/dashboard/department", methods=["GET"])
@roles_required("hod")
def hod_home():
    semester = request.args.get("semester", type=int)
    course_id = request.args.get("course_id", type=int)
    faculty_id = request.args.get("faculty_id", type=int)
    aspect = request.args.get("aspect") or None

    view = dashboard_service.department_view(semester, course_id, faculty_id, aspect)
    alerts = alert_service.list_alerts(acknowledged=False)
    return render_template("hod/dashboard.html", view=view, alerts=alerts,
                            filters={"semester": semester, "course_id": course_id,
                                     "faculty_id": faculty_id, "aspect": aspect})


@bp.route("/alerts/<int:alert_id>/ack", methods=["POST"])
@roles_required("hod")
@validate_csrf
def acknowledge_alert(alert_id):
    alert_service.acknowledge(alert_id)
    flash("Alert acknowledged.", "success")
    return redirect(url_for("dashboard.hod_home"))


@bp.route("/export", methods=["GET"])
@roles_required("faculty", "hod")
def export():
    fmt = request.args.get("format", "csv")
    if fmt not in ("csv", "pdf"):
        abort(400, "format must be 'csv' or 'pdf'")

    if session["role"] == "faculty":
        course_id = request.args.get("course_id", type=int)
        course = course_repo.find_by_id(course_id) if course_id else None
        if not course or not course_repo.is_owned_by_faculty(course["course_id"], session["user_id"]):
            abort(403)
        cycle_id = request.args.get("cycle_id", type=int)
        buf = report_service.faculty_csv(course, cycle_id) if fmt == "csv" else report_service.faculty_pdf(course, cycle_id)
        filename = f"faculty_report_{course['code']}.{fmt}"
    else:
        filters = {
            "semester": request.args.get("semester", type=int),
            "course_id": request.args.get("course_id", type=int),
            "faculty_id": request.args.get("faculty_id", type=int),
            "aspect": request.args.get("aspect") or None,
        }
        buf = report_service.department_csv(filters) if fmt == "csv" else report_service.department_pdf(filters)
        filename = f"department_report.{fmt}"

    mimetype = "text/csv" if fmt == "csv" else "application/pdf"
    return send_file(buf, mimetype=mimetype, as_attachment=True, download_name=filename)
