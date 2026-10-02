"""Structured EML diagnostics, log search, and support-bundle generation."""
from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DiagnosticEvent:
    level: str
    line_number: int
    message: str
    source: Path


class DiagnosticService:
    ERROR = ("panic", "fatal", "error", "out of bounds", "stack overflow")
    WARNING = ("warn", "warning")
    MAX_SCAN_BYTES = 16 * 1024 * 1024

    def parse_file(self, path: Path, max_bytes: int | None = None) -> list[DiagnosticEvent]:
        path = Path(path)
        try:
            if max_bytes and path.stat().st_size > max_bytes:
                with path.open("rb") as handle:
                    handle.seek(-max_bytes, 2)
                    raw = handle.read()
                lines = raw.decode("utf-8", errors="replace").splitlines()
                if lines:
                    lines = lines[1:]  # discard a possibly partial first record
            else:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
        events = []
        for number, line in enumerate(lines, 1):
            try:
                record = json.loads(line)
            except ValueError:
                record = None
            if isinstance(record, dict) and isinstance(record.get("level"), str):
                fields = record.get("fields") if isinstance(record.get("fields"), dict) else record
                parts = []
                if isinstance(fields, dict):
                    for key in ("message", "report", "error", "stacktrace"):
                        value = fields.get(key)
                        if value is not None and str(value) not in parts:
                            parts.append(str(value))
                message = " | ".join(parts) or line
                level = str(record["level"]).lower()
                if level in {"warn", "warning"}:
                    level = "warning"
                elif level in {"error", "fatal", "panic"}:
                    level = "error"
                else:
                    level = "info"
                events.append(DiagnosticEvent(level, number, message, path))
                continue
            lowered = line.lower()
            if any(marker in lowered for marker in self.ERROR):
                level = "error"
            elif any(marker in lowered for marker in self.WARNING):
                level = "warning"
            else:
                level = "info"
            events.append(DiagnosticEvent(level, number, line, path))
        return events

    def search(self, logs_dir: Path, query: str | None = None, level: str | None = None, max_bytes: int | None = MAX_SCAN_BYTES) -> list[DiagnosticEvent]:
        logs_dir = Path(logs_dir)
        events: list[DiagnosticEvent] = []
        for path in sorted(logs_dir.glob("*.eml.log")) if logs_dir.is_dir() else []:
            events.extend(self.parse_file(path, max_bytes=max_bytes))
        query = query.lower() if query else None
        return [event for event in events if (not query or query in event.message.lower()) and (not level or event.level == level)]

    def summarize(self, logs_dir: Path) -> dict[str, int | str | None]:
        events = self.search(logs_dir)
        log_paths = sorted(Path(logs_dir).glob("*.eml.log")) if Path(logs_dir).is_dir() else []
        latest_path = log_paths[-1] if log_paths else None
        latest_events = self.parse_file(latest_path) if latest_path else []
        total_errors = sum(event.level == "error" for event in events)
        latest_errors = sum(event.level == "error" for event in latest_events)
        latest_warnings = sum(event.level == "warning" for event in latest_events)
        current_errors = latest_errors
        current_warnings = latest_warnings
        last_success_session = None
        if latest_path:
            # Large EML logs are parsed in a bounded tail for detailed search,
            # but status history must not silently disappear when an older
            # error falls outside that tail. Count lightweight structured
            # levels line-by-line without retaining the records.
            full_errors = 0
            full_warnings = 0
            full_current_errors = 0
            full_current_warnings = 0
            full_boundary = -1
            full_success = None
            try:
                with latest_path.open("r", encoding="utf-8", errors="replace") as stream:
                    for index, line in enumerate(stream):
                        try:
                            record = json.loads(line)
                        except ValueError:
                            record = None
                        fields = record.get("fields") if isinstance(record, dict) and isinstance(record.get("fields"), dict) else {}
                        message = str(fields.get("message", ""))
                        if message == "Type registry loaded successfully":
                            full_boundary = index
                            full_success = record.get("timestamp")
                            full_current_errors = 0
                            full_current_warnings = 0
                        level = str(record.get("level", "")).lower() if isinstance(record, dict) else ""
                        if level in {"error", "fatal", "panic"}:
                            full_errors += 1
                            if index > full_boundary: full_current_errors += 1
                        elif level in {"warn", "warning"}:
                            full_warnings += 1
                            if index > full_boundary: full_current_warnings += 1
            except OSError:
                pass
            if full_errors or full_warnings or full_success:
                total_errors = full_errors
                current_errors = full_current_errors
                current_warnings = full_current_warnings
                last_success_session = full_success
                latest_errors = full_errors
        current_status = "failed" if current_errors else "degraded" if current_warnings else "healthy" if latest_events else "unknown"
        latest_messages = "\n".join(event.message.lower() for event in latest_events if event.level == "error")
        if "panic in a function that cannot unwind" in latest_messages:
            recommended_action = (
                "Stop the game, keep the failed probe quarantined, and restore the last-known-good profile. "
                "Do not repeat the same mutation; use a read-only or typed research probe instead."
            )
        elif current_status == "failed":
            recommended_action = "Stop the game, review the failed module, and use automatic recovery before trying again."
        elif current_status == "degraded":
            recommended_action = "Review the warnings before enabling additional research modules."
        else:
            recommended_action = "No recovery action is needed."
        return {
            "status": current_status,
            "current_runtime_status": current_status,
            "current_errors": current_errors,
            "current_warnings": current_warnings,
            "events": len(events),
            "errors": total_errors,
            "warnings": full_warnings if latest_path and (full_errors or full_warnings or last_success_session) else sum(event.level == "warning" for event in events),
            "latest_log": latest_path.name if latest_path else None,
            "latest_status": current_status,
            "latest_errors": latest_errors,
            "historical_errors": max(0, total_errors - current_errors),
            "last_success_session": last_success_session,
            "recommended_action": recommended_action,
        }


