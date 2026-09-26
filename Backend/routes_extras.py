import io
import logging
import uuid
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
from auth import get_current_user, get_optional_user, hash_password, verify_password, require_verified_email, generate_verification_code
from config import settings
from email_service import send_email, send_verification_email
from job_parser import parse_somon_tj

extras_router = APIRouter(prefix="/api", tags=["Extras"])
logger = logging.getLogger("careerhub")


# ──────────────────────────── Email Verification ────────────────────────────


@extras_router.post("/auth/send-verification/")
async def send_verification(
    data: dict | None = None,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    email = (data or {}).get("email") or (user.email if user else None)
    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    result = await db.execute(select(User).where(User.email == email))
    target = result.scalar_one_or_none()
    if not target:
        return {"detail": "If the email exists, a verification link has been sent"}

    if user and user.id != target.id:
        raise HTTPException(status_code=403, detail="Cannot send verification for another email")

    if target.is_email_verified:
        return {"detail": "Email is already verified"}

    result = await db.execute(
        select(EmailVerification)
        .where(EmailVerification.user_id == target.id, EmailVerification.is_used == False)
        .order_by(EmailVerification.created_at.desc())
    )
    existing = result.scalar_one_or_none()
    if existing and existing.token.isdigit() and len(existing.token) == 6:
        token = existing.token
    else:
        token = generate_verification_code()
        if existing:
            existing.is_used = True
        db.add(EmailVerification(user_id=target.id, token=token))
        await db.commit()

    sent = send_verification_email(
        to_email=target.email,
        name=target.first_name or target.username,
        token=token,
    )
    if not sent:
        if not (settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD):
            logger.warning(
                "SMTP не настроен — код подтверждения для %s: %s", target.email, token
            )
            return {
                "detail": "SMTP не настроен: код подтверждения выведен в консоль сервера",
                "dev_code": token,
            }
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return {"detail": "Verification email sent"}


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


@extras_router.post("/auth/verify-code/")
async def verify_code(
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    code = str((data or {}).get("code") or "").strip()
    if len(code) != 6 or not code.isdigit():
        raise HTTPException(status_code=400, detail="Введите 6-значный код")

    if user.is_email_verified:
        return {"detail": "Email already verified", "is_email_verified": True}

    result = await db.execute(
        select(EmailVerification)
        .where(
            EmailVerification.user_id == user.id,
            EmailVerification.token == code,
            EmailVerification.is_used == False,
        )
        .order_by(EmailVerification.created_at.desc())
    )
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=400, detail="Неверный код")

    if (datetime.now(timezone.utc) - ev.created_at.replace(tzinfo=timezone.utc)) > timedelta(hours=24):
        raise HTTPException(status_code=400, detail="Срок действия кода истёк, запросите новый")

    ev.is_used = True
    user.is_email_verified = True
    await db.commit()
    return {"detail": "Email verified successfully", "is_email_verified": True}


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

    send_email(
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
            params={"q": query, "format": "json", "limit": 5},
            headers={"User-Agent": "CareerHub/1.0"},
        )
        resp.raise_for_status()
        results = resp.json()

    if not results:
        return {}

    best = results[0]
    for item in results:
        display = (item.get("display_name") or "").lower()
        if any(
            key in display
            for key in ("tajikistan", "таджикистан", "dushanbe", "душанбе", "khujand", "худжанд")
        ):
            best = item
            break

    return {
        "lat": float(best["lat"]),
        "lon": float(best["lon"]),
        "display_name": best.get("display_name", ""),
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
        "polyline": route.get("geometry", {}).get("coordinates", []),
        "steps": steps,
    }


def _format_duration(duration_s: int) -> str:
    total_min = round(duration_s / 60)
    hours, minutes = divmod(total_min, 60)
    if hours > 0:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


def _step_text(instruction: str, step_type: str, modifier: str) -> str:
    directions = {
        "left": "налево",
        "right": "направо",
        "slight left": "легкое поворот налево",
        "slight right": "легкое поворот направо",
        "uturn": "разворот",
    }
    if step_type == "depart":
        return "Начните движение"
    if step_type == "arrive":
        return "Прибытие"
    if step_type == "turn":
        text = f"Поверните {directions.get(modifier, 'поворот')}"
        if instruction:
            text += f" на {instruction}"
        return text
    if step_type == "new name":
        return f"Продолжайте по {instruction}" if instruction else "Продолжайте движение"
    if step_type == "merge":
        return "Встаньте на полосу"
    if step_type == "roundabout":
        return "На круговом движении"
    text = step_type.replace("_", " ").capitalize() if step_type else ""
    if instruction:
        text = f"{text} ({instruction})" if text else instruction
    return text or "Продолжайте движение"


@extras_router.post("/route/")
async def calculate_route(data: dict):
    user_location = str(data.get("user_location") or "").strip()
    job_lat = data.get("job_lat")
    job_lng = data.get("job_lng")

    origin = ""
    destination = ""

    if user_location and job_lat is not None and job_lng is not None:
        origin = user_location
        origin_coords = await _geocode(origin)
        if not origin_coords:
            raise HTTPException(
                status_code=400,
                detail="Не удалось найти координаты вашего места проживания.",
            )
        try:
            dest_coords = {
                "lat": float(job_lat),
                "lon": float(job_lng),
                "display_name": "",
            }
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid job coordinates")
    else:
        origin = str(data.get("origin") or "").strip()
        destination = str(data.get("destination") or "").strip()

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

    distance_km = round(route["distance_m"] / 1000, 1)
    steps = [
        {
            "text": _step_text(s["instruction"], s["type"], s["modifier"]),
            "distance": s["distance_m"],
            "instruction": s["instruction"],
            "distance_m": s["distance_m"],
            "duration_s": s["duration_s"],
            "type": s["type"],
            "modifier": s["modifier"],
        }
        for s in route["steps"]
    ]

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
            "display_name": dest_coords.get("display_name", ""),
        },
        "distance_km": distance_km,
        "duration_min": round(route["duration_s"] / 60, 1),
        "distance_m": route["distance_m"],
        "duration_s": route["duration_s"],
        "distance_text": f"{distance_km} км",
        "duration_text": _format_duration(route["duration_s"]),
        "duration_minutes": round(route["duration_s"] / 60),
        "user_address": origin_coords.get("display_name") or origin,
        "user_coordinates": {"lat": origin_coords["lat"], "lng": origin_coords["lon"]},
        "polyline": route["polyline"],
        "steps": steps,
    }


