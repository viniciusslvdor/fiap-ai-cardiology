"""CardioIA monitoring REST API (in-memory storage).

Run: uv run python src/monitoring/api.py   (docs at http://127.0.0.1:8000/docs)
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field


class VitalsIn(BaseModel):
    patient_id: str = Field(min_length=1, max_length=32, examples=["P001"])
    device_id: str | None = Field(default=None, max_length=64)
    seq: int | None = Field(default=None, ge=0, description="device sequence number, used to drop duplicates")
    captured_at: datetime | None = None
    heart_rate: int = Field(ge=20, le=250, description="beats per minute")
    temperature: float | None = Field(default=None, ge=25, le=45, description="°C")
    humidity: float | None = Field(default=None, ge=0, le=100)
    moving: bool = True
    still_seconds: int = Field(default=0, ge=0)
    fall: bool = False
    source: str = "simulator"


class Vitals(VitalsIn):
    id: int
    received_at: datetime


class AlertIn(BaseModel):
    patient_id: str
    level: str
    codes: list[str]
    message: str
    reading_id: int | None = None
    notified_to: str | None = None


class Alert(AlertIn):
    id: int
    created_at: datetime


class Store:
    """Thread-safe in-memory storage."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.vitals: list[Vitals] = []
        self.alerts: list[Alert] = []
        self._seen: set[tuple[str, int]] = set()

    def add_vitals(self, data: VitalsIn) -> tuple[Vitals, bool]:
        now = datetime.now(timezone.utc)
        with self._lock:
            if data.device_id and data.seq is not None:
                key = (data.device_id, data.seq)
                if key in self._seen:
                    existing = next(v for v in self.vitals if (v.device_id, v.seq) == key)
                    return existing, False
                self._seen.add(key)
            item = Vitals(**data.model_dump(), id=len(self.vitals) + 1, received_at=now)
            if item.captured_at is None:
                item.captured_at = now
            self.vitals.append(item)
            return item, True

    def add_alert(self, data: AlertIn) -> Alert:
        with self._lock:
            item = Alert(**data.model_dump(), id=len(self.alerts) + 1, created_at=datetime.now(timezone.utc))
            self.alerts.append(item)
            return item


def create_app() -> FastAPI:
    app = FastAPI(title="CardioIA Monitoring API", version="0.3.0",
                  description="Receives vital signs from the CardioIA wearable (simulated).")
    store = Store()
    app.state.store = store

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok", "readings": len(store.vitals), "alerts": len(store.alerts)}

    @app.post("/api/vitals", status_code=status.HTTP_201_CREATED)
    def create_vitals(data: VitalsIn) -> dict:
        item, created = store.add_vitals(data)
        return {"id": item.id, "duplicate": not created}

    @app.get("/api/vitals")
    def list_vitals(after_id: int = Query(0, ge=0), patient_id: str | None = None,
                    limit: int = Query(500, ge=1, le=5000)) -> list[Vitals]:
        items = [v for v in store.vitals if v.id > after_id and (patient_id is None or v.patient_id == patient_id)]
        return items[:limit]

    @app.get("/api/patients")
    def list_patients() -> list[dict]:
        latest: dict[str, Vitals] = {}
        for v in store.vitals:
            latest[v.patient_id] = v
        return [{"patient_id": pid, "latest": v} for pid, v in sorted(latest.items())]

    @app.get("/api/patients/{patient_id}/latest")
    def latest(patient_id: str) -> Vitals:
        for v in reversed(store.vitals):
            if v.patient_id == patient_id:
                return v
        raise HTTPException(status_code=404, detail=f"No readings for patient {patient_id}")

    @app.post("/api/alerts", status_code=status.HTTP_201_CREATED)
    def create_alert(data: AlertIn) -> Alert:
        return store.add_alert(data)

    @app.get("/api/alerts")
    def list_alerts(patient_id: str | None = None) -> list[Alert]:
        return [a for a in store.alerts if patient_id is None or a.patient_id == patient_id]

    return app


app = create_app()

if __name__ == "__main__":
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Runs the CardioIA monitoring API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
