"""Persistent game-build snapshots and update migration planning."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .compatibility import build_satisfies
from .platform_services import GameBuildDetector


@dataclass(frozen=True)
class UpdateStatus:
    state: str
    previous_build: str | None
    current_build: str | None
    message: str


class UpdateMigrationService:
    def __init__(self, snapshot_path: Path):
        self.snapshot_path = Path(snapshot_path)

    def inspect(self, game_dir: Path) -> UpdateStatus:
        current = GameBuildDetector().detect(game_dir).build_id
        previous = self._load().get("build_id")
        if not current:
            return UpdateStatus("unknown", previous, None, "Current game build could not be determined.")
        if not previous:
            return UpdateStatus("unrecorded", None, current, "Current build has not been recorded yet.")
        if previous == current:
            return UpdateStatus("unchanged", previous, current, "Game build matches the recorded compatibility snapshot.")
        return UpdateStatus("changed", previous, current, f"Game build changed from {previous} to {current}; modules require review.")

    def record(self, game_dir: Path, loader_api: str | None = None) -> UpdateStatus:
        status = self.inspect(game_dir)
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        existing = self._load()
        profiles = existing.get("profiles", {}) if isinstance(existing.get("profiles", {}), dict) else {}
        if status.current_build:
            profiles[str(status.current_build)] = {"build_id": status.current_build, "loader_api": loader_api, "recorded_at": time.time()}
        self.snapshot_path.write_text(json.dumps({"build_id": status.current_build, "loader_api": loader_api, "recorded_at": time.time(), "profiles": profiles}, indent=2), encoding="utf-8")
        return UpdateStatus("recorded", status.previous_build, status.current_build, "Compatibility snapshot recorded.")

    def compatibility_profile(self, build_id: str | None) -> dict[str, Any] | None:
        if not build_id: return None
        profiles = self._load().get("profiles", {})
        value = profiles.get(str(build_id)) if isinstance(profiles, dict) else None
        return value if isinstance(value, dict) else None

    def migration_plan(self, modules: dict[str, dict[str, Any]], current_build: str | None, update_detected: bool = False) -> list[dict[str, str]]:
        plan = []
        for module_id, manifest in sorted(modules.items()):
            builds = manifest.get("compatible_game_builds", [])
            if update_detected and manifest.get("feature_state") == "research-only":
                action = "disable"
                reason = "Research-only modules are disabled until fresh post-update evidence is collected."
            elif not builds and update_detected:
                action = "review"
                reason = "Game build changed and the module declares no compatibility range."
            else:
                result = build_satisfies(current_build, builds)
                if result is False:
                    action = "disable"
                    reason = "Current game build is outside declared compatibility."
                elif result is None:
                    action = "review"
                    reason = "Current game build is unknown."
                else:
                    action = "keep"
                    reason = "Declared compatibility includes the current build."
            plan.append({"module_id": module_id, "action": action, "reason": reason})
        return plan

    def _load(self) -> dict[str, Any]:
        if not self.snapshot_path.is_file(): return {}
        try:
            data = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}
