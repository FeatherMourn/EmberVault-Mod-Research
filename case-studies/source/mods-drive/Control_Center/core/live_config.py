"""Atomic live-configuration bridge for settings explicitly marked dynamic."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any


class LiveConfigError(RuntimeError):
    pass


class LiveConfigService:
    def build_payload(self, modules: dict[str, dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
        source = config.get("module_settings", {})
        dynamic: dict[str, dict[str, Any]] = {}
        for module_id, manifest in modules.items():
            allowed = {str(setting.get("key")) for setting in manifest.get("settings", []) if setting.get("dynamic") is True}
            if not allowed: continue
            values = source.get(module_id, {})
            dynamic[module_id] = {key: values[key] for key in sorted(allowed) if key in values}
        canonical = json.dumps(dynamic, sort_keys=True, separators=(",", ":"))
        return {"schema": "control_center.live_config.v1", "timestamp": time.time(), "profile_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(), "modules": dynamic}

    def write(self, path: Path, modules: dict[str, dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
        path = Path(path); payload = self.build_payload(modules, config); path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
        return payload

    @staticmethod
    def read(path: Path) -> dict[str, Any]:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise LiveConfigError(f"Live configuration is invalid: {exc}") from exc
        if not isinstance(data, dict) or data.get("schema") != "control_center.live_config.v1" or not isinstance(data.get("modules"), dict):
            raise LiveConfigError("Unsupported live configuration schema.")
        return data
