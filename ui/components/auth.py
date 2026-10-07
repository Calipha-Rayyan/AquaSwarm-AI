from __future__ import annotations

import hmac
import os
from typing import Any

from backend.client import BackendClient, BackendUnavailable


def _setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value not in (None, ""):
        return value
    try:  # Streamlit secrets (sectioned or non-env secrets)
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default


def authenticate(email: str, password: str) -> bool:
    """Authenticate the prototype manager session from environment settings.

    Set AQUASWARM_DEMO_EMAIL / AQUASWARM_DEMO_PASSWORD in .env or Streamlit
    secrets. The built-in demo values are only a convenience for local use.
    """
    expected_email = _setting("AQUASWARM_DEMO_EMAIL", "demo@aquaswarm.ai").strip().lower()
    expected_password = _setting("AQUASWARM_DEMO_PASSWORD", "AquaSwarm@123")

    return (
        hmac.compare_digest(email.strip().lower().encode(), expected_email.encode())
        & hmac.compare_digest(password.encode(), expected_password.encode())
    )


def using_default_credentials() -> bool:
    return not _setting("AQUASWARM_DEMO_PASSWORD")


def build_client() -> BackendClient:
    """One place that builds the backend client from settings."""
    from config.settings import (
        AQUASWARM_BACKEND_MODE,
        AQUASWARM_BACKEND_TIMEOUT,
        AQUASWARM_BACKEND_URL,
    )

    return BackendClient(
        base_url=AQUASWARM_BACKEND_URL,
        timeout=AQUASWARM_BACKEND_TIMEOUT,
        mode=AQUASWARM_BACKEND_MODE,
    )


def get_tank_options() -> list[str]:
    """Tank codes from the backend API. There is no CSV fallback: a failure
    raises with the real reason so it can be shown and fixed."""
    rows = build_client().get_tanks()
    codes = [str(row["tank_code"]) for row in rows if row.get("tank_code")]
    if not codes:
        raise BackendUnavailable("The backend returned no tanks.")
    return list(dict.fromkeys(codes))


def get_backend_status() -> dict[str, Any]:
    """Health/data check for the sidebar. Never raises."""
    try:
        return build_client().diagnose()
    except Exception as exc:  # e.g. settings import failure
        return {"ok": False, "label": "?", "mode": "?", "url": "—", "tanks": 0,
                "suppliers": 0, "error": f"{type(exc).__name__}: {exc}"}