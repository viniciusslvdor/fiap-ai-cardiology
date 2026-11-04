"""Sends simulated patients to the API (one reading per minute, fixed seed).

Run: uv run python src/monitoring/simulator.py
"""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone

from client import DEFAULT_API, CardioIAClient

SCENARIOS = {
    "P001": "normal",  # includes one isolated 126 bpm reading
    "P002": "tachycardia",
    "P003": "fever",
    "P004": "collapse",
    "P005": "fall",
}


def generate(patient_id: str, scenario: str, n: int = 40, interval_s: int = 60,
             end: datetime | None = None, seed: int = 42) -> list[dict]:
    rng = random.Random(f"{seed}-{patient_id}")
    end = end or datetime.now(timezone.utc)
    start = end - timedelta(seconds=interval_s * (n - 1))
    readings = []
    still_since: int | None = None

    for i in range(n):
        hr = rng.randint(66, 84)
        temp = round(rng.uniform(36.3, 36.9), 1)
        moving = rng.random() < 0.6
        fall = False

        if scenario == "normal" and i == 20:
            hr = 126
        elif scenario == "tachycardia" and i >= 15:
            hr = min(100 + (i - 15) * 3 + rng.randint(-2, 2), 158)
        elif scenario == "fever" and i >= 10:
            temp = round(min(36.8 + (i - 10) * 0.1, 38.8) + rng.uniform(-0.05, 0.05), 1)
            hr = rng.randint(88, 104)
        elif scenario == "collapse" and i >= 5:
            moving = False
            if i >= 30:
                hr = max(58 - (i - 30) * 2, 41)
        elif scenario == "fall" and i >= 25:
            fall = i == 25
            moving = i == 25
            hr = rng.randint(90, 110) if i < 28 else hr

        if moving:
            still_since = None
        elif still_since is None:
            still_since = i
        still_seconds = 0 if still_since is None else (i - still_since + 1) * interval_s

        readings.append({
            "patient_id": patient_id,
            "device_id": f"sim-{patient_id}",
            "seq": i + 1,
            "captured_at": (start + timedelta(seconds=interval_s * i)).isoformat(),
            "heart_rate": hr,
            "temperature": temp,
            "humidity": round(rng.uniform(45, 60), 1),
            "moving": moving,
            "still_seconds": still_seconds,
            "fall": fall,
            "source": f"simulator:{scenario}",
        })
    return readings


def simulate(client: CardioIAClient, n: int = 40) -> dict[str, int]:
    batches = {pid: generate(pid, scenario, n=n) for pid, scenario in SCENARIOS.items()}
    sent = {pid: 0 for pid in SCENARIOS}
    for i in range(n):
        for pid, readings in batches.items():
            client.send_vitals(readings[i])
            sent[pid] += 1
    return sent


def main() -> None:
    parser = argparse.ArgumentParser(description="Sends simulated vital signs to the CardioIA API")
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("-n", type=int, default=40, help="readings per patient")
    args = parser.parse_args()
    sent = simulate(CardioIAClient(args.api), n=args.n)
    for pid, count in sent.items():
        print(f"{pid} ({SCENARIOS[pid]}): {count} readings sent")


if __name__ == "__main__":
    main()
