"""Profile-scoped gameplay settings with explicit staged application state."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any
from datetime import datetime, timezone
import json
from pathlib import Path

from .profiles import Profile, ProfileService
from .storage import write_json_atomic


@dataclass(frozen=True)
class SettingDefinition:
    key: str
    name: str
    description: str
    default: Any
    value_type: str
    minimum: float | None = None
    maximum: float | None = None


DEFINITIONS = (
    SettingDefinition("enemy_damage_multiplier", "Enemy damage", "Research value for incoming damage.", 1.0, "number", 0.25, 4.0),
    SettingDefinition("resource_yield_multiplier", "Resource yield", "Research value for gathered resources.", 1.0, "number", 0.25, 4.0),
    SettingDefinition("experimental_rules", "Experimental rules", "Marks this profile as a tuning test surface.", False, "boolean"),
    SettingDefinition("base_crit_chance", "Base critical chance", "EML research value mapped to BalancingTable.baseCritChance.", 0.1, "number", 0.0, 1.0),
)


class GameSettingsService:
    def __init__(self, profiles: ProfileService):
        self.profiles = profiles

    def definitions(self) -> tuple[SettingDefinition, ...]:
        return DEFINITIONS

    def values(self, profile: Profile) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for definition in DEFINITIONS:
            value = profile.settings.get(definition.key, definition.default)
            if definition.value_type == "boolean":
                valid = isinstance(value, bool)
            else:
                valid = (
                    isinstance(value, (int, float)) and not isinstance(value, bool)
                    and math.isfinite(value)
                    and (definition.minimum is None or value >= definition.minimum)
                    and (definition.maximum is None or value <= definition.maximum)
                )
            result[definition.key] = value if valid else definition.default
        return result

    def stage(self, profile: Profile, key: str, value: Any) -> Profile:
        definition = next((item for item in DEFINITIONS if item.key == key), None)
        if not definition:
            raise ValueError(f"Unknown game setting: {key}")
        if definition.value_type == "number" and (
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or (definition.minimum is not None and value < definition.minimum)
            or (definition.maximum is not None and value > definition.maximum)
        ):
            raise ValueError(f"Invalid value for {key}")
        if definition.value_type == "boolean" and not isinstance(value, bool):
            raise ValueError(f"Invalid value for {key}")
        settings = dict(profile.settings)
        settings[key] = value
        updated = Profile(**{**profile.__dict__, "settings": settings})
        self.profiles.save(updated)
        return updated

    def reset(self, profile: Profile) -> Profile:
        updated = Profile(**{**profile.__dict__, "settings": {}})
        self.profiles.save(updated)
        return updated

    def export(self, profile: Profile) -> Path:
        """Write a portable tuning manifest outside the live game directory."""
        destination = self.profiles.root / "exports" / "game-settings" / f"{profile.id}.json"
        payload = {
            "schema_version": 1,
            "profile_id": profile.id,
            "profile_name": profile.name,
            "settings": self.values(profile),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "application_state": "staged-only",
        }
        write_json_atomic(destination, payload)
        return destination

    def import_manifest(self, profile: Profile, source: Path) -> Profile:
        """Import a previously exported staged manifest for the same profile."""
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("Unable to read game settings manifest") from exc
        if not isinstance(payload, dict):
            raise ValueError("Game settings manifest must be an object")
        if payload.get("schema_version") != 1:
            raise ValueError("Unsupported game settings manifest version")
        if payload.get("profile_id") != profile.id:
            raise ValueError("Game settings manifest belongs to another profile")
        if payload.get("application_state") != "staged-only":
            raise ValueError("Only staged-only manifests can be imported")
        settings = payload.get("settings")
        if not isinstance(settings, dict):
            raise ValueError("Game settings manifest has invalid settings")
        definitions = {item.key: item for item in DEFINITIONS}
        if set(settings) != set(definitions):
            raise ValueError("Game settings manifest does not match the current setting definitions")
        validated: dict[str, Any] = {}
        for key, value in settings.items():
            definition = definitions[key]
            if definition.value_type == "number" and (
                isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or (definition.minimum is not None and value < definition.minimum)
                or (definition.maximum is not None and value > definition.maximum)
            ):
                raise ValueError(f"Invalid value for {key}")
            if definition.value_type == "boolean" and not isinstance(value, bool):
                raise ValueError(f"Invalid value for {key}")
            validated[key] = value
        updated = Profile(**{**profile.__dict__, "settings": validated})
        self.profiles.save(updated)
        return updated
