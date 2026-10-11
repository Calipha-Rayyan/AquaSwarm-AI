"""Notification Subsystem for AquaSwarm AI.

Provides modular dispatch for:
1. E-mail (SMTP): Alerts to managers, password resets, access approvals.
2. WhatsApp: Modular provider adapter (Twilio or Meta Cloud API) with safe credential validation.
3. Deduplication: Prevents repeated identical notifications within a cooldown window.
4. Testing: Self-test functions for configuration auditing without exposing secrets.
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
import time
from email.message import EmailMessage
from typing import Any, Dict, Iterable, List, Optional

log = logging.getLogger("aquaswarm.notify")

# In-memory deduplication cache: key -> timestamp
_NOTIFICATION_CACHE: Dict[str, float] = {}
DEDUP_COOLDOWN_SECONDS = 600.0  # 10 minutes


def _dedup_key(channel: str, recipient: str, subject: str) -> str:
    return f"{channel}:{recipient}:{subject}".strip().lower()


def is_suppressed(channel: str, recipient: str, subject: str) -> bool:
    """Check if an identical notification was sent recently within cooldown."""
    key = _dedup_key(channel, recipient, subject)
    last_sent = _NOTIFICATION_CACHE.get(key)
    now = time.monotonic()
    if last_sent is not None and (now - last_sent) < DEDUP_COOLDOWN_SECONDS:
        return True
    return False


def record_sent(channel: str, recipient: str, subject: str) -> None:
    key = _dedup_key(channel, recipient, subject)
    _NOTIFICATION_CACHE[key] = time.monotonic()


# ---------------------------------------------------------------------------
# E-mail (SMTP)
# ---------------------------------------------------------------------------

def email_configured() -> bool:
    return bool(os.getenv("AQUASWARM_SMTP_HOST", "").strip())


# Alias for backwards compatibility
configured = email_configured


def send_email(to: str | Iterable[str], subject: str, body: str, bypass_dedup: bool = False) -> bool:
    if not email_configured():
        return False

    recipients = [to] if isinstance(to, str) else [r for r in to if r]
    if not recipients:
        return False

    recipient_str = ", ".join(recipients)
    if not bypass_dedup and is_suppressed("email", recipient_str, subject):
        log.info("Email suppressed by deduplication cooldown: %s", subject)
        return True

    sender = os.getenv("AQUASWARM_SMTP_FROM") or os.getenv("AQUASWARM_SMTP_USER") or "aquaswarm@localhost"
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = sender, recipient_str, subject
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
        record_sent("email", recipient_str, subject)
        return True
    except Exception as exc:
        log.warning("E-mail dispatch failed: %s", exc)
        return False


def notify_managers(subject: str, body: str) -> bool:
    """E-mail every active manager and administrator (no-op without SMTP)."""
    if not email_configured():
        return False
    from backend import users

    admins_and_managers = users.active_emails(("manager", "admin"))
    if not admins_and_managers:
        return False
    return send_email(admins_and_managers, subject, body)


# ---------------------------------------------------------------------------
# WhatsApp Adapter (Twilio / Meta Cloud API)
# ---------------------------------------------------------------------------

def whatsapp_configured() -> bool:
    """Check if WhatsApp provider credentials are set."""
    # Twilio WhatsApp check
    twilio_ready = bool(
        os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        and os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        and os.getenv("TWILIO_WHATSAPP_NUMBER", "").strip()
    )
    # Meta WhatsApp Cloud API check
    meta_ready = bool(
        os.getenv("WHATSAPP_API_TOKEN", "").strip()
        and os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    )
    return twilio_ready or meta_ready


def send_whatsapp(to_number: str, message: str, bypass_dedup: bool = False) -> Dict[str, Any]:
    """Send a WhatsApp message via configured provider.

    Returns structured status dict without logging secrets.
    """
    to_clean = (to_number or "").strip()
    if not to_clean:
        return {"success": False, "error": "Recipient phone number is required."}

    if not whatsapp_configured():
        return {
            "success": False,
            "error": "WhatsApp provider credentials (Twilio or Meta Cloud API) are not configured in environment.",
        }

    if not bypass_dedup and is_suppressed("whatsapp", to_clean, message[:30]):
        return {"success": True, "suppressed": True, "message": "Suppressed by deduplication cooldown."}

    # If Twilio is configured
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "").strip()

    if account_sid and auth_token and from_number:
        try:
            import requests

            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            sender = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"
            target = to_clean if to_clean.startswith("whatsapp:") else f"whatsapp:{to_clean}"
            resp = requests.post(
                url,
                data={"From": sender, "To": target, "Body": message},
                auth=(account_sid, auth_token),
                timeout=10,
            )
            if resp.status_code in (200, 201):
                record_sent("whatsapp", to_clean, message[:30])
                return {"success": True, "provider": "Twilio", "sid": resp.json().get("sid")}
            return {"success": False, "provider": "Twilio", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as exc:
            return {"success": False, "provider": "Twilio", "error": str(exc)}

    # If Meta Cloud API is configured
    api_token = os.getenv("WHATSAPP_API_TOKEN", "").strip()
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    if api_token and phone_id:
        try:
            import requests

            url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
            headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
            payload = {
                "messaging_product": "whatsapp",
                "to": to_clean.replace("+", "").replace("whatsapp:", ""),
                "type": "text",
                "text": {"body": message},
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                record_sent("whatsapp", to_clean, message[:30])
                return {"success": True, "provider": "Meta", "id": resp.json().get("messages", [{}])[0].get("id")}
            return {"success": False, "provider": "Meta", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as exc:
            return {"success": False, "provider": "Meta", "error": str(exc)}

    return {"success": False, "error": "No matching active WhatsApp provider found."}


# ---------------------------------------------------------------------------
# Diagnostics & Testing
# ---------------------------------------------------------------------------

def get_notification_status() -> Dict[str, Any]:
    """Summary of notification channel readiness for display in settings and diagnostics."""
    smtp_host = os.getenv("AQUASWARM_SMTP_HOST", "").strip()
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    meta_token = os.getenv("WHATSAPP_API_TOKEN", "").strip()

    channels = []
    if email_configured():
        channels.append("Email (SMTP)")
    if whatsapp_configured():
        channels.append("WhatsApp")

    return {
        "email_ready": email_configured(),
        "email_host": smtp_host or "Not configured",
        "email_from": os.getenv("AQUASWARM_SMTP_FROM") or os.getenv("AQUASWARM_SMTP_USER") or "Not configured",
        "whatsapp_ready": whatsapp_configured(),
        "whatsapp_provider": "Twilio" if twilio_sid else "Meta Cloud API" if meta_token else "Not configured",
        "active_channels": channels,
    }


def test_notification(channel: str, recipient: str, subject: str = "AquaSwarm Test Alert", body: str = "This is a test notification from AquaSwarm AI.") -> Dict[str, Any]:
    """Send an immediate test notification over the specified channel."""
    channel_clean = (channel or "").lower().strip()
    if channel_clean == "email":
        if not email_configured():
            return {
                "success": False,
                "channel": "email",
                "error": "SMTP server is not configured in environment variables (AQUASWARM_SMTP_HOST is empty).",
            }
        ok = send_email(recipient, subject, body, bypass_dedup=True)
        return {
            "success": ok,
            "channel": "email",
            "message": "Test email sent successfully." if ok else "Failed to send email. Check SMTP server logs.",
        }

    if channel_clean == "whatsapp":
        if not whatsapp_configured():
            return {
                "success": False,
                "channel": "whatsapp",
                "error": "WhatsApp provider credentials (Twilio or Meta Cloud API) are not configured.",
            }
        result = send_whatsapp(recipient, f"{subject}\n\n{body}", bypass_dedup=True)
        return {
            "success": result.get("success", False),
            "channel": "whatsapp",
            "message": "WhatsApp test message sent successfully." if result.get("success") else result.get("error", "Failed to dispatch WhatsApp message."),
        }

    return {"success": False, "channel": channel, "error": f"Unknown notification channel '{channel}'."}