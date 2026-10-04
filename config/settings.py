from __future__ import annotations

import os

from dotenv import load_dotenv
from crewai import LLM

# Load the project .env file. Do not print or expose the API key.
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
    "GEMINI_MODEL", "gemini-3.5-flash-lite"
).strip()


def _normalize_gemini_model(model: str) -> str:
    """Return the bare Gemini model ID expected by CrewAI's Gemini adapter."""
    value = (model or "").strip()

    # Avoid accidental combinations such as gemini/models/... or gemini/gemini/...
    for prefix in ("models/", "gemini/"):
        while value.lower().startswith(prefix):
            value = value[len(prefix):]

    # 2.5 Flash is access-restricted for many new AI Studio projects. Use the
    # current low-cost Flash-Lite model instead. The same mapping also prevents
    # the user from staying on a congested 3.8 Flash endpoint during demos.
    if value.lower() in {
        "gemini-2.5-flash",
        "gemini-2.5-flash-001",
        "gemini-3.8-flash",
    }:
        return "gemini-3.5-flash-lite"

    return value or "gemini-3.5-flash-lite"


GEMINI_MODEL = _normalize_gemini_model(_RAW_GEMINI_MODEL)

AQUASWARM_BACKEND_ENABLED = os.getenv(
    "AQUASWARM_BACKEND_ENABLED", "true"
).strip().lower() in {"1", "true", "yes", "on"}

AQUASWARM_BACKEND_URL = os.getenv(
    "AQUASWARM_API_URL", "http://127.0.0.1:8000"
).rstrip("/")

AQUASWARM_DEFAULT_INFLOW = float(os.getenv("AQUASWARM_DEFAULT_INFLOW", "0"))
AQUASWARM_BACKEND_TIMEOUT = float(os.getenv("AQUASWARM_BACKEND_TIMEOUT", "2.0"))


def get_gemini_llm() -> LLM:
    """Create the Gemini LLM used by AquaSwarm agents."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add it to D:\\AquaSwarm-AI\\.env."
        )

    return LLM(
        model=f"gemini/{GEMINI_MODEL}",
        api_key=GEMINI_API_KEY,
    )


GEMINI_LLM = get_gemini_llm() if GEMINI_API_KEY else None

# Existing AquaSwarm agents import GROQ_LLM. Keep the alias so we do not have
# to edit every task import just to change the provider.
GROQ_LLM = GEMINI_LLM