# ──────────────────────────── PDF Generation ────────────────────────────

FONT_DIR = r"C:\Windows\Fonts"
FONT_PATHS = {
    "arial": f"{FONT_DIR}/arial.ttf",
    "arial_bold": f"{FONT_DIR}/arialbd.ttf",
    "arial_italic": f"{FONT_DIR}/ariali.ttf",
    "arial_bold_italic": f"{FONT_DIR}/arialbi.ttf",
    "times": f"{FONT_DIR}/times.ttf",
    "times_bold": f"{FONT_DIR}/timesbd.ttf",
    "times_italic": f"{FONT_DIR}/timesi.ttf",
    "times_bold_italic": f"{FONT_DIR}/timesbi.ttf",
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


def _job_info_rows(job) -> list[list[str]]:
    info_rows = []
    if getattr(job, "employer_name", None):
        info_rows.append(["Компания", str(job.employer_name)])
    elif job.employer_id:
        info_rows.append(["Компания", "N/A"])
    salary = ""
    if job.salary_min and job.salary_max:
        salary = f"{job.salary_min} - {job.salary_max} TJS"
    elif job.salary_min:
        salary = f"от {job.salary_min} TJS"
    if salary:
        info_rows.append(["Зарплата", salary])
    if job.schedule:
        info_rows.append(["График", job.schedule])
    if job.work_format:
        info_rows.append(["Формат", job.work_format])
    if job.location_address:
        info_rows.append(["Локация", job.location_address])
    if job.experience_required:
        info_rows.append(["Опыт", str(job.experience_required)])
    if job.created_at:
        posted = (
            job.created_at.strftime("%Y-%m-%d")
            if hasattr(job.created_at, "strftime")
            else str(job.created_at)
        )
        info_rows.append(["Опубликовано", posted])
    return info_rows


def _generate_job_pdf(job, style: str = "modern") -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buf = io.BytesIO()
    scheme = STYLE_COLORS.get(style, STYLE_COLORS["modern"])
    primary = colors.HexColor(scheme["primary"])
    accent = colors.HexColor(scheme["accent"])
    text_color = colors.HexColor(scheme["text"])
    info_rows = _job_info_rows(job)
    description = (job.description or "").replace("\n", "<br/>")

    if style == "classic":
        _build_classic_job_pdf(buf, job, info_rows, description, primary, accent, text_color)
    elif style == "minimal":
        _build_minimal_job_pdf(buf, job, info_rows, description, primary, accent, text_color)
    elif style == "creative":
        _build_creative_job_pdf(buf, job, info_rows, description, primary, accent, text_color)
    else:
        _build_modern_job_pdf(buf, job, info_rows, description, primary, accent, text_color)

    buf.seek(0)
    return buf.getvalue()


def _build_modern_job_pdf(buf, job, info_rows, description, primary, accent, text_color):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("MTitle", parent=styles["Title"], fontSize=18, textColor=primary, spaceAfter=6)
    heading_style = ParagraphStyle("MHeading", parent=styles["Heading2"], fontSize=13, textColor=accent, spaceAfter=4)
    body_style = ParagraphStyle("MBody", parent=styles["BodyText"], fontSize=10, leading=14, textColor=text_color)

    elements = []
    header_table = Table([[Paragraph(f"<b>{job.title}</b>", title_style)]], colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), primary),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    if info_rows:
        info_data = [[Paragraph("<b>Параметры</b>", heading_style), ""]]
        for label, value in info_rows:
            info_data.append([f"<b>{label}:</b>", str(value)])
        info_table = Table(info_data, colWidths=[4 * cm, doc.width - 4 * cm])
        info_table.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), accent),
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

    if description:
        elements.append(Paragraph("<b>Описание</b>", heading_style))
        elements.append(Paragraph(description, body_style))

    doc.build(elements)


