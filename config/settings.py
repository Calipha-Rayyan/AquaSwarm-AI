from __future__ import annotations

import os

from dotenv import load_dotenv
from crewai import LLM

# Load local .env when running outside Streamlit Cloud.
load_dotenv(override=True)


def get_secret(name: str, default: str = "") -> str:
    """Read a setting from the environment, then from Streamlit secrets.

    Streamlit Community Cloud exposes top-level secrets as environment
    variables, but nested/sectioned secrets are only visible via st.secrets.
    """
    value = os.getenv(name)
    if value not in (None, ""):
        return str(value).strip()

    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass

    return default


def _float(name: str, default: float) -> float:
    try:
        return float(get_secret(name, str(default)))
    except ValueError:
        return default


def _flag(name: str, default: bool) -> bool:
    raw = get_secret(name, "true" if default else "false").lower()
    return raw in {"1", "true", "yes", "on"}


# ---------------------------------------------------------------------------
# Gemini configuration (LLM used by the CrewAI agents only)
# ---------------------------------------------------------------------------

GEMINI_API_KEY = (
    get_secret("GEMINI_API_KEY") or get_secret("GOOGLE_API_KEY")
)

_RAW_GEMINI_MODEL = get_secret("GEMINI_MODEL", "gemini-3.5-flash-lite")


def _normalize_gemini_model(model: str) -> str:
    value = (model or "").strip()

    for prefix in ("models/", "gemini/"):
        while value.lower().startswith(prefix):
            value = value[len(prefix):]

    if value.lower() in {
        "gemini-2.5-flash",
        "gemini-2.5-flash-001",
        "gemini-3.8-flash",
    }:
        return "gemini-3.5-flash-lite"

    return value or "gemini-3.5-flash-lite"


GEMINI_MODEL = _normalize_gemini_model(_RAW_GEMINI_MODEL)

# ---------------------------------------------------------------------------
# Backend integration
#
# The backend (FastAPI + SQLite) is the single source of truth for tanks,
# consumption and suppliers. There is no CSV fallback in the pipeline: if the
# backend cannot be reached, the operation stops with the real error.
# ---------------------------------------------------------------------------

AQUASWARM_BACKEND_ENABLED = _flag("AQUASWARM_BACKEND_ENABLED", True)

AQUASWARM_BACKEND_URL = get_secret("AQUASWARM_API_URL").rstrip("/")

_mode = get_secret("AQUASWARM_BACKEND_MODE").strip().strip('"').strip("'").lower()
if _mode not in {"auto", "http", "inprocess"}:
    # Streamlit Cloud runs only the Streamlit app, so default to in-process
    # unless a real API URL was configured.
    _mode = "auto" if AQUASWARM_BACKEND_URL else "inprocess"
AQUASWARM_BACKEND_MODE = _mode

if not AQUASWARM_BACKEND_URL:
    AQUASWARM_BACKEND_URL = "http://127.0.0.1:8000"

# Shared secret sent as the X-API-Key header on every HTTP call.
AQUASWARM_API_KEY = get_secret("AQUASWARM_API_KEY")

AQUASWARM_BACKEND_TIMEOUT = max(0.5, _float("AQUASWARM_BACKEND_TIMEOUT", 5.0))

AQUASWARM_DEFAULT_INFLOW = max(0.0, _float("AQUASWARM_DEFAULT_INFLOW", 0.0))

# ---------------------------------------------------------------------------
# Water operating policy (see tools/water_tools.py)
# ---------------------------------------------------------------------------

AQUASWARM_RESERVE_DAYS = max(0.5, _float("AQUASWARM_RESERVE_DAYS", 7.0))
AQUASWARM_MIN_OPERATING_FILL_PCT = min(
    max(_float("AQUASWARM_MIN_OPERATING_FILL_PCT", 40.0), 0.0), 90.0
)
AQUASWARM_MAX_FILL_PCT = min(
    max(_float("AQUASWARM_MAX_FILL_PCT", 95.0), 50.0), 100.0
)


def get_gemini_llm() -> LLM:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to .env or Streamlit Secrets."
        )

    return LLM(
        model=f"gemini/{GEMINI_MODEL}",
        api_key=GEMINI_API_KEY,
    )


GEMINI_LLM = get_gemini_llm() if GEMINI_API_KEY else None

# Existing agents import GROQ_LLM for compatibility.
GROQ_LLM = GEMINI_LLM