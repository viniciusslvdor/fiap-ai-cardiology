"""REST client for the CardioIA monitoring API."""

from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_API = "http://127.0.0.1:8000"


class CardioIAClient:
    def __init__(self, base_url: str = DEFAULT_API, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=(502, 503, 504),
                      allowed_methods=frozenset({"GET", "POST"}))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers.update({"Accept": "application/json"})

    def _request(self, method: str, path: str, **kwargs) -> Any:
        response = self.session.request(method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def send_vitals(self, reading: dict) -> dict:
        return self._request("POST", "/api/vitals", json=reading)

    def send_alert(self, alert: dict) -> dict:
        return self._request("POST", "/api/alerts", json=alert)

    def health(self) -> dict:
        return self._request("GET", "/api/health")

    def get_vitals(self, after_id: int = 0, patient_id: str | None = None, limit: int = 500) -> list[dict]:
        params: dict[str, Any] = {"after_id": after_id, "limit": limit}
        if patient_id:
            params["patient_id"] = patient_id
        return self._request("GET", "/api/vitals", params=params)

    def get_patients(self) -> list[dict]:
        return self._request("GET", "/api/patients")

    def get_latest(self, patient_id: str) -> dict:
        return self._request("GET", f"/api/patients/{patient_id}/latest")

    def get_alerts(self, patient_id: str | None = None) -> list[dict]:
        params = {"patient_id": patient_id} if patient_id else None
        return self._request("GET", "/api/alerts", params=params)