def _build_classic_job_pdf(buf, job, info_rows, description, primary, accent, text_color):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CTitle", parent=styles["Title"], fontName="Times-Bold", fontSize=20, textColor=primary, alignment=1, spaceAfter=4)
    sub_style = ParagraphStyle("CSub", parent=styles["Normal"], fontName="Times-Roman", fontSize=11, textColor=accent, alignment=1, spaceAfter=10)
    heading_style = ParagraphStyle("CHeading", parent=styles["Heading2"], fontName="Times-Bold", fontSize=12, textColor=primary, spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle("CBody", parent=styles["BodyText"], fontName="Times-Roman", fontSize=11, leading=15, textColor=text_color)

    elements = []
    elements.append(Paragraph(job.title, title_style))
    if getattr(job, "employer_name", None):
        elements.append(Paragraph(str(job.employer_name), sub_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=primary, spaceAfter=10))

    if info_rows:
        data = [["Параметр", "Значение"]]
        data += [[label, str(value)] for label, value in info_rows]
        table = Table(data, colWidths=[4.5 * cm, doc.width - 4.5 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("FONTNAME", (0, 1), (0, -1), "Times-Bold"),
            ("FONTNAME", (1, 1), (1, -1), "Times-Roman"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.8, primary),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FAFAFA")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(table)

    if description:
        elements.append(Paragraph("Описание вакансии", heading_style))
        elements.append(Paragraph(description, body_style))

    doc.build(elements)


def _build_minimal_job_pdf(buf, job, info_rows, description, primary, accent, text_color):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=2.2 * cm, bottomMargin=2 * cm,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("MinTitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=16, textColor=primary, leading=20, spaceAfter=4)
    heading_style = ParagraphStyle("MinHeading", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=accent, leading=12, spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("MinBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=text_color)
    label_style = ParagraphStyle("MinLabel", parent=styles["Normal"], fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#6B7280"), leading=12)
    value_style = ParagraphStyle("MinValue", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5, textColor=text_color, leading=12)

    elements = []
    elements.append(Paragraph(job.title, title_style))
    elements.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#D1D5DB"), spaceBefore=6, spaceAfter=8))

    if info_rows:
        data = []
        for label, value in info_rows:
            data.append([Paragraph(label.upper(), label_style), Paragraph(str(value), value_style)])
        table = Table(data, colWidths=[4 * cm, doc.width - 4 * cm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#E5E7EB")),
        ]))
        elements.append(table)

    if description:
        elements.append(Paragraph("ОПИСАНИЕ", heading_style))
        elements.append(Paragraph(description, body_style))

    doc.build(elements)


def _build_creative_job_pdf(buf, job, info_rows, description, primary, accent, text_color):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=1.2 * cm, bottomMargin=1.5 * cm,
        leftMargin=0, rightMargin=0,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CrTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=22, textColor=colors.white, alignment=TA_CENTER, leading=26, spaceAfter=4,
    )
    sub_style = ParagraphStyle("CrSub", parent=styles["Normal"], fontSize=11, textColor=colors.white, alignment=TA_CENTER)
    heading_style = ParagraphStyle("CrHeading", parent=styles["Heading2"], fontSize=13, textColor=primary, spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle("CrBody", parent=styles["BodyText"], fontSize=10, leading=14, textColor=text_color)

    elements = []
    hero = Table(
        [[Paragraph(f"<b>{job.title}</b>", title_style)],
         [Paragraph(str(getattr(job, "employer_name", "") or "Вакансия"), sub_style)]],
        colWidths=[doc.width],
    )
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), primary),
        ("TOPPADDING", (0, 0), (-1, 0), 18),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 18),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ]))
    elements.append(hero)

    inner_left = 1.2 * cm
    if info_rows:
        badge_rows = []
        for label, value in info_rows:
            badge_rows.append([
                Paragraph(f"<font color='{primary.hexval()}'><b>{label}</b></font>", body_style),
                Paragraph(str(value), body_style),
            ])
        table = Table(badge_rows, colWidths=[4 * cm, doc.width - 4 * cm - 2 * inner_left])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#FFF7ED")),
            ("BOX", (0, 0), (-1, -1), 1, accent),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#FDE68A")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        wrap = Table([[table]], colWidths=[doc.width])
        wrap.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), inner_left),
            ("RIGHTPADDING", (0, 0), (-1, -1), inner_left),
            ("TOPPADDING", (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(wrap)

    if description:
        desc_block = [
            Paragraph(f"<font color='{primary.hexval()}'><b>Описание</b></font>", heading_style),
            Paragraph(description, body_style),
        ]
        desc_wrap = Table([[desc_block]], colWidths=[doc.width])
        desc_wrap.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), inner_left),
            ("RIGHTPADDING", (0, 0), (-1, -1), inner_left),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(desc_wrap)

    doc.build(elements)


