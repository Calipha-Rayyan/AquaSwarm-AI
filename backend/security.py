"""API-key protection and CORS settings for the AquaSwarm FastAPI backend.

* Every route except ``/health`` requires the ``X-API-Key`` header when
  ``AQUASWARM_API_KEY`` is configured (constant-time comparison).
* When no key is configured the API only answers loopback clients, so a
  forgotten setting can never expose the database to the network.
* In-process calls (Streamlit Cloud) never cross the network and therefore
  bypass these HTTP-layer checks by design.

This module deliberately does not import crewai/config so the backend stays
light and import-safe.
"""
from __future__ import annotations

import hmac
import os
from typing import List, Optional

from fastapi import Header, HTTPException, Request, status

PUBLIC_PATHS = {"/health"}
_LOOPBACK = {"127.0.0.1", "::1", "localhost", "testclient"}


def configured_api_key() -> str:
    return os.getenv("AQUASWARM_API_KEY", "").strip()


def cors_origins() -> List[str]:
    raw = os.getenv(
        "AQUASWARM_CORS_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    )
    return [item.strip() for item in raw.split(",") if item.strip()]


def docs_enabled() -> bool:
    return os.getenv("AQUASWARM_ENABLE_DOCS", "false").strip().lower() in {
        "1", "true", "yes", "on",
    }


def require_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(default=None),
) -> None:
    if request.url.path in PUBLIC_PATHS:
        return

    expected = configured_api_key()

    if not expected:
        client_host = request.client.host if request.client else ""
        if client_host in _LOOPBACK:
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key is not configured on the server.",
        )

    supplied = (x_api_key or "").encode("utf-8")
    if not hmac.compare_digest(supplied, expected.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )