import io
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import (
    User, EmailVerification, PasswordResetToken,
    TariffPlan, UserSubscription, Payment, Job, Resume,
    StudentProfile, Notification,
)
from schemas import TariffPlanSchema
from auth import get_current_user, hash_password, verify_password
from config import settings
from job_parser import parse_somon_tj

extras_router = APIRouter(prefix="/api", tags=["Extras"])

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = settings.__dict__.get("SMTP_USER", "")
SMTP_PASS = settings.__dict__.get("SMTP_PASS", "")
SMTP_FROM = settings.__dict__.get("SMTP_FROM", "noreply@careerhub.tj")


def _send_email(to_email: str, subject: str, html_body: str):
    if not SMTP_USER:
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    except Exception:
        pass


# ──────────────────────────── Email Verification ────────────────────────────


@extras_router.post("/auth/send-verification/")
async def send_verification(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.is_email_verified:
        return {"detail": "Email is already verified"}

    result = await db.execute(
        select(EmailVerification)
        .where(EmailVerification.user_id == user.id, EmailVerification.is_used == False)
        .order_by(EmailVerification.created_at.desc())
    )
    existing = result.scalar_one_or_none()
    if existing:
        token = existing.token
    else:
        token = str(uuid.uuid4())
        ev = EmailVerification(user_id=user.id, token=token)
        db.add(ev)
        await db.commit()

    verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={token}"

    _send_email(
        to_email=user.email,
        subject="CareerHub - Verify your email",
        html_body=f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <h2>Email Verification</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>Click the link below to verify your email address:</p>
            <a href="{verify_url}"
               style="display:inline-block;padding:12px 24px;background:#4F46E5;color:#fff;
                      text-decoration:none;border-radius:6px;margin:16px 0;">
                Verify Email
            </a>
            <p style="color:#666;font-size:13px;">Or copy this link: {verify_url}</p>
            <p style="color:#999;font-size:12px;">This link expires in 24 hours.</p>
        </div>
        """,
    )

    return {"detail": "Verification email sent", "token": token}


@extras_router.get("/auth/verify-email/")
async def verify_email(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailVerification).where(
            EmailVerification.token == token,
            EmailVerification.is_used == False,
        )
    )
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if (datetime.now(timezone.utc) - ev.created_at.replace(tzinfo=timezone.utc)) > timedelta(hours=24):
        raise HTTPException(status_code=400, detail="Token expired")

    ev.is_used = True

    result = await db.execute(select(User).where(User.id == ev.user_id))
    user = result.scalar_one_or_none()
    if user:
        user.is_email_verified = True

    await db.commit()
    return {"detail": "Email verified successfully"}


@extras_router.get("/auth/check-verification/")
async def check_verification(
    user: User = Depends(get_current_user),
):
    return {"is_email_verified": user.is_email_verified}


# ──────────────────────────── Password Reset ────────────────────────────


@extras_router.post("/auth/password-reset/")
async def request_password_reset(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    email = data.get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return {"detail": "If the email exists, a reset link has been sent"}

    token = str(uuid.uuid4())
    prt = PasswordResetToken(user_id=user.id, token=token)
    db.add(prt)
    await db.commit()

    reset_url = f"{settings.FRONTEND_URL}/auth/password-reset-confirm?token={token}"

    _send_email(
        to_email=user.email,
        subject="CareerHub - Password Reset",
        html_body=f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <h2>Password Reset</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_url}"
               style="display:inline-block;padding:12px 24px;background:#DC2626;color:#fff;
                      text-decoration:none;border-radius:6px;margin:16px 0;">
                Reset Password
            </a>
            <p style="color:#666;font-size:13px;">Or copy this link: {reset_url}</p>
            <p style="color:#999;font-size:12px;">This link expires in 1 hour. Ignore if you didn't request this.</p>
        </div>
        """,
    )

    return {"detail": "If the email exists, a reset link has been sent"}


@extras_router.post("/auth/password-reset/confirm/")
async def confirm_password_reset(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    token = data.get("token", "")
    new_password = data.get("password", "")

    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and password required")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == token,
            PasswordResetToken.is_used == False,
        )
    )
    prt = result.scalar_one_or_none()
    if not prt:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if (datetime.now(timezone.utc) - prt.created_at.replace(tzinfo=timezone.utc)) > timedelta(hours=1):
        raise HTTPException(status_code=400, detail="Token expired")

    prt.is_used = True

    result = await db.execute(select(User).where(User.id == prt.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.hashed_password = hash_password(new_password)
    await db.commit()

    return {"detail": "Password reset successfully"}


# ──────────────────────────── Tariff Plans ────────────────────────────


@extras_router.get("/tariffs/", response_model=list[TariffPlanSchema])
async def list_tariffs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TariffPlan).where(TariffPlan.is_active == True)
    )
    plans = result.scalars().all()
    return [TariffPlanSchema.model_validate(p) for p in plans]


