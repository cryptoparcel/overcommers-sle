from __future__ import annotations

import smtplib
from email.message import EmailMessage
from flask import current_app


def send_email(subject: str, body: str, to_email: str) -> bool:
    """Send an email if SMTP is configured. Returns True if sent."""
    cfg = current_app.config
    host = cfg.get("SMTP_HOST", "")
    if not host:
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.get("FROM_EMAIL")
    msg["To"] = to_email
    msg.set_content(body)

    port = int(cfg.get("SMTP_PORT", 587))
    username = cfg.get("SMTP_USERNAME", "")
    password = cfg.get("SMTP_PASSWORD", "")
    use_tls = bool(cfg.get("SMTP_USE_TLS", True))

    try:
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=20)
            server.starttls()
        else:
            server = smtplib.SMTP(host, port, timeout=20)

        if username and password:
            server.login(username, password)

        server.send_message(msg)
        server.quit()
        return True
    except Exception:
        # Don't crash the request path on email failures.
        current_app.logger.exception("Email send failed")
        return False
