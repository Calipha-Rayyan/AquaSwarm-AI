from __future__ import annotations

import os

from dotenv import load_dotenv
from crewai import LLM

# Load local .env when running outside Streamlit Cloud.
load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Gemini configuration
# ---------------------------------------------------------------------------

GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or ""
).strip()

_RAW_GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite",
).strip()


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
# ---------------------------------------------------------------------------

AQUASWARM_BACKEND_ENABLED = (
    os.getenv("AQUASWARM_BACKEND_ENABLED", "true")
    .strip()
    .lower()
    in {"1", "true", "yes", "on"}
)

AQUASWARM_BACKEND_MODE = (
    os.getenv("AQUASWARM_BACKEND_MODE", "auto")
    .strip()
    .lower()
)

if AQUASWARM_BACKEND_MODE not in {"auto", "http", "inprocess"}:
    AQUASWARM_BACKEND_MODE = "auto"

AQUASWARM_BACKEND_URL = os.getenv(
    "AQUASWARM_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

AQUASWARM_DEFAULT_INFLOW = float(
    os.getenv("AQUASWARM_DEFAULT_INFLOW", "0")
)

AQUASWARM_BACKEND_TIMEOUT = float(
    os.getenv("AQUASWARM_BACKEND_TIMEOUT", "1.0")
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