class SupportBundleService:
    """Create a bounded, local-only diagnostic archive."""

    def create(self, base_dir: Path, game_dir: Path | None, destination: Path) -> Path:
        base_dir = Path(base_dir).resolve(); destination = Path(destination).resolve()
        files: list[tuple[Path, str]] = []
        for path in sorted((base_dir / "profiles").glob("*.json")):
            if path.name not in {"active_profile.json", "installer.json", "setting_inventory.json", "legacy_setting_mapping.json"}:
                continue
            files.append((path, f"profiles/{path.name}"))
        for path in sorted((base_dir / "modules").glob("*/module.json")):
            files.append((path, f"modules/{path.parent.name}/module.json"))
        # Include bounded, non-secret research provenance needed to reproduce
        # compatibility decisions; never include arbitrary research payloads.
        for path in sorted((base_dir / "research").glob("*catalog*.json")):
            files.append((path, f"research/{path.name}"))
        for path in sorted((base_dir / "research").glob("*VALIDATION*.md")):
            files.append((path, f"research/{path.name}"))
        for path in sorted((base_dir / "research").glob("*FEASIBILITY*.md")):
            files.append((path, f"research/{path.name}"))
        boundary_dir = base_dir / "research" / "localization_boundary_reports"
        for path in sorted(boundary_dir.glob("*.json"))[-10:]:
            files.append((path, f"research/localization_boundary_reports/{path.name}"))
        feasibility_dir = base_dir / "research" / "feasibility_reports"
        for path in sorted(feasibility_dir.glob("*.json"))[-10:]:
            files.append((path, f"research/feasibility_reports/{path.name}"))
        for path in sorted((base_dir / "research").glob("live_preflight_*.json"))[-5:]:
            files.append((path, f"research/{path.name}"))
        if game_dir:
            for path in sorted((Path(game_dir) / "logs").glob("*.eml.log"))[-5:]:
                files.append((path, f"game_logs/{path.name}"))
        summary = DiagnosticService().summarize(Path(game_dir) / "logs") if game_dir else {"status": "unknown"}
        from .health_report import HealthReportService
        health = HealthReportService(base_dir).generate(game_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("summary.json", json.dumps({"created": datetime.now(timezone.utc).isoformat(), "diagnostics": summary}, indent=2))
            archive.writestr("health.json", json.dumps(health, indent=2))
            for source, name in files[:64]:
                if source.is_file(): archive.write(source, name)
        return destination
