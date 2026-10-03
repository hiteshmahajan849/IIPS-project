"""Feedback controller: Student course list and Submit Feedback
(FR-04 to FR-07, sequence diagram Chapter 4.5)."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..services import feedback_service
from ..utils.security import get_csrf_token, roles_required, validate_csrf
from ..utils.validators import ValidationError

bp = Blueprint("feedback", __name__)


@bp.route("/courses", methods=["GET"])
@roles_required("student")
def courses():
    cycle, pending = feedback_service.open_cycle_courses(session["user_id"])
    return render_template("student/courses.html", cycle=cycle, courses=pending)


@bp.route("/feedback/<int:course_id>", methods=["GET"])
@roles_required("student")
def feedback_form(course_id):
    cycle, pending = feedback_service.open_cycle_courses(session["user_id"])
    course = next((c for c in pending if c["course_id"] == course_id), None)
    if not course:
        flash("That course is not available for feedback right now.", "error")
        return redirect(url_for("feedback.courses"))
    return render_template("student/feedback_form.html", course=course, cycle=cycle,
                            csrf_token=get_csrf_token())


@bp.route("/feedback/<int:course_id>", methods=["POST"])
@roles_required("student")
@validate_csrf
def submit_feedback(course_id):
    try:
        feedback_service.submit(session["user_id"], course_id, request.form)
    except feedback_service.DuplicateSubmissionError:
        flash("You have already submitted feedback for this course this cycle.", "error")
        return redirect(url_for("feedback.courses")), 409
    except feedback_service.CycleClosedError as exc:
        flash(str(exc), "error")
        return redirect(url_for("feedback.courses")), 403
    except feedback_service.NotEnrolledError as exc:
        flash(str(exc), "error")
        return redirect(url_for("feedback.courses")), 403
    except ValidationError as exc:
        flash(str(exc), "error")
        return redirect(url_for("feedback.feedback_form", course_id=course_id))

    return redirect(url_for("feedback.thanks"))


@bp.route("/thanks", methods=["GET"])
@roles_required("student")
def thanks():
    return render_template("student/thanks.html")
