import os
from typing import Any, Optional

import requests


def _default_timeout() -> float:
    try:
        return max(0.5, float(os.getenv("AQUASWARM_BACKEND_TIMEOUT", "2.0")))
    except ValueError:
        return 2.0


class BackendClient:
    """HTTP client for the AquaSwarm FastAPI backend."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (
            base_url
            or os.getenv(
                "AQUASWARM_API_URL",
                "http://127.0.0.1:8000",
            )
        ).rstrip("/")

        self.timeout = _default_timeout() if timeout is None else max(0.5, float(timeout))

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ):
        url = f"{self.base_url}{endpoint}"

        kwargs.setdefault(
            "timeout",
            self.timeout,
        )

        response = requests.request(
            method,
            url,
            **kwargs,
        )

        response.raise_for_status()

        if not response.content:
            return {}

        return response.json()

    def get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ):
        return self._request(
            "GET",
            endpoint,
            params=params,
        )

    def post(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ):
        return self._request(
            "POST",
            endpoint,
            json=payload,
        )

    def patch(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ):
        return self._request(
            "PATCH",
            endpoint,
            json=payload,
        )

    def health(self):
        return self.get("/health")

    def get_sites(self):
        return self.get("/sites")

    def get_tanks(
        self,
        site_id: Optional[int] = None,
    ):
        params = {}

        if site_id is not None:
            params["site_id"] = site_id

        return self.get(
            "/tanks",
            params=params or None,
        )

    def get_consumption(
        self,
        site_id: Optional[int] = None,
        tank_code: Optional[str] = None,
        limit: int = 100,
    ):
        params = {
            "limit": limit,
        }

        if site_id is not None:
            params["site_id"] = site_id

        if tank_code:
            params["tank_code"] = tank_code

        return self.get(
            "/consumption",
            params=params,
        )

    def get_suppliers(
        self,
        available_only: bool = False,
    ):
        return self.get(
            "/suppliers",
            params={
                "available_only": available_only,
            },
        )

    def get_alerts(
        self,
        status: Optional[str] = None,
    ):
        params = {}

        if status:
            params["status"] = status

        return self.get(
            "/alerts",
            params=params or None,
        )

    def create_alert(self, payload):
        return self.post(
            "/alerts",
            payload,
        )

    def get_events(
        self,
        limit: int = 100,
    ):
        return self.get(
            "/events",
            params={"limit": limit},
        )

    def create_delivery_request(
        self,
        payload,
    ):
        return self.post(
            "/delivery-requests",
            payload,
        )

    def get_delivery_requests(self):
        return self.get(
            "/delivery-requests",
        )

    def create_approval(self, payload):
        return self.post(
            "/approvals",
            payload,
        )

    def get_approvals(self):
        return self.get(
            "/approvals",
        )

    def update_delivery_status(
        self,
        request_id: int,
        payload,
    ):
        return self.patch(
            f"/delivery-requests/{request_id}/status",
            payload,
        )

    def create_verification(self, payload):
        return self.post(
            "/verifications",
            payload,
        )

    def get_verifications(self):
        return self.get(
            "/verifications",
        )

    def get_agent_runs(
        self,
        limit: int = 200,
    ):
        return self.get(
            "/agent-runs",
            params={"limit": limit},
        )

    def create_agent_run(self, payload):
        return self.post(
            "/agent-runs",
            payload,
        )
