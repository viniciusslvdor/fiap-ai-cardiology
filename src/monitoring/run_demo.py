"""Runs the API, sends the simulated patients, runs the monitor once and saves
a summary in results/monitoring/demo_summary.json.

Run: uv run python src/monitoring/run_demo.py [--api http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from collections import Counter
from pathlib import Path

import uvicorn

from api import create_app
from client import CardioIAClient
from monitor import Monitor
from notifier import DEFAULT_OUTBOX, EmailNotifier
from simulator import SCENARIOS, generate, simulate

RESULTS = Path(__file__).resolve().parents[2] / "results" / "monitoring"


def start_api(port: int) -> uvicorn.Server:
    server = uvicorn.Server(uvicorn.Config(create_app(), host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if server.started:
            return server
        time.sleep(0.05)
    raise RuntimeError("API did not start")


def main() -> None:
    parser = argparse.ArgumentParser(description="CardioIA REST + e-mail demo")
    parser.add_argument("--api", help="use an API that is already running instead of starting one")
    parser.add_argument("--port", type=int, default=8765, help="port for the embedded API")
    args = parser.parse_args()

    server = None
    base_url = args.api
    if not base_url:
        server = start_api(args.port)
        base_url = f"http://127.0.0.1:{args.port}"
    client = CardioIAClient(base_url)
    notifier = EmailNotifier()
    if notifier.mode == "dry-run":
        for old in DEFAULT_OUTBOX.glob("*.eml"):
            old.unlink()

    print(f"1) API at {base_url}: {client.health()}")

    sent = simulate(client)
    print(f"2) Sent {sum(sent.values())} readings via POST /api/vitals: {sent}")

    again = client.send_vitals(generate("P001", SCENARIOS["P001"])[0])
    print(f"3) Same reading sent again -> duplicate={again['duplicate']} (id {again['id']})")

    monitor = Monitor(client, notifier)
    events = monitor.poll_once()
    attention = Counter(e["patient"] for e in events if e["level"] == "attention")
    high = [e for e in events if e["level"] == "high"]
    print(f"4) Monitor read {monitor.last_id} readings (GET /api/vitals), e-mail mode: {notifier.mode}")
    print(f"   attention (logged, no e-mail): {dict(attention)}")
    for e in high:
        print(f"   HIGH {e['patient']} reading #{e['reading_id']}: {', '.join(e['codes'])} -> {e['action']}")

    alerts = client.get_alerts()
    print(f"5) GET /api/alerts -> {len(alerts)} alerts recorded")
    for pid in SCENARIOS:
        latest = client.get_latest(pid)
        print(f"   {pid} latest: {latest['heart_rate']} bpm, {latest['temperature']} °C, "
              f"{'moving' if latest['moving'] else 'still ' + str(latest['still_seconds']) + ' s'}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    summary = {
        "readings_sent": sent,
        "duplicate_detected": again["duplicate"],
        "email_mode": notifier.mode,
        "attention_events": dict(attention),
        "alerts": [{k: a[k] for k in ("patient_id", "codes", "message", "reading_id", "notified_to")}
                   for a in alerts],
    }
    (RESULTS / "demo_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"6) Summary saved to {(RESULTS / 'demo_summary.json').relative_to(RESULTS.parents[1])}")

    if server:
        server.should_exit = True


if __name__ == "__main__":
    main()
