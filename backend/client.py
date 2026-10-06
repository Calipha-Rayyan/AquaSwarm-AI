from __future__ import annotations

import os
import re
from typing import Any, Optional

import requests


def _default_timeout() -> float:
    try:
        return max(0.5, float(os.getenv("AQUASWARM_BACKEND_TIMEOUT", "1.0")))
    except ValueError:
        return 1.0


class BackendClient:
    """
    AquaSwarm backend client.

    Modes:
      - http: use the FastAPI server over HTTP.
      - inprocess: call the same FastAPI endpoint functions in-process.
      - auto: try HTTP first; if the server is unavailable, switch to in-process.

    The in-process mode is important for Streamlit Community Cloud because
    Streamlit Cloud runs the Streamlit app, not a separate Uvicorn service.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        mode: Optional[str] = None,
    ):
        self.base_url = (
            base_url
            or os.getenv(
                "AQUASWARM_API_URL",
                "http://127.0.0.1:8000",
            )
        ).rstrip("/")

        requested_mode = (
            mode
            or os.getenv("AQUASWARM_BACKEND_MODE", "auto")
        ).strip().lower()

        if requested_mode not in {"auto", "http", "inprocess"}:
            requested_mode = "auto"

        self.mode = requested_mode
        self.timeout = (
            _default_timeout()
            if timeout is None
            else max(0.5, float(timeout))
        )

        self._http_failed = False
        self.mode_label = (
            "BACKEND API (IN-PROCESS)"
            if self.mode == "inprocess"
            else "BACKEND API (HTTP)"
            if self.mode == "http"
            else "BACKEND API (AUTO)"
        )

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _request_http(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ):
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)

        response = requests.request(
            method,
            url,
            **kwargs,
        )
        response.raise_for_status()

        if not response.content:
            return {}

        return response.json()

    # ------------------------------------------------------------------
    # In-process FastAPI integration
    # ------------------------------------------------------------------

    @staticmethod
    def _request_inprocess(
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
        payload: Optional[dict[str, Any]] = None,
    ):
        """
        Execute the existing FastAPI endpoint handlers directly.

        This does not duplicate backend logic. It uses the same endpoint
        functions and database layer already implemented in backend/api.py.
        """
        from backend import api

        params = params or {}
        payload = payload or {}

        if method == "GET":
            if endpoint == "/health":
                return api.health()

            if endpoint == "/sites":
                return api.get_sites()

            if endpoint == "/tanks":
                return api.get_tanks(
                    site_id=params.get("site_id")
                )

            if endpoint == "/consumption":
                return api.get_consumption(
                    site_id=params.get("site_id"),
                    tank_code=params.get("tank_code"),
                    limit=params.get("limit", 100),
                )

            if endpoint == "/suppliers":
                return api.get_suppliers(
                    available_only=params.get("available_only", False)
                )

            if endpoint == "/alerts":
                return api.get_alerts(
                    status=params.get("status")
                )

            if endpoint == "/events":
                return api.get_events(
                    limit=params.get("limit", 100)
                )

            if endpoint == "/delivery-requests":
                return api.get_delivery_requests()

            if endpoint == "/approvals":
                return api.get_approvals()

            if endpoint == "/verifications":
                return api.get_verifications()

            if endpoint == "/agent-runs":
                return api.get_agent_runs(
                    limit=params.get("limit", 200)
                )

        if method == "POST":
            if endpoint == "/alerts":
                model = api.AlertIn(**payload)
                return api.create_alert(model)

            if endpoint == "/delivery-requests":
                model = api.DeliveryRequestIn(**payload)
                return api.create_delivery_request(model)

            if endpoint == "/approvals":
                model = api.ApprovalIn(**payload)
                return api.create_approval(model)

            if endpoint == "/verifications":
                model = api.VerificationIn(**payload)
                return api.create_verification(model)

            if endpoint == "/agent-runs":
                model = api.AgentRunIn(**payload)
                return api.create_agent_run(model)

        if method == "PATCH":
            match = re.fullmatch(
                r"/delivery-requests/(\d+)/status",
                endpoint,
            )
            if match:
                model = api.DeliveryStatusIn(**payload)
                return api.update_delivery_status(
                    int(match.group(1)),
                    model,
                )

        raise ValueError(
            f"Unsupported in-process backend operation: "
            f"{method} {endpoint}"
        )

    # ------------------------------------------------------------------
    # Unified request method
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
        payload: Optional[dict[str, Any]] = None,
    ):
        method = method.upper()

        if self.mode == "inprocess" or self._http_failed:
            result = self._request_inprocess(
                method,
                endpoint,
                params=params,
                payload=payload,
            )
            self.mode_label = "BACKEND API (IN-PROCESS)"
            return result

        try:
            kwargs: dict[str, Any] = {}
            if params is not None:
                kwargs["params"] = params
            if payload is not None:
                kwargs["json"] = payload

            result = self._request_http(
                method,
                endpoint,
                **kwargs,
            )

            self.mode_label = "BACKEND API (HTTP)"
            return result

        except (requests.ConnectionError, requests.Timeout):
            if self.mode == "http":
                raise

            self._http_failed = True
            self.mode_label = "BACKEND API (IN-PROCESS)"

            return self._request_inprocess(
                method,
                endpoint,
                params=params,
                payload=payload,
            )

        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None

            # A server-side 5xx means the external API itself failed.
            # In auto mode, recover through the same FastAPI handlers
            # in-process. Client validation errors (4xx) are not hidden.
            if (
                self.mode == "auto"
                and status is not None
                and status >= 500
            ):
                self._http_failed = True
                self.mode_label = "BACKEND API (IN-PROCESS)"
                return self._request_inprocess(
                    method,
                    endpoint,
                    params=params,
                    payload=payload,
                )

            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
            payload=payload,
        )

    def patch(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ):
        return self._request(
            "PATCH",
            endpoint,
            payload=payload,
        )

    def health(self):
        return self.get("/health")

    def get_sites(self):
        return self.get("/sites")

    def get_tanks(self, site_id: Optional[int] = None):
        params = {}
        if site_id is not None:
            params["site_id"] = site_id
        return self.get("/tanks", params=params or None)

    def get_consumption(
        self,
        site_id: Optional[int] = None,
        tank_code: Optional[str] = None,
        limit: int = 100,
    ):
        params: dict[str, Any] = {"limit": limit}

        if site_id is not None:
            params["site_id"] = site_id

        if tank_code:
            params["tank_code"] = tank_code

        return self.get("/consumption", params=params)

    def get_suppliers(self, available_only: bool = False):
        return self.get(
            "/suppliers",
            params={"available_only": available_only},
        )

    def get_alerts(self, status: Optional[str] = None):
        params = {}
        if status:
            params["status"] = status
        return self.get("/alerts", params=params or None)

    def create_alert(self, payload):
        return self.post("/alerts", payload)

    def get_events(self, limit: int = 100):
        return self.get("/events", params={"limit": limit})

    def create_delivery_request(self, payload):
        return self.post("/delivery-requests", payload)

    def get_delivery_requests(self):
        return self.get("/delivery-requests")

    def create_approval(self, payload):
        return self.post("/approvals", payload)

    def get_approvals(self):
        return self.get("/approvals")

    def update_delivery_status(self, request_id: int, payload):
        return self.patch(
            f"/delivery-requests/{request_id}/status",
            payload,
        )

    def create_verification(self, payload):
        return self.post("/verifications", payload)

    def get_verifications(self):
        return self.get("/verifications")

    def get_agent_runs(self, limit: int = 200):
        return self.get("/agent-runs", params={"limit": limit})

    def create_agent_run(self, payload):
        return self.post("/agent-runs", payload)
