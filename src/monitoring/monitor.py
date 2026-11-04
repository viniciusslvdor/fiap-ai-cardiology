"""Polls the API for new readings, evaluates each patient and sends an e-mail on
high risk. A new e-mail is sent when the problems change or after a 10 min
cooldown.

Run: uv run python src/monitoring/monitor.py --interval 5
"""

from __future__ import annotations

import argparse
import time
from collections import defaultdict, deque
from datetime import datetime

import requests

from client import DEFAULT_API, CardioIAClient
from notifier import EmailNotifier
from risk import Assessment, Thresholds, assess


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class Monitor:
    def __init__(self, client: CardioIAClient, notifier: EmailNotifier, limits: Thresholds = Thresholds(),
                 history_size: int = 20, cooldown_s: int = 600) -> None:
        self.client = client
        self.notifier = notifier
        self.limits = limits
        self.cooldown_s = cooldown_s
        self.last_id = 0
        self.history: dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))
        self.last_alert: dict[str, tuple[tuple[str, ...], datetime | None]] = {}

    def _should_notify(self, assessment: Assessment, captured: datetime | None) -> bool:
        key = tuple(sorted(assessment.codes))
        previous = self.last_alert.get(assessment.patient_id)
        if previous is None or previous[0] != key:
            return True
        last_time = previous[1]
        return captured is not None and last_time is not None and \
            (captured - last_time).total_seconds() >= self.cooldown_s

    def poll_once(self) -> list[dict]:
        events = []
        readings = self.client.get_vitals(after_id=self.last_id)
        readings.sort(key=lambda r: r.get("captured_at") or "")
        for reading in readings:
            self.last_id = max(self.last_id, reading["id"])
            patient = reading["patient_id"]
            history = self.history[patient]
            history.append(reading)
            assessment = assess(list(history), self.limits)

            if not assessment.is_high:
                self.last_alert.pop(patient, None)
                if assessment.level == "attention":
                    events.append({"patient": patient, "reading_id": reading["id"], "level": "attention",
                                   "codes": [f.code for f in assessment.findings], "action": "logged only"})
                continue

            captured = _parse_time(reading.get("captured_at"))
            if not self._should_notify(assessment, captured):
                continue
            result = self.notifier.send(assessment, reading)
            self.client.send_alert({
                "patient_id": patient,
                "level": assessment.level,
                "codes": assessment.codes,
                "message": "; ".join(f.message for f in assessment.findings if f.level == "high"),
                "reading_id": reading["id"],
                "notified_to": self.notifier.config.recipient,
            })
            self.last_alert[patient] = (tuple(sorted(assessment.codes)), captured)
            events.append({"patient": patient, "reading_id": reading["id"], "level": "high",
                           "codes": assessment.codes, "action": result})
        return events


def main() -> None:
    parser = argparse.ArgumentParser(description="CardioIA monitoring robot")
    parser.add_argument("--api", default=DEFAULT_API, help="API base URL")
    parser.add_argument("--interval", type=float, default=5.0, help="seconds between polls")
    parser.add_argument("--once", action="store_true", help="poll a single time and exit")
    args = parser.parse_args()

    client = CardioIAClient(args.api)
    notifier = EmailNotifier()
    monitor = Monitor(client, notifier)
    print(f"Monitoring {args.api} | e-mail mode: {notifier.mode} | Ctrl+C to stop")
    while True:
        try:
            for event in monitor.poll_once():
                print(f"[{event['level'].upper():9}] {event['patient']} reading #{event['reading_id']} "
                      f"{','.join(event['codes'])} -> {event['action']}")
        except requests.RequestException as exc:
            print(f"API unavailable ({exc.__class__.__name__}), retrying in {args.interval} s")
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
