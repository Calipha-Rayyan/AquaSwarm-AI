from __future__ import annotations

from backend.client import BackendClient, BackendUnavailable


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
    """Tank codes from the backend. An empty list means nothing is set up yet."""
    rows = build_client().get_tanks()
    return list(dict.fromkeys(str(r["tank_code"]) for r in rows if r.get("tank_code")))


__all__ = ["build_client", "get_tank_options", "BackendUnavailable"]