# ──────────────────────────── Route Calculation ────────────────────────────


async def _geocode(query: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": "CareerHub/1.0"},
        )
        resp.raise_for_status()
        results = resp.json()

    if not results:
        return {}

    r = results[0]
    return {
        "lat": float(r["lat"]),
        "lon": float(r["lon"]),
        "display_name": r.get("display_name", ""),
    }


async def _route_osrm(lat1: float, lon1: float, lat2: float, lon2: float) -> dict:
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}"
        f"?overview=full&geometries=geojson&steps=true"
    )
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        return {}

    route = data["routes"][0]
    legs = route.get("legs", [])
    steps = []
    for leg in legs:
        for step in leg.get("steps", []):
            maneuver = step.get("maneuver", {})
            steps.append({
                "instruction": step.get("name", "").strip() or maneuver.get("type", ""),
                "distance_m": round(step.get("distance", 0)),
                "duration_s": round(step.get("duration", 0)),
                "type": maneuver.get("type", ""),
                "modifier": maneuver.get("modifier", ""),
            })

    return {
        "distance_m": round(route.get("distance", 0)),
        "duration_s": round(route.get("duration", 0)),
        "steps": steps,
    }


@extras_router.post("/route/")
async def calculate_route(data: dict):
    origin = data.get("origin", "")
    destination = data.get("destination", "")

    if not origin or not destination:
        raise HTTPException(status_code=400, detail="origin and destination required")

    origin_coords = await _geocode(origin)
    if not origin_coords:
        raise HTTPException(status_code=404, detail=f"Could not geocode origin: {origin}")

    dest_coords = await _geocode(destination)
    if not dest_coords:
        raise HTTPException(status_code=404, detail=f"Could not geocode destination: {destination}")

    route = await _route_osrm(
        origin_coords["lat"], origin_coords["lon"],
        dest_coords["lat"], dest_coords["lon"],
    )

    if not route:
        raise HTTPException(status_code=502, detail="Route calculation failed")

    duration_min = round(route["duration_s"] / 60, 1)
    distance_km = round(route["distance_m"] / 1000, 2)

    return {
        "origin": {
            "query": origin,
            "lat": origin_coords["lat"],
            "lon": origin_coords["lon"],
            "display_name": origin_coords["display_name"],
        },
        "destination": {
            "query": destination,
            "lat": dest_coords["lat"],
            "lon": dest_coords["lon"],
            "display_name": dest_coords["display_name"],
        },
        "distance_km": distance_km,
        "duration_min": duration_min,
        "distance_m": route["distance_m"],
        "duration_s": route["duration_s"],
        "steps": route["steps"],
    }


# ──────────────────────────── PDF Generation ────────────────────────────

FONT_DIR = r"C:\Windows\Fonts"
FONT_PATHS = {
    "arial": f"{FONT_DIR}/arial.ttf",
    "arial_bold": f"{FONT_DIR}/arialbd.ttf",
    "arial_italic": f"{FONT_DIR}/ariali.ttf",
    "arial_bold_italic": f"{FONT_DIR}/arialbi.ttf",
}

STYLE_COLORS = {
    "classic": {"primary": "#1a1a2e", "accent": "#16213e", "text": "#333333", "header_bg": "#1a1a2e"},
    "modern": {"primary": "#4F46E5", "accent": "#7C3AED", "text": "#374151", "header_bg": "#4F46E5"},
    "minimal": {"primary": "#111827", "accent": "#6B7280", "text": "#374151", "header_bg": "#F3F4F6"},
    "creative": {"primary": "#EC4899", "accent": "#F59E0B", "text": "#1F2937", "header_bg": "#EC4899"},
}


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _register_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    registered = []
    for name, path in FONT_PATHS.items():
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            registered.append(name)
        except Exception:
            pass
    return registered


