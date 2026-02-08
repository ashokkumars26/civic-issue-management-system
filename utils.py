from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from io import BytesIO
from typing import Optional
import os


def ai_analyze_issue(issue_type: str, description: str) -> str:
    """
    Simple rule-based AI-style analysis summary.
    In a real system, this could call an external ML/NLP service.
    """
    severity = "Moderate"
    priority = "Medium"

    desc_lower = description.lower()
    if "urgent" in desc_lower or "immediately" in desc_lower:
        severity = "High"
        priority = "High"
    if "school" in desc_lower or "hospital" in desc_lower:
        priority = "High"

    return (
        f"Automated analysis for issue type '{issue_type}':\n"
        f"- Estimated severity: {severity}\n"
        f"- Suggested resolution priority: {priority}\n"
        f"- Notes: Location and citizen description indicate that field\n"
        f"  inspection by the respective civic department is recommended."
    )


def _draw_wrapped_text(c, text: str, x: float, y: float, max_width: float, line_height: float):
    """Utility to wrap and draw text on the PDF canvas."""
    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if c.stringWidth(test_line, "Helvetica", 10) <= max_width:
            line = test_line
        else:
            c.drawString(x, y, line)
            y -= line_height
            line = word
    if line:
        c.drawString(x, y, line)
        y -= line_height
    return y


def _maybe_draw_image(c, image_path: Optional[str], x: float, y: float, width: float, height: float):
    if image_path and os.path.exists(image_path):
        try:
            c.drawImage(image_path, x, y, width=width, height=height, preserveAspectRatio=True, mask='auto')
        except Exception:
            # If image fails to load, ignore in PDF
            pass


def generate_issue_pdf(issue) -> bytes:
    """Generate a government-style PDF report for a given issue."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin = 20 * mm
    y = height - margin

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y, "GOVERNMENT OF TAMIL NADU - CIVIC ISSUE REPORT")
    y -= 20

    c.setFont("Helvetica", 10)
    c.drawString(margin, y, "Chennai Metropolitan Area - AI-Assisted CivicCare System")
    y -= 20

    # Issue metadata
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, f"Issue ID: {issue.id}")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Issue Type: {issue.issue_type}")
    y -= 15

    citizen_name = issue.user.name if issue.user and issue.user.name else "Not Provided"
    citizen_email = issue.user.email if issue.user and issue.user.email else "Not Provided"
    citizen_phone = issue.user.phone if issue.user and issue.user.phone else "Not Provided"

    c.drawString(margin, y, f"Citizen Name: {citizen_name}")
    y -= 15
    c.drawString(margin, y, f"Citizen Email: {citizen_email}")
    y -= 15
    c.drawString(margin, y, f"Citizen Phone: {citizen_phone}")
    y -= 20

    # Location
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Location Details")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Area: {issue.area}")
    y -= 15
    c.drawString(margin, y, f"Street: {issue.street or '-'}")
    y -= 15
    c.drawString(margin, y, f"Landmark: {issue.landmark or '-'}")
    y -= 20

    # Description
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Issue Description")
    y -= 15
    c.setFont("Helvetica", 10)
    y = _draw_wrapped_text(c, issue.description, margin, y, width - 2 * margin, 12)
    y -= 10

    # AI Analysis
    if issue.ai_summary:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "AI Analysis Summary")
        y -= 15
        c.setFont("Helvetica", 10)
        y = _draw_wrapped_text(c, issue.ai_summary, margin, y, width - 2 * margin, 12)
        y -= 10

    # Status timeline
    if issue.status_logs:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "Status Timeline")
        y -= 15
        c.setFont("Helvetica", 10)
        for log in issue.status_logs:
            line = f"{log.created_at.strftime('%d-%m-%Y %H:%M')} - {log.status}: {log.remarks or ''}"
            y = _draw_wrapped_text(c, line, margin, y, width - 2 * margin, 12)
        y -= 10

    # Authority remarks
    if issue.authority_remarks:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "Authority Remarks")
        y -= 15
        c.setFont("Helvetica", 10)
        y = _draw_wrapped_text(c, issue.authority_remarks, margin, y, width - 2 * margin, 12)
        y -= 10

    # Feedback
    if issue.feedbacks:
        fb = issue.feedbacks[-1]
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "Citizen Feedback")
        y -= 15
        c.setFont("Helvetica", 10)
        c.drawString(margin, y, f"Rating: {fb.rating}/5")
        y -= 15
        if fb.comments:
            y = _draw_wrapped_text(c, fb.comments, margin, y, width - 2 * margin, 12)
        y -= 10

    # Images
    c.showPage()
    y = height - margin
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Photographic Evidence")
    y -= 30

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Before Fix")
    c.drawString(width / 2, y, "After Fix")
    y -= 20

    img_height = 80 * mm
    img_width = (width / 2) - (1.5 * margin)

    _maybe_draw_image(c, issue.before_image, margin, y - img_height, img_width, img_height)
    _maybe_draw_image(c, issue.after_image, width / 2, y - img_height, img_width, img_height)

    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(
        margin,
        15 * mm,
        "Digitally generated document by Chennai CivicCare AI System - No manual signature required."
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer




