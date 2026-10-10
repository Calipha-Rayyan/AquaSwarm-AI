"""Optional e-mail notifications (Phase 2 groundwork).

Nothing is sent unless SMTP is configured:
  AQUASWARM_SMTP_HOST, AQUASWARM_SMTP_PORT (587), AQUASWARM_SMTP_USER,
  AQUASWARM_SMTP_PASSWORD, AQUASWARM_SMTP_FROM
Messages are best-effort and never raise into the caller.
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Iterable

log = logging.getLogger("aquaswarm.notify")


def configured() -> bool:
    return bool(os.getenv("AQUASWARM_SMTP_HOST", "").strip())


def send_email(to: str | Iterable[str], subject: str, body: str) -> bool:
    if not configured():
        return False
    recipients = [to] if isinstance(to, str) else [r for r in to if r]
    if not recipients:
        return False

    sender = os.getenv("AQUASWARM_SMTP_FROM") or os.getenv("AQUASWARM_SMTP_USER") or "aquaswarm@localhost"
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = sender, ", ".join(recipients), subject
    message.set_content(body)

    try:
        host = os.environ["AQUASWARM_SMTP_HOST"].strip()
        port = int(os.getenv("AQUASWARM_SMTP_PORT", "587"))
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            user = os.getenv("AQUASWARM_SMTP_USER", "")
            if user:
                smtp.login(user, os.getenv("AQUASWARM_SMTP_PASSWORD", ""))
            smtp.send_message(message)
        return True
    except Exception as exc:  # never break the workflow because mail failed
        log.warning("E-mail not sent: %s", exc)
        return False


def notify_managers(subject: str, body: str) -> bool:
    """E-mail every active manager/administrator (no-op without SMTP)."""
    if not configured():
        return False
    from backend import users

    return send_email(users.active_emails(("manager", "admin")), subject, body)