def _generate_job_pdf(job, style: str = "modern") -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib.enums import TA_LEFT, TA_CENTER

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm)
    scheme = STYLE_COLORS.get(style, STYLE_COLORS["modern"])
    primary_rgb = _hex_to_rgb(scheme["primary"])
    accent_rgb = _hex_to_rgb(scheme["accent"])

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18,
                                 textColor=colors.Color(primary_rgb[0] / 255, primary_rgb[1] / 255, primary_rgb[2] / 255),
                                 spaceAfter=6)
    heading_style = ParagraphStyle("Heading2", parent=styles["Heading2"], fontSize=13,
                                   textColor=colors.Color(accent_rgb[0] / 255, accent_rgb[1] / 255, accent_rgb[2] / 255),
                                   spaceAfter=4)
    body_style = ParagraphStyle("Body2", parent=styles["BodyText"], fontSize=10, leading=14)

    elements = []

    header_data = [[Paragraph(f"<b>{job.title}</b>", title_style)]]
    header_table = Table(header_data, colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.Color(primary_rgb[0] / 255, primary_rgb[1] / 255, primary_rgb[2] / 255)),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    info_rows = []
    if job.employer_id:
        info_rows.append(["Company", str(getattr(job, 'employer_name', 'N/A'))])
    salary = ""
    if job.salary_min and job.salary_max:
        salary = f"{job.salary_min} - {job.salary_max} TJS"
    elif job.salary_min:
        salary = f"From {job.salary_min} TJS"
    if salary:
        info_rows.append(["Salary", salary])
    if job.schedule:
        info_rows.append(["Schedule", job.schedule])
    if job.work_format:
        info_rows.append(["Work Format", job.work_format])
    if job.location_address:
        info_rows.append(["Location", job.location_address])
    if job.created_at:
        info_rows.append(["Posted", job.created_at.strftime("%Y-%m-%d") if hasattr(job.created_at, 'strftime') else str(job.created_at)])

    if info_rows:
        info_data = [[Paragraph("<b>Job Details</b>", heading_style), ""]]
        for label, value in info_rows:
            info_data.append([f"<b>{label}:</b>", str(value)])

        info_table = Table(info_data, colWidths=[4 * cm, doc.width - 4 * cm])
        info_style = [
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(accent_rgb[0] / 255, accent_rgb[1] / 255, accent_rgb[2] / 255)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        info_table.setStyle(TableStyle(info_style))
        elements.append(info_table)
        elements.append(Spacer(1, 12))

    if job.description:
        elements.append(Paragraph("<b>Description</b>", heading_style))
        elements.append(Paragraph(job.description.replace("\n", "<br/>"), body_style))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()


def _generate_resume_pdf(resume, student_profile=None, user=None, style: str = "modern") -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm)
    scheme = STYLE_COLORS.get(style, STYLE_COLORS["modern"])
    primary_rgb = _hex_to_rgb(scheme["primary"])
    accent_rgb = _hex_to_rgb(scheme["accent"])

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ResumeTitle", parent=styles["Title"], fontSize=18,
                                 textColor=colors.Color(primary_rgb[0] / 255, primary_rgb[1] / 255, primary_rgb[2] / 255),
                                 spaceAfter=6)
    heading_style = ParagraphStyle("ResumeHeading", parent=styles["Heading2"], fontSize=13,
                                   textColor=colors.Color(accent_rgb[0] / 255, accent_rgb[1] / 255, accent_rgb[2] / 255),
                                   spaceAfter=4)
    body_style = ParagraphStyle("ResumeBody", parent=styles["BodyText"], fontSize=10, leading=14)

    elements = []

    name = ""
    if user:
        name = f"{user.first_name} {user.last_name}".strip() or user.username
    elif student_profile and student_profile.user:
        u = student_profile.user
        name = f"{u.first_name} {u.last_name}".strip() or u.username

    header_data = [[Paragraph(f"<b>{name}</b>", title_style)]]
    if resume.title:
        header_data[0][0] = Paragraph(f"<b>{name}</b><br/><font size=10>{resume.title}</font>", title_style)

    header_table = Table(header_data, colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.Color(primary_rgb[0] / 255, primary_rgb[1] / 255, primary_rgb[2] / 255)),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    info_rows = []
    if user and user.email:
        info_rows.append(["Email", user.email])
    if user and user.phone:
        info_rows.append(["Phone", user.phone])
    if student_profile:
        if student_profile.university:
            info_rows.append(["University", student_profile.university])
        if student_profile.faculty:
            info_rows.append(["Faculty", student_profile.faculty])
        if student_profile.course:
            info_rows.append(["Course", str(student_profile.course)])
        if student_profile.city:
            info_rows.append(["City", student_profile.city])
    if resume.schedule_type:
        info_rows.append(["Schedule", resume.schedule_type])
    if resume.work_format:
        info_rows.append(["Work Format", resume.work_format])

    if info_rows:
        info_data = [[Paragraph("<b>Personal Information</b>", heading_style), ""]]
        for label, value in info_rows:
            info_data.append([f"<b>{label}:</b>", str(value)])

        info_table = Table(info_data, colWidths=[4 * cm, doc.width - 4 * cm])
        info_table.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(accent_rgb[0] / 255, accent_rgb[1] / 255, accent_rgb[2] / 255)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 12))

    if resume.skills:
        elements.append(Paragraph("<b>Skills</b>", heading_style))
        skills_text = ", ".join(resume.skills) if isinstance(resume.skills, list) else str(resume.skills)
        elements.append(Paragraph(skills_text, body_style))
        elements.append(Spacer(1, 8))

    links = []
    if resume.github_url:
        links.append(("GitHub", resume.github_url))
    if resume.portfolio_url:
        links.append(("Portfolio", resume.portfolio_url))
    if resume.linkedin_url:
        links.append(("LinkedIn", resume.linkedin_url))
    if links:
        elements.append(Paragraph("<b>Links</b>", heading_style))
        for label, url in links:
            elements.append(Paragraph(f"<b>{label}:</b> {url}", body_style))
        elements.append(Spacer(1, 8))

    if resume.about:
        elements.append(Paragraph("<b>About</b>", heading_style))
        elements.append(Paragraph(resume.about.replace("\n", "<br/>"), body_style))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()