def _resume_pdf_data(resume, student_profile=None, user=None) -> dict:
    name = ""
    if user:
        name = f"{user.first_name} {user.last_name}".strip() or user.username
    elif student_profile and getattr(student_profile, "user", None):
        u = student_profile.user
        name = f"{u.first_name} {u.last_name}".strip() or u.username

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

    skills = ""
    if resume.skills:
        skills = ", ".join(resume.skills) if isinstance(resume.skills, list) else str(resume.skills)

    links = []
    if resume.github_url:
        links.append(("GitHub", resume.github_url))
    if resume.portfolio_url:
        links.append(("Portfolio", resume.portfolio_url))
    if resume.linkedin_url:
        links.append(("LinkedIn", resume.linkedin_url))

    return {
        "name": name,
        "title": resume.title or "",
        "info_rows": info_rows,
        "skills": skills,
        "links": links,
        "about": (resume.about or "").replace("\n", "<br/>"),
    }


def _build_modern_resume_pdf(buf, data, scheme):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm)
    primary = colors.HexColor(scheme["primary"])
    accent = colors.HexColor(scheme["accent"])

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ResumeTitle", parent=styles["Title"], fontName="arial_bold", fontSize=18,
                                 textColor=colors.white, spaceAfter=6)
    heading_style = ParagraphStyle("ResumeHeading", parent=styles["Heading2"], fontName="arial_bold", fontSize=13,
                                   textColor=accent, spaceAfter=4)
    table_head_style = ParagraphStyle("ResumeTableHead", parent=styles["Heading2"], fontName="arial_bold", fontSize=13,
                                      textColor=colors.white, spaceAfter=0, spaceBefore=0)
    body_style = ParagraphStyle("ResumeBody", parent=styles["BodyText"], fontName="arial", fontSize=10, leading=14)

    elements = []
    name = data["name"]
    header_data = [[Paragraph(f"<b>{name}</b>", title_style)]]
    if data["title"]:
        header_data[0][0] = Paragraph(f"<b>{name}</b><br/><font size=10>{data['title']}</font>", title_style)

    header_table = Table(header_data, colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), primary),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    if data["info_rows"]:
        info_data = [[Paragraph("Personal Information", table_head_style), ""]]
        for label, value in data["info_rows"]:
            info_data.append([f"{label}:", str(value)])

        info_table = Table(info_data, colWidths=[4 * cm, doc.width - 4 * cm])
        info_table.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), accent),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 1), (0, -1), "arial_bold"),
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

    if data["skills"]:
        elements.append(Paragraph("<b>Skills</b>", heading_style))
        elements.append(Paragraph(data["skills"], body_style))
        elements.append(Spacer(1, 8))

    if data["links"]:
        elements.append(Paragraph("<b>Links</b>", heading_style))
        for label, url in data["links"]:
            elements.append(Paragraph(f"<b>{label}:</b> {url}", body_style))
        elements.append(Spacer(1, 8))

    if data["about"]:
        elements.append(Paragraph("<b>About</b>", heading_style))
        elements.append(Paragraph(data["about"], body_style))

    doc.build(elements)


