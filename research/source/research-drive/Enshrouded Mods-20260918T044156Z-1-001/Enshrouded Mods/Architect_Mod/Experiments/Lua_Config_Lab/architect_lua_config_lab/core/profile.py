"""Profile model and JSON persistence.

A profile is a named collection of startup resource edits. It uses a stable
JSON format with a version number from day one. Application state is never
written into the generated Lua; the profile JSON is the tool's own format.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional

PROFILE_VERSION = 1

EVIDENCE_STATES = {
    "PROVEN_STARTUP_EFFECT",
    "SCHEMA_VALIDATED",
    "EXPERIMENTAL",
    "DISPROVEN",
    "UNSUPPORTED",
}

TARGET_MODES = {"first", "all", "match"}


@dataclass
class Target:
    mode: str = "first"
    # For MATCH mode: scalar equality selector.
    selector: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"mode": self.mode}
        if self.selector is not None:
            data["selector"] = self.selector
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Target":
        return Target(
            mode=data.get("mode", "first"),
            selector=data.get("selector"),
        )

    def validate(self) -> Optional[str]:
        if self.mode not in TARGET_MODES:
            return "unknown target mode %r" % self.mode
        if self.mode == "match":
            selector = self.selector or {}
            if "field" not in selector or "operator" not in selector or "value" not in selector:
                return "MATCH target requires a selector with field/operator/value"
            if selector.get("operator") != "eq":
                return "only operator 'eq' is supported in the MVP"
        return None


@dataclass
class Edit:
    enabled: bool = True
    resource_type: str = ""          # qualified, e.g. "keen::BalancingTable"
    target: Target = dc_field(default_factory=Target)
    path: str = ""                   # e.g. "playerBaseStamina"
    schema_type: str = ""            # resolved leaf type, e.g. "u32"
    value: Any = None
    evidence_state: str = "EXPERIMENTAL"
    expected_original: Any = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "enabled": self.enabled,
            "resource_type": self.resource_type,
            "target": self.target.to_dict(),
            "path": self.path,
            "schema_type": self.schema_type,
            "value": self.value,
            "evidence_state": self.evidence_state,
        }
        if self.expected_original is not None:
            data["expected_original"] = self.expected_original
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Edit":
        return Edit(
            enabled=bool(data.get("enabled", True)),
            resource_type=data.get("resource_type", ""),
            target=Target.from_dict(data.get("target", {})),
            path=data.get("path", ""),
            schema_type=data.get("schema_type", ""),
            value=data.get("value"),
            evidence_state=data.get("evidence_state", "EXPERIMENTAL"),
            expected_original=data.get("expected_original"),
        )

    def validate(self) -> Optional[str]:
        if not self.resource_type:
            return "edit is missing resource_type"
        if not self.path:
            return "edit is missing path"
        if not self.schema_type:
            return "edit is missing schema_type"
        if self.evidence_state not in EVIDENCE_STATES:
            return "unknown evidence_state %r" % self.evidence_state
        return self.target.validate()


@dataclass
class Profile:
    name: str = ""
    description: str = ""
    game_build: str = ""
    types_lua_sha256: str = ""
    edits: List[Edit] = dc_field(default_factory=list)
    profile_version: int = PROFILE_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_version": self.profile_version,
            "name": self.name,
            "description": self.description,
            "game_build": self.game_build,
            "types_lua_sha256": self.types_lua_sha256,
            "edits": [edit.to_dict() for edit in self.edits],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Profile":
        return Profile(
            profile_version=int(data.get("profile_version", PROFILE_VERSION)),
            name=data.get("name", ""),
            description=data.get("description", ""),
            game_build=data.get("game_build", ""),
            types_lua_sha256=data.get("types_lua_sha256", ""),
            edits=[Edit.from_dict(item) for item in data.get("edits", [])],
        )

    def validate(self) -> Optional[str]:
        if self.profile_version != PROFILE_VERSION:
            return "unsupported profile_version %r" % self.profile_version
        if not self.name:
            return "profile has no name"
        for edit in self.edits:
            problem = edit.validate()
            if problem:
                return "edit %r: %s" % (edit.path, problem)
        return None

    def enabled_edits(self) -> List[Edit]:
        return [edit for edit in self.edits if edit.enabled]


def profile_hash(profile: Profile) -> str:
    """Deterministic SHA-256 of the semantic profile content."""
    canonical = json.dumps(
        profile.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def dumps(profile: Profile) -> str:
    return json.dumps(profile.to_dict(), indent=2, ensure_ascii=False)


def loads(text: str) -> Profile:
    return Profile.from_dict(json.loads(text))


def save_profile(profile: Profile, path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(dumps(profile))
        handle.write("\n")


def load_profile(path: str) -> Profile:
    with open(path, "r", encoding="utf-8") as handle:
        return loads(handle.read())


def semantic_equal(a: Profile, b: Profile) -> bool:
    """Compare two profiles for semantic (not byte) equality."""
    return _normalise(a.to_dict()) == _normalise(b.to_dict())


def _normalise(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalise(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_normalise(v) for v in value]
    return value
