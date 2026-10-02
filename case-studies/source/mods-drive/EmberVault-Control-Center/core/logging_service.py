"""Structured JSON-lines logging shared by every EmberVault component."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path


class StructuredLogService:
    def __init__(self, path: Path, application: str = "control-center"):
        self.path = Path(path)
        self.application = application
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, severity: str, message: str, *, operation_id: str | None = None,
              profile_id: str | None = None, package_id: str | None = None,
              details: dict | None = None) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "application": self.application,
            "severity": severity.lower(),
            "message": message,
            "operation_id": operation_id,
            "profile_id": profile_id,
            "package_id": package_id,
            "details": details if isinstance(details, dict) else ({"value": details} if details is not None else {}),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")

    def info(self, message: str, **kwargs) -> None:
        self.write("info", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self.write("warning", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self.write("error", message, **kwargs)
