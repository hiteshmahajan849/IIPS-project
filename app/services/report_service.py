"""ReportService: PDF/CSV export for Faculty and HOD (FR-15).

Only ever exports aggregated numbers and anonymous comment text -- never a
student identifier (NFR-04). Uses the open-source `reportlab` library for
PDF; CSV uses only the Python standard library.
"""
from __future__ import annotations

import csv
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from . import dashboard_service


def faculty_csv(course, cycle_id: int | None) -> io.BytesIO:
    view = dashboard_service.faculty_course_view(course["course_id"], cycle_id)
    comments = dashboard_service.faculty_comments(course["course_id"], cycle_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["IIPS Feedback Report - Faculty"])
    writer.writerow(["Course", f"{course['code']} - {course['name']}"])
    writer.writerow(["Average Rating", view["avg_overall"]])
    writer.writerow(["Responses", view["responses"]])
    writer.writerow([])
    writer.writerow(["Aspect", "Average Score"])
    for aspect, score in view["ratings_by_aspect"].items():
        writer.writerow([aspect, score])
    writer.writerow([])
    writer.writerow(["Sentiment", "Percent"])
    for label, pct in view["sentiment_pct"].items():
        writer.writerow([label, pct])
    writer.writerow([])
    writer.writerow(["Anonymous Comment", "Sentiment", "Confidence"])
    for c in comments:
        writer.writerow([c["comment"], c["label"], c["confidence"]])

    return io.BytesIO(buf.getvalue().encode("utf-8"))


def faculty_pdf(course, cycle_id: int | None) -> io.BytesIO:
    view = dashboard_service.faculty_course_view(course["course_id"], cycle_id)
    comments = dashboard_service.faculty_comments(course["course_id"], cycle_id)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"IIPS Feedback Report &mdash; {course['code']} {course['name']}", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Average Rating: {view['avg_overall']} / 5 &nbsp;&nbsp; Responses: {view['responses']}",
                   styles["Normal"]),
        Spacer(1, 12),
    ]

    aspect_data = [["Aspect", "Average Score"]] + [[a, s] for a, s in view["ratings_by_aspect"].items()]
    elements.append(_styled_table(aspect_data))
    elements.append(Spacer(1, 12))

    sentiment_data = [["Sentiment", "Percent"]] + [[k, f"{v}%"] for k, v in view["sentiment_pct"].items()]
    elements.append(_styled_table(sentiment_data))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Anonymous Comments", styles["Heading2"]))
    for c in comments[:50]:
        elements.append(Paragraph(f"[{c['label']}] {c['comment']}", styles["Normal"]))
        elements.append(Spacer(1, 4))

    doc.build(elements)
    buf.seek(0)
    return buf


def department_csv(filters: dict) -> io.BytesIO:
    view = dashboard_service.department_view(**filters)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["IIPS Feedback Report - Department"])
    writer.writerow(["Course", "Faculty", "Semester", "Avg Rating", "Negative %", "Responses"])
    for c in view["courses"]:
        writer.writerow([c["code"], c["faculty_name"], c["semester"], c["avg_rating"], c["negative_pct"], c["responses"]])
    return io.BytesIO(buf.getvalue().encode("utf-8"))


def department_pdf(filters: dict) -> io.BytesIO:
    view = dashboard_service.department_view(**filters)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("IIPS Feedback Report &mdash; Department", styles["Title"]),
        Spacer(1, 12),
    ]
    data = [["Course", "Faculty", "Sem", "Avg", "Neg %", "Responses"]]
    for c in view["courses"]:
        data.append([c["code"], c["faculty_name"], c["semester"], c["avg_rating"], f"{c['negative_pct']}%", c["responses"]])
    elements.append(_styled_table(data))
    doc.build(elements)
    buf.seek(0)
    return buf


def _styled_table(data) -> Table:
    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b57")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    return table
