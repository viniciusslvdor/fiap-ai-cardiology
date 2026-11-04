"""Alert e-mails.

Sent by SMTP when SMTP_HOST, SMTP_USER and SMTP_PASSWORD are set (optional:
SMTP_PORT, ALERT_EMAIL_FROM, ALERT_EMAIL_TO). Otherwise the message is saved
as a .eml file in results/monitoring/outbox/.
"""

from __future__ import annotations

import html
import os
import re
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

from risk import Assessment

DEFAULT_OUTBOX = Path(__file__).resolve().parents[2] / "results" / "monitoring" / "outbox"


@dataclass
class EmailConfig:
    host: str | None
    port: int
    user: str | None
    password: str | None
    sender: str
    recipient: str

    @classmethod
    def from_env(cls) -> "EmailConfig":
        user = os.getenv("SMTP_USER")
        return cls(
            host=os.getenv("SMTP_HOST"),
            port=int(os.getenv("SMTP_PORT", "587")),
            user=user,
            password=os.getenv("SMTP_PASSWORD"),
            sender=os.getenv("ALERT_EMAIL_FROM", user or "cardioia-monitor@localhost"),
            recipient=os.getenv("ALERT_EMAIL_TO", "care-team@cardioia.example"),
        )

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.host and self.user and self.password)


class EmailNotifier:
    def __init__(self, config: EmailConfig | None = None, outbox: Path = DEFAULT_OUTBOX) -> None:
        self.config = config or EmailConfig.from_env()
        self.outbox = outbox

    @property
    def mode(self) -> str:
        return "smtp" if self.config.smtp_enabled else "dry-run"

    def build(self, assessment: Assessment, reading: dict) -> EmailMessage:
        codes = ", ".join(assessment.codes)
        captured = reading.get("captured_at", "")
        msg = EmailMessage()
        msg["Subject"] = f"[CardioIA] HIGH RISK - patient {assessment.patient_id}: {codes}"
        msg["From"] = self.config.sender
        msg["To"] = self.config.recipient
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain="cardioia.local")

        lines = [f"- {f.message} [{f.level}]" for f in assessment.findings]
        temp = reading.get("temperature")
        vitals = (f"Heart rate: {reading['heart_rate']} bpm | "
                  f"Temperature: {f'{temp:.1f} °C' if temp is not None else 'n/a'} | "
                  f"{'moving' if reading.get('moving') else 'still for ' + str(reading.get('still_seconds', 0)) + ' s'}")
        text = "\n".join([
            f"CardioIA automatic alert - patient {assessment.patient_id}",
            f"Reading #{reading.get('id')} captured at {captured}",
            "",
            "Findings:",
            *lines,
            "",
            vitals,
            "",
            "Suggested action: contact the patient and check the vital signs.",
            "This is an automatic message from an academic simulation. It is not a diagnosis.",
        ])
        msg.set_content(text)

        items = "".join(f"<li><b>{html.escape(f.code)}</b>: {html.escape(f.message)} ({f.level})</li>"
                        for f in assessment.findings)
        msg.add_alternative(f"""\
<html><body style="font-family: Arial, sans-serif">
  <h2 style="color:#c62828">CardioIA - high-risk alert</h2>
  <p>Patient <b>{html.escape(assessment.patient_id)}</b>, reading #{reading.get('id')} captured at
     {html.escape(str(captured))}.</p>
  <ul>{items}</ul>
  <p>{html.escape(vitals)}</p>
  <p><b>Suggested action:</b> contact the patient and check the vital signs.</p>
  <p style="color:#777;font-size:12px">Automatic message from an academic simulation. Not a diagnosis.</p>
</body></html>""", subtype="html")
        return msg

    def send(self, assessment: Assessment, reading: dict) -> str:
        msg = self.build(assessment, reading)
        if self.config.smtp_enabled:
            with smtplib.SMTP(self.config.host, self.config.port, timeout=15) as smtp:
                smtp.starttls()
                smtp.login(self.config.user, self.config.password)
                smtp.send_message(msg)
            return f"e-mail sent to {self.config.recipient}"

        self.outbox.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        name = re.sub(r"[^A-Za-z0-9_-]", "_", f"{stamp}_{assessment.patient_id}_{'-'.join(assessment.codes)}")
        path = self.outbox / f"{name}.eml"
        path.write_bytes(bytes(msg))
        return f"dry run, saved to {path.name}"
