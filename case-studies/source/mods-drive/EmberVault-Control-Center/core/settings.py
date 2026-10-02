"""Persistent application settings with atomic writes."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Settings:
    game_path: str | None = None
    backup_directory: str | None = None
    module_directory: str | None = None
    update_channel: str = "stable"
    theme: str = "ember-dark"
    advanced_mode: bool = False


class SettingsService:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "settings.json"

    def load(self) -> Settings:
        if not self.path.is_file():
            return Settings()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            defaults = Settings()
            values = {k: raw[k] for k in asdict(defaults) if isinstance(raw, dict) and k in raw}
            for key in ("game_path", "backup_directory", "module_directory"):
                if key in values and values[key] is not None and not isinstance(values[key], str):
                    values[key] = getattr(defaults, key)
            for key in ("update_channel", "theme"):
                if key in values and (not isinstance(values[key], str) or not values[key].strip()):
                    values[key] = getattr(defaults, key)
            if "advanced_mode" in values and not isinstance(values["advanced_mode"], bool):
                values["advanced_mode"] = defaults.advanced_mode
            return Settings(**values)
        except (OSError, ValueError, TypeError):
            return Settings()

    def save(self, settings: Settings) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="settings-", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(asdict(settings), handle, indent=2)
                handle.write("\n")
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