def _build_classic_resume_pdf(buf, data, scheme):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                            leftMargin=2.2 * cm, rightMargin=2.2 * cm)
    primary = colors.HexColor(scheme["primary"])
    accent = colors.HexColor(scheme["accent"])
    text_color = colors.HexColor(scheme["text"])

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle("ClsName", parent=styles["Title"], fontName="times_bold", fontSize=22,
                                textColor=primary, alignment=1, spaceAfter=2)
    sub_style = ParagraphStyle("ClsSub", parent=styles["Normal"], fontName="times_italic", fontSize=11,
                               textColor=accent, alignment=1, spaceAfter=10)
    heading_style = ParagraphStyle("ClsHeading", parent=styles["Heading2"], fontName="times_bold", fontSize=12,
                                   textColor=primary, spaceBefore=14, spaceAfter=6)
    table_head_style = ParagraphStyle("ClsTableHead", parent=styles["Heading2"], fontName="times_bold", fontSize=12,
                                      textColor=colors.white, spaceBefore=0, spaceAfter=0)
    body_style = ParagraphStyle("ClsBody", parent=styles["BodyText"], fontName="times", fontSize=11,
                                leading=15, textColor=text_color)

    elements = []
    elements.append(Paragraph(data["name"] or " ", name_style))
    if data["title"]:
        elements.append(Paragraph(data["title"], sub_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=primary, spaceAfter=10))

    if data["info_rows"]:
        rows = [[Paragraph("Personal Information", table_head_style), ""]]
        for label, value in data["info_rows"]:
            rows.append([str(label), str(value)])
        table = Table(rows, colWidths=[4.5 * cm, doc.width - 4.5 * cm])
        table.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), primary),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 1), (0, -1), "times_bold"),
            ("FONTNAME", (1, 1), (1, -1), "times"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.8, primary),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(table)

    if data["skills"]:
        elements.append(Paragraph("Skills", heading_style))
        elements.append(Paragraph(data["skills"], body_style))

    if data["links"]:
        elements.append(Paragraph("Links", heading_style))
        for label, url in data["links"]:
            elements.append(Paragraph(f"<b>{label}:</b> {url}", body_style))

    if data["about"]:
        elements.append(Paragraph("About", heading_style))
        elements.append(Paragraph(data["about"], body_style))

    doc.build(elements)


def _build_minimal_resume_pdf(buf, data, scheme):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2.2 * cm, bottomMargin=2 * cm,
                            leftMargin=2.5 * cm, rightMargin=2.5 * cm)
    primary = colors.HexColor(scheme["primary"])
    accent = colors.HexColor(scheme["accent"])
    text_color = colors.HexColor(scheme["text"])

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle("MinName", parent=styles["Normal"], fontName="arial_bold", fontSize=16,
                                textColor=primary, leading=20, spaceAfter=2)
    sub_style = ParagraphStyle("MinSub", parent=styles["Normal"], fontName="arial", fontSize=10.5,
                               textColor=accent, leading=14, spaceAfter=6)
    heading_style = ParagraphStyle("MinHeading", parent=styles["Normal"], fontName="arial_bold", fontSize=9,
                                   textColor=accent, leading=12, spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("MinBody", parent=styles["BodyText"], fontName="arial", fontSize=9.5,
                                leading=13.5, textColor=text_color)
    label_style = ParagraphStyle("MinLabel", parent=styles["Normal"], fontName="arial", fontSize=9,
                                 textColor=colors.HexColor("#6B7280"), leading=12)
    value_style = ParagraphStyle("MinValue", parent=styles["Normal"], fontName="arial", fontSize=9.5,
                                 textColor=text_color, leading=12)

    elements = []
    elements.append(Paragraph(data["name"] or " ", name_style))
    if data["title"]:
        elements.append(Paragraph(data["title"], sub_style))
    elements.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#D1D5DB"),
                               spaceBefore=4, spaceAfter=8))

    if data["info_rows"]:
        rows = []
        for label, value in data["info_rows"]:
            rows.append([Paragraph(label.upper(), label_style), Paragraph(str(value), value_style)])
        table = Table(rows, colWidths=[4 * cm, doc.width - 4 * cm])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
        ]))
        elements.append(table)

    if data["skills"]:
        elements.append(Paragraph("SKILLS", heading_style))
        elements.append(Paragraph(data["skills"], body_style))

    if data["links"]:
        elements.append(Paragraph("LINKS", heading_style))
        for label, url in data["links"]:
            elements.append(Paragraph(f"<b>{label}:</b> {url}", body_style))

    if data["about"]:
        elements.append(Paragraph("ABOUT", heading_style))
        elements.append(Paragraph(data["about"], body_style))

    doc.build(elements)