@extras_router.get("/jobs/{job_id}/pdf/")
async def get_job_pdf(
    job_id: int,
    style: str = Query("modern", pattern="^(classic|modern|minimal|creative)$"),
    db: AsyncSession = Depends(get_db),
):
    _register_fonts()

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.employer_id:
        from models import EmployerProfile
        emp_result = await db.execute(select(EmployerProfile).where(EmployerProfile.id == job.employer_id))
        emp = emp_result.scalar_one_or_none()
        if emp:
            job.employer_name = emp.company_name
        else:
            job.employer_name = "N/A"
    else:
        job.employer_name = "N/A"

    pdf_bytes = _generate_job_pdf(job, style)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="job_{job_id}.pdf"'},
    )


@extras_router.get("/resumes/{resume_id}/pdf/")
async def get_resume_pdf(
    resume_id: int,
    style: str = Query("modern", pattern="^(classic|modern|minimal|creative)$"),
    db: AsyncSession = Depends(get_db),
):
    _register_fonts()

    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    student_profile = None
    user = None
    if resume.student_id:
        sp_result = await db.execute(select(StudentProfile).where(StudentProfile.id == resume.student_id))
        student_profile = sp_result.scalar_one_or_none()
        if student_profile:
            u_result = await db.execute(select(User).where(User.id == student_profile.user_id))
            user = u_result.scalar_one_or_none()

    pdf_bytes = _generate_resume_pdf(resume, student_profile, user, style)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="resume_{resume_id}.pdf"'},
    )


# ──────────────────────────── Parsing (Employer Only) ────────────────────────────


@extras_router.post("/parsing/somon-tj/")
async def trigger_somon_parsing(
    max_jobs: int = Query(30, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("employer", "staff") and not user.is_staff:
        raise HTTPException(status_code=403, detail="Only employers can trigger parsing")

    result = await parse_somon_tj(db, max_jobs)
    return result
