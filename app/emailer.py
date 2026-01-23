from __future__ import annotations

import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(to_email: str, subject: str, body: str) -> None:
    """Send an email if SMTP env vars are configured.
    Safe no-op if missing config so the app still runs.
    """
    cfg = current_app.config
    host = cfg.get("SMTP_HOST") or cfg.get("SMTP_SERVER")
    user = cfg.get("SMTP_USER") or cfg.get("SMTP_USERNAME")
    password = cfg.get("SMTP_PASSWORD")
    from_email = cfg.get("SMTP_FROM") or cfg.get("FROM_EMAIL") or user
    port = int(cfg.get("SMTP_PORT") or 587)

    if not host or not from_email:
        current_app.logger.info("SMTP not configured; skipping email.")
        return

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
    except Exception as e:
        current_app.logger.warning(f"Email send failed: {e}")
