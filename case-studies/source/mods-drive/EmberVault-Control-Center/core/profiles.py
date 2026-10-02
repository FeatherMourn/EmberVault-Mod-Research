"""Profile storage for isolated Enshrouded configurations."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class Profile:
    id: str
    name: str
    description: str = ""
    profile_type: str = "custom"
    enabled_packages: list[str] = field(default_factory=list)
    settings: dict = field(default_factory=dict)
    target_build: str | None = None
    last_known_good_operation: str | None = None


class ProfileService:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.directory = self.root / "profiles"

    def _path(self, profile_id: str) -> Path:
        if not profile_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in profile_id):
            raise ValueError("Invalid profile id")
        return self.directory / f"{profile_id}.json"

    def list(self) -> list[Profile]:
        profiles = []
        seen_ids: set[str] = set()
        for path in sorted(self.directory.glob("*.json")) if self.directory.is_dir() else []:
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(raw, dict):
                    continue
                profile = Profile(**raw)
                if (not isinstance(profile.id, str) or not profile.id
                        or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in profile.id)
                        or not isinstance(profile.name, str) or not profile.name.strip()):
                    continue
                if profile.id in seen_ids:
                    continue
                if not isinstance(profile.enabled_packages, list):
                    profile.enabled_packages = []
                else:
                    profile.enabled_packages = [item for item in profile.enabled_packages if isinstance(item, str) and item.strip()]
                if not isinstance(profile.settings, dict):
                    profile.settings = {}
                seen_ids.add(profile.id)
                profiles.append(profile)
            except (OSError, ValueError, TypeError):
                continue
        return profiles

    def save(self, profile: Profile) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self._path(profile.id)
        fd, temp_name = tempfile.mkstemp(prefix=f"{profile.id}-", suffix=".tmp", dir=self.directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(asdict(profile), handle, indent=2)
                handle.write("\n")
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def ensure_defaults(self) -> list[Profile]:
        defaults = [
            Profile("default", "Default", "Safe starting profile.", "stable"),
            Profile("research", "Research", "Isolated experimental profile.", "research"),
        ]
        existing = {profile.id for profile in self.list()}
        for profile in defaults:
            if profile.id not in existing:
                self.save(profile)
        return self.list()

    def create_custom(self, name: str, description: str = "") -> Profile:
        name = name.strip()
        if not name:
            raise ValueError("Profile name is required")
        profile_id = "".join(char.lower() if char.isalnum() else "-" for char in name).strip("-")
        if not profile_id:
            raise ValueError("Profile name must contain letters or numbers")
        if any(profile.id == profile_id for profile in self.list()):
            raise ValueError(f"Profile already exists: {profile_id}")
        profile = Profile(profile_id, name, description.strip(), "custom")
        self.save(profile)
        return profile

    def delete_custom(self, profile_id: str) -> None:
        if profile_id in {"default", "research"}:
            raise ValueError("Built-in profiles cannot be deleted")
        target = self._path(profile_id)
        if not target.is_file():
            raise ValueError(f"Unknown profile: {profile_id}")
        target.unlink()

    def export_profile(self, profile_id: str, destination: Path) -> Path:
        profile = next((item for item in self.list() if item.id == profile_id), None)
        if not profile:
            raise ValueError(f"Unknown profile: {profile_id}")
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({"schema_version": 1, "profile": asdict(profile)}, indent=2) + "\n", encoding="utf-8")
        return destination

    def import_profile(self, source: Path, *, new_id: str | None = None) -> Profile:
        raw = json.loads(Path(source).read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("schema_version") != 1 or not isinstance(raw.get("profile"), dict):
            raise ValueError("Invalid profile export")
        data = dict(raw["profile"])
        data["id"] = new_id or data.get("id")
        if not isinstance(data.get("id"), str) or any(item.id == data["id"] for item in self.list()):
            raise ValueError("Imported profile ID is missing or already exists")
        profile = Profile(**data)
        self.save(profile)
        return profile
