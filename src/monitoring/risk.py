"""Risk rules for vital signs.

Levels: normal < attention < high. Most conditions must repeat in consecutive
readings to reach "high"; extreme values and falls are immediate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

LEVELS = ("normal", "attention", "high")


@dataclass(frozen=True)
class Thresholds:
    """Same limits used on the ESP32 and in Node-RED."""

    hr_high: int = 120           # tachycardia
    hr_attention: int = 100      # elevated heart rate
    hr_low: int = 50             # bradycardia
    hr_extreme_high: int = 150   # alert on the first reading
    hr_extreme_low: int = 40
    temp_high: float = 38.0      # fever
    temp_attention: float = 37.5 # low-grade fever
    temp_low: float = 35.0       # hypothermia
    temp_extreme: float = 39.5
    still_attention_s: int = 30 * 60   # 30 min without moving
    confirm_readings: int = 2          # consecutive readings needed for "high"


@dataclass(frozen=True)
class Finding:
    code: str      # e.g. TACHYCARDIA
    level: str     # "attention" or "high"
    message: str


@dataclass
class Assessment:
    patient_id: str
    level: str = "normal"
    findings: list[Finding] = field(default_factory=list)

    @property
    def is_high(self) -> bool:
        return self.level == "high"

    @property
    def codes(self) -> list[str]:
        return [f.code for f in self.findings if f.level == "high"]

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)
        if LEVELS.index(finding.level) > LEVELS.index(self.level):
            self.level = finding.level


def _last_n(history: Sequence[dict], n: int) -> Sequence[dict]:
    return history[-n:] if len(history) >= n else []


def _sustained(history: Sequence[dict], n: int, condition) -> bool:
    """True when the condition holds in each of the last n readings."""
    window = _last_n(history, n)
    return bool(window) and all(condition(r) for r in window)


def assess(history: Sequence[dict], limits: Thresholds = Thresholds()) -> Assessment:
    """Evaluates a patient's readings (oldest first)."""
    if not history:
        raise ValueError("history must have at least one reading")
    last = history[-1]
    result = Assessment(patient_id=last.get("patient_id", "?"))
    hr = last["heart_rate"]
    temp = last.get("temperature")
    n = limits.confirm_readings

    # Heart rate
    if hr > limits.hr_high:
        sustained = _sustained(history, n, lambda r: r["heart_rate"] > limits.hr_high)
        level = "high" if sustained or hr >= limits.hr_extreme_high else "attention"
        result.add(Finding("TACHYCARDIA", level, f"Heart rate {hr} bpm (limit {limits.hr_high} bpm)"))
    elif hr < limits.hr_low:
        sustained = _sustained(history, n, lambda r: r["heart_rate"] < limits.hr_low)
        level = "high" if sustained or hr <= limits.hr_extreme_low else "attention"
        result.add(Finding("BRADYCARDIA", level, f"Heart rate {hr} bpm (limit {limits.hr_low} bpm)"))
    elif hr > limits.hr_attention:
        result.add(Finding("ELEVATED_HR", "attention", f"Heart rate {hr} bpm"))

    # Temperature
    if temp is not None:
        if temp >= limits.temp_high:
            sustained = _sustained(history, n, lambda r: (r.get("temperature") or 0) >= limits.temp_high)
            level = "high" if sustained or temp >= limits.temp_extreme else "attention"
            result.add(Finding("FEVER", level, f"Temperature {temp:.1f} °C (limit {limits.temp_high} °C)"))
        elif temp < limits.temp_low:
            sustained = _sustained(history, n, lambda r: (r.get("temperature") or 99) < limits.temp_low)
            result.add(Finding("HYPOTHERMIA", "high" if sustained else "attention",
                               f"Temperature {temp:.1f} °C (limit {limits.temp_low} °C)"))
        elif temp >= limits.temp_attention:
            result.add(Finding("LOW_GRADE_FEVER", "attention", f"Temperature {temp:.1f} °C"))

    # Lying still is only high risk together with an abnormal heart rate
    still = last.get("still_seconds") or 0
    if not last.get("moving", True) and still >= limits.still_attention_s:
        hr_abnormal = hr > limits.hr_high or hr < limits.hr_low
        minutes = still // 60
        if hr_abnormal:
            result.add(Finding("NO_MOVEMENT", "high",
                               f"No movement for {minutes} min with abnormal heart rate ({hr} bpm)"))
        else:
            result.add(Finding("NO_MOVEMENT", "attention", f"No movement for {minutes} min"))

    if last.get("fall"):
        result.add(Finding("FALL", "high", "Possible fall detected by the accelerometer"))

    return result
