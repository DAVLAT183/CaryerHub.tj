import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import settings

logger = logging.getLogger("careerhub.email")


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    user = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD
    if not user or not password:
        logger.error(
            "SMTP is not configured: set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in Backend/.env"
        )
        return False

    from_addr = settings.EMAIL_FROM or user
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=15) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        logger.info("Email sent to %s (%s)", to_email, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False


def send_verification_email(to_email: str, name: str, token: str) -> bool:
    return send_email(
        to_email=to_email,
        subject="CareerHub - Код подтверждения",
        html_body=f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <h2>Подтверждение email</h2>
            <p>Привет, {name},</p>
            <p>Введите этот код на странице подтверждения:</p>
            <div style="font-size:32px;letter-spacing:10px;font-weight:bold;
                        background:#F3F4F6;padding:16px 24px;border-radius:8px;
                        text-align:center;margin:16px 0;color:#111827;">
                {token}
            </div>
            <p style="color:#666;font-size:13px;">Код действует 24 часа. Если вы не запрашивали его — просто проигнорируйте письмо.</p>
        </div>
        """,
    )
