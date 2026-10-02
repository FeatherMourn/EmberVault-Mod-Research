"""Profile preparation and safe game-launch planning."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class LaunchError(RuntimeError):
    pass


@dataclass(frozen=True)
class LaunchPlan:
    game_dir: Path
    profile_path: Path
    runtime_profile: Path
    profile_id: str
    profile_hash: str
    steam_uri: str


class ProfileLaunchService:
    GAME_APP_ID = "1203620"

    def clone_profile(self, source: Path, destination: Path, profile_id: str | None = None, world_id: str | None = None) -> Path:
        """Clone a profile without sharing mutable JSON state or overwriting files."""
        source = Path(source).resolve(); destination = Path(destination).resolve()
        try:
            record = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise LaunchError(f"Profile is invalid: {exc}") from exc
        if not isinstance(record, dict):
            raise LaunchError("Profile must be a JSON object.")
        config = record.get("config", record)
        if not isinstance(config, dict) or not isinstance(config.get("enabled_modules", {}), dict):
            raise LaunchError("Profile does not contain enabled_modules configuration.")
        cloned = json.loads(json.dumps(record))
        cloned["id"] = profile_id or f"{record.get('id', source.stem)}_copy"
        if world_id:
            cloned["world_id"] = world_id
        if destination.exists():
            raise LaunchError(f"Destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(cloned, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, destination)
        return destination

    def prepare(self, game_dir: Path, profile_path: Path, runtime_profile: Path) -> LaunchPlan:
        game_dir = Path(game_dir).resolve(); profile_path = Path(profile_path).resolve(); runtime_profile = Path(runtime_profile).resolve()
        if not (game_dir / "Enshrouded.exe").is_file():
            raise LaunchError(f"Enshrouded.exe was not found: {game_dir}")
        try:
            record = json.loads(profile_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise LaunchError(f"Profile is invalid: {exc}") from exc
        if not isinstance(record, dict): raise LaunchError("Profile must be a JSON object.")
        config = record.get("config", record)
        if not isinstance(config, dict) or not isinstance(config.get("enabled_modules", {}), dict):
            raise LaunchError("Profile does not contain enabled_modules configuration.")
        profile_id = str(record.get("id", profile_path.stem))
        payload = {"profile_id": profile_id, "source": str(profile_path), "config": config}
        if record.get("world_id"):
            payload["world_id"] = str(record["world_id"])
        encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        payload["sha256"] = digest
        runtime_profile.parent.mkdir(parents=True, exist_ok=True)
        temporary = runtime_profile.with_suffix(runtime_profile.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, runtime_profile)
        return LaunchPlan(game_dir, profile_path, runtime_profile, profile_id, digest, f"steam://rungameid/{self.GAME_APP_ID}")

    def launch(self, plan: LaunchPlan) -> None:
        if not (plan.game_dir / "Enshrouded.exe").is_file():
            raise LaunchError(f"Enshrouded.exe was not found: {plan.game_dir}")
        if not plan.runtime_profile.is_file():
            raise LaunchError("Prepared runtime profile is missing.")
        try:
            payload = json.loads(plan.runtime_profile.read_text(encoding="utf-8"))
            recorded_hash = payload.pop("sha256")
            canonical = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise LaunchError(f"Prepared runtime profile is invalid: {exc}") from exc
        digest = hashlib.sha256(canonical).hexdigest()
        if recorded_hash != digest or digest != plan.profile_hash:
            raise LaunchError("Prepared runtime profile hash verification failed.")
        try:
            running = "Enshrouded.exe" in subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq Enshrouded.exe"], text=True, stderr=subprocess.DEVNULL
            )
        except Exception as exc:
            raise LaunchError("Unable to establish Enshrouded process state; launch blocked.") from exc
        if running:
            raise LaunchError("Enshrouded is already running; launch blocked.")
        subprocess.Popen(["explorer.exe", plan.steam_uri])

    @staticmethod
    def eml_session_started(log_path: Path, baseline_size: int = 0) -> bool:
        """Return whether EML has written beyond a known log baseline.

        A running Enshrouded process alone is not proof that Steam loaded the
        proxy or that EML executed. Probe automation can use this check before
        waiting for mod markers, avoiding false-positive sessions.
        """
        try:
            return Path(log_path).stat().st_size > int(baseline_size)
        except (OSError, TypeError, ValueError):
            return False

    @staticmethod
    def wait_for_eml_session(log_path: Path, baseline_size: int = 0,
                             timeout: float = 30.0, interval: float = 0.5) -> bool:
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            if ProfileLaunchService.eml_session_started(log_path, baseline_size):
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(max(0.05, interval))
