from __future__ import annotations

import os
import re
from typing import Any, Optional
from urllib.parse import urlparse

import requests

_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


class BackendError(RuntimeError):
    """Base class for backend failures. The message is safe to show in the UI."""


class BackendUnavailable(BackendError):
    """The backend could not be reached or initialised."""


class BackendAuthError(BackendError):
    """The backend rejected the API key."""


def _default_timeout() -> float:
    try:
        return max(0.5, float(os.getenv("AQUASWARM_BACKEND_TIMEOUT", "5.0")))
    except ValueError:
        return 5.0


def _api_key() -> str:
    key = os.getenv("AQUASWARM_API_KEY", "").strip()
    if key:
        return key
    try:  # Streamlit secrets (sectioned/non-env secrets)
        import streamlit as st

        if "AQUASWARM_API_KEY" in st.secrets:
            return str(st.secrets["AQUASWARM_API_KEY"]).strip()
    except Exception:
        pass
    return ""


def _load_inprocess_api():
    """Import the FastAPI module and surface the real failure reason."""
    try:
        from backend import api

        return api
    except Exception as exc:  # database seeding, missing package, locked file...
        raise BackendUnavailable(
            f"In-process backend failed to initialise: {type(exc).__name__}: {exc}"
        ) from exc


class BackendClient:
    """
    AquaSwarm backend client.

    Modes:
      - http: call the FastAPI server over HTTP with the X-API-Key header.
      - inprocess: call the same endpoint functions directly (no network).
      - auto: try HTTP first and use in-process only if the server cannot be
        reached (connection error/timeout). HTTP 4xx/5xx errors are never
        hidden.

    There is no CSV fallback. Failures raise BackendError subclasses with the
    real reason so the operation can stop and show it.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        mode: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = (
            base_url
            or os.getenv("AQUASWARM_API_URL", "http://127.0.0.1:8000")
        ).rstrip("/")

        requested_mode = (
            mode
            or os.getenv("AQUASWARM_BACKEND_MODE", "")
            or ("auto" if os.getenv("AQUASWARM_API_URL") else "inprocess")
        ).strip().strip('"').strip("'").lower()

        if requested_mode not in {"auto", "http", "inprocess"}:
            requested_mode = "inprocess"

        self.mode = requested_mode
        self.timeout = (
            _default_timeout()
            if timeout is None
            else max(0.5, float(timeout))
        )
        self.api_key = api_key if api_key is not None else _api_key()

        self._http_failed = False
        self._session = requests.Session()
        self.mode_label = (
            "IN-PROCESS" if self.mode == "inprocess"
            else "HTTP" if self.mode == "http"
            else "AUTO"
        )

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _check_transport(self) -> None:
        """Never send the API key over plain HTTP to a remote host."""
        parsed = urlparse(self.base_url)
        host = (parsed.hostname or "").lower()
        if (
            self.api_key
            and parsed.scheme != "https"
            and host not in _LOCAL_HOSTS
            and os.getenv("AQUASWARM_ALLOW_INSECURE_HTTP", "").lower()
            not in {"1", "true", "yes"}
        ):
            raise BackendError(
                "Refusing to send the API key over unencrypted HTTP to "
                f"{host}. Use an https:// AQUASWARM_API_URL."
            )

    def _request_http(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ):
        self._check_transport()
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)

        headers = dict(kwargs.pop("headers", None) or {})
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        response = self._session.request(
            method,
            url,
            headers=headers,
            **kwargs,
        )

        if response.status_code in (401, 403):
            raise BackendAuthError(
                "The backend rejected the API key (HTTP "
                f"{response.status_code}). Check AQUASWARM_API_KEY."
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
        api = _load_inprocess_api()

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
                method, endpoint, params=params, payload=payload
            )
            self.mode_label = "IN-PROCESS"
            return result

        kwargs: dict[str, Any] = {}
        if params is not None:
            kwargs["params"] = params
        if payload is not None:
            kwargs["json"] = payload

        try:
            result = self._request_http(method, endpoint, **kwargs)
            self.mode_label = "HTTP"
            return result

        except (requests.ConnectionError, requests.Timeout) as exc:
            if self.mode == "http":
                raise BackendUnavailable(
                    f"Cannot reach the backend at {self.base_url}: {exc}"
                ) from exc

            # auto mode: the server is not running, use the in-process API.
            self._http_failed = True
            self.mode_label = "IN-PROCESS"
            return self._request_inprocess(
                method, endpoint, params=params, payload=payload
            )

        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "?"
            detail = ""
            try:
                detail = exc.response.json().get("detail", "")
            except Exception:
                pass
            raise BackendError(
                f"Backend returned HTTP {status} for {method} {endpoint}"
                + (f": {detail}" if detail else "")
            ) from exc

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

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def diagnose(self) -> dict[str, Any]:
        """Health + data check used by the UI. Never raises."""
        info: dict[str, Any] = {
            "ok": False,
            "mode": self.mode,
            "label": self.mode_label,
            "url": self.base_url if self.mode != "inprocess" else "—",
            "tanks": 0,
            "suppliers": 0,
            "error": "",
        }
        try:
            self.health()
            info["tanks"] = len(self.get_tanks())
            info["suppliers"] = len(self.get_suppliers())
            info["label"] = self.mode_label
            info["ok"] = info["tanks"] > 0
            if not info["ok"]:
                info["error"] = "Backend is reachable but contains no tanks."
        except Exception as exc:
            info["label"] = self.mode_label
            info["error"] = f"{type(exc).__name__}: {exc}"
        return info