def _build_creative_resume_pdf(buf, data, scheme):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.2 * cm, bottomMargin=1.5 * cm,
                            leftMargin=0, rightMargin=0)
    primary = colors.HexColor(scheme["primary"])
    accent = colors.HexColor(scheme["accent"])
    text_color = colors.HexColor(scheme["text"])

    styles = getSampleStyleSheet()
    hero_name_style = ParagraphStyle("CrName", parent=styles["Title"], fontName="arial_bold", fontSize=22,
                                     textColor=colors.white, alignment=TA_CENTER, leading=26, spaceAfter=4)
    hero_sub_style = ParagraphStyle("CrSub", parent=styles["Normal"], fontName="arial", fontSize=11,
                                    textColor=colors.white, alignment=TA_CENTER)
    heading_style = ParagraphStyle("CrHeading", parent=styles["Heading2"], fontName="arial_bold", fontSize=13,
                                   textColor=primary, spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle("CrBody", parent=styles["BodyText"], fontName="arial", fontSize=10, leading=14,
                                textColor=text_color)

    inner = 1.2 * cm

    def wrap(flowables):
        block = Table([[flowables]], colWidths=[doc.width])
        block.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), inner),
            ("RIGHTPADDING", (0, 0), (-1, -1), inner),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return block

    elements = []
    hero_rows = [[Paragraph(f"<b>{data['name']}</b>", hero_name_style)]]
    if data["title"]:
        hero_rows.append([Paragraph(data["title"], hero_sub_style)])
    hero = Table(hero_rows, colWidths=[doc.width])
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), primary),
        ("TOPPADDING", (0, 0), (-1, 0), 18),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 18),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ]))
    elements.append(hero)

    if data["info_rows"]:
        rows = []
        for label, value in data["info_rows"]:
            rows.append([
                Paragraph(f"<font color='{primary.hexval()}'><b>{label}</b></font>", body_style),
                Paragraph(str(value), body_style),
            ])
        table = Table(rows, colWidths=[4 * cm, doc.width - 4 * cm - 2 * inner])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#FFF7ED")),
            ("BOX", (0, 0), (-1, -1), 1, accent),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#FDE68A")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(wrap([table]))

    if data["skills"]:
        elements.append(wrap([
            Paragraph(f"<font color='{accent.hexval()}'><b>SKILLS</b></font>", heading_style),
            Paragraph(data["skills"], body_style),
        ]))

    if data["links"]:
        link_blocks = [Paragraph(f"<font color='{accent.hexval()}'><b>LINKS</b></font>", heading_style)]
        for label, url in data["links"]:
            link_blocks.append(Paragraph(f"<b>{label}:</b> {url}", body_style))
        elements.append(wrap(link_blocks))

    if data["about"]:
        elements.append(wrap([
            Paragraph(f"<font color='{accent.hexval()}'><b>ABOUT</b></font>", heading_style),
            Paragraph(data["about"], body_style),
        ]))

    doc.build(elements)


RESUME_PDF_BUILDERS = {
    "classic": _build_classic_resume_pdf,
    "minimal": _build_minimal_resume_pdf,
    "creative": _build_creative_resume_pdf,
}


def _generate_resume_pdf(resume, student_profile=None, user=None, style: str = "modern") -> bytes:
    data = _resume_pdf_data(resume, student_profile, user)
    scheme = STYLE_COLORS.get(style, STYLE_COLORS["modern"])
    builder = RESUME_PDF_BUILDERS.get(style, _build_modern_resume_pdf)

    buf = io.BytesIO()
    builder(buf, data, scheme)
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
    user: User = Depends(require_verified_email),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in ("employer", "staff") and not user.is_staff:
        raise HTTPException(status_code=403, detail="Only employers can trigger parsing")

    result = await parse_somon_tj(db, max_jobs)
    return result
