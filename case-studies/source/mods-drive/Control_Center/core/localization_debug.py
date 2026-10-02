"""Diagnostics for runtime localization registration and UI evidence."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class LocalizationDiagnostic:
    status: str
    build_id: str | None
    expected_keys: tuple[str, ...]
    observed_keys: tuple[str, ...]
    missing_keys: tuple[str, ...]
    log_sha256: str
    ui_consumption_verified: bool
    issues: tuple[str, ...]
    last_marker: str = ""
    boundary: str = "unknown"
    panic_observed: bool = False
    next_safe_action: str = "Review the probe log and keep the module research-only."


class LocalizationDebugger:
    """Parse structured probe output without claiming catalog UI success."""

    @staticmethod
    def validate_report(report: object) -> tuple[str, ...]:
        """Validate persisted boundary evidence without promoting capability."""
        if not isinstance(report, dict):
            return ("boundary report must be an object",)
        required = {
            "schema", "status", "boundary", "last_marker", "panic_observed",
            "registration", "missing_keys", "issues", "next_safe_action", "log_sha256",
        }
        issues = [f"missing field: {key}" for key in sorted(required - set(report))]
        if report.get("schema") != "control_center.localization_boundary_report.v1":
            issues.append("unsupported boundary report schema")
        for key in ("panic_observed", "registration"):
            if key in report and not isinstance(report[key], bool):
                issues.append(f"{key} must be boolean")
        for key in ("missing_keys", "issues"):
            if key in report and not isinstance(report[key], list):
                issues.append(f"{key} must be an array")
        return tuple(issues)

    def inspect(self, log_path: Path, expected_keys: Iterable[str] = (), from_byte: int = 0) -> LocalizationDiagnostic:
        log_path = Path(log_path)
        full_raw = log_path.read_bytes()
        raw = full_raw[max(0, int(from_byte)):]
        expected = tuple(sorted({str(key) for key in expected_keys if str(key)}))
        observed: set[str] = set()
        build_id: str | None = None
        registration_ok = False
        markers: list[str] = []
        panic_observed = False
        issues: list[str] = []
        for line in raw.decode("utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            fields = event.get("fields", {}) if isinstance(event, dict) else {}
            message = str(fields.get("message", ""))
            if "panic in a function that cannot unwind" in message.lower() or "fatal error" in message.lower():
                panic_observed = True
            if message.startswith("[CC-LOCALIZATION] "):
                marker = message[len("[CC-LOCALIZATION] "):].split("|", 1)[0]
                if marker:
                    markers.append(marker)
            if message == "Type registry loaded successfully":
                version = str(fields.get("version", ""))
                build_id = version.split("|", 1)[0] or build_id
            if "[CC-LOCALIZATION] REGISTER|" in message:
                registration_ok = "ok=true" in message.lower()
            if "[CC-LOCALIZATION] KEY|" in message:
                key = message.split("KEY|", 1)[1].split("|", 1)[0].strip()
                if key:
                    observed.add(key)
        missing = tuple(sorted(set(expected) - observed))
        if not registration_ok:
            issues.append("No successful localization registration marker was observed.")
        if missing:
            issues.append("Expected localization keys were not observed: " + ", ".join(missing))
        if panic_observed:
            issues.append("A loader/game panic was observed; do not repeat the mutating probe without isolation.")
        last_marker = markers[-1] if markers else ""
        boundary = last_marker.lower() if last_marker else "no_marker"
        next_safe_action = "Review the probe log and keep the module research-only."
        if panic_observed:
            next_safe_action = "Do not repeat the mutating probe; use tag-only mode and inspect the last successful marker first."
        elif last_marker == "TAG" and not registration_ok:
            next_safe_action = "Validate the tag-only path before testing collection registration."
        elif last_marker == "TAG" and not any(marker == "REGISTER" for marker in markers):
            next_safe_action = "Collection registration was not reached; keep the probe tag-only until the boundary is isolated."
        status = "runtime_registration_verified" if registration_ok and not missing else "review_required"
        return LocalizationDiagnostic(status, build_id, expected, tuple(sorted(observed)), missing,
                                      hashlib.sha256(raw).hexdigest(), False, tuple(issues),
                                      last_marker, boundary, panic_observed, next_safe_action)
