"""Inspection and donor-schema comparison for extracted KFC resources."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .content_validation import KNOWN_RESOURCE_TYPES


GUID_RE = re.compile(r"^[0-9a-fA-F-]{36}")


@dataclass(frozen=True)
class ResourceRecord:
    resource_type: str
    path: Path
    guid: str | None
    data: dict[str, Any]
    sha256: str
    schema: dict[str, str]
    arrays: dict[str, int]


@dataclass(frozen=True)
class SchemaDifference:
    severity: str
    path: str
    message: str


@dataclass(frozen=True)
class ClonePlan:
    resource_type: str
    donor: Path
    destination: Path
    donor_guid: str | None
    schema_fingerprint: str
    differences: tuple[SchemaDifference, ...]
    warnings: tuple[str, ...]

    @property
    def safe(self) -> bool:
        return not any(item.severity == "error" for item in self.differences)


class ResourceInspector:
    """Read-only inspector; it never edits extracted KFC files or the game."""

    def metadata_policy(self, resource_type: str, policy_path: Path | None = None) -> dict[str, Any]:
        """Return the build-aware metadata safety decision for a resource type."""
        path = Path(policy_path) if policy_path else Path(__file__).resolve().parents[1] / "research" / "SAFE_METADATA_RESOURCE_TYPES_20260928.json"
        try:
            policy = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            return {"state": "unknown", "type": resource_type, "error": str(exc)}
        verified = {str(item.get("type")) for item in policy.get("verified_types", [])}
        quarantined = {str(item.get("type")): str(item.get("reason", "quarantined")) for item in policy.get("quarantined_types", [])}
        aliases = [str(resource_type)]
        if not str(resource_type).startswith("keen::"):
            aliases.append("keen::" + str(resource_type))
        quarantined_match = next((name for name in aliases if name in quarantined), None)
        if quarantined_match:
            return {"state": "quarantined", "type": resource_type, "policy_type": quarantined_match, "reason": quarantined[quarantined_match], "target_build": policy.get("target_build")}
        verified_match = next((name for name in aliases if name in verified), None)
        if verified_match:
            return {"state": "verified", "type": resource_type, "policy_type": verified_match, "target_build": policy.get("target_build")}
        return {"state": "unverified", "type": resource_type, "target_build": policy.get("target_build")}

    def inspect(self, path: Path, resource_type: str | None = None) -> ResourceRecord:
        path = Path(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"Unable to read resource JSON {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"Resource JSON must be an object: {path}")
        inferred = resource_type or path.parent.name
        schema: dict[str, str] = {}
        arrays: dict[str, int] = {}
        self._walk(data, "", schema, arrays)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        guid_match = GUID_RE.match(path.stem)
        return ResourceRecord(inferred, path, guid_match.group(0) if guid_match else None, data, digest, schema, arrays)

    def scan(self, project: Path) -> list[ResourceRecord]:
        project = Path(project)
        records: list[ResourceRecord] = []
        for path in sorted(project.rglob("*.json")):
            if path.name in ("mod.json", "content.json", "CLONE_MANIFEST.json"):
                continue
            try:
                records.append(self.inspect(path))
            except ValueError:
                continue
        return records

    def compare(self, donor: ResourceRecord, candidate: ResourceRecord) -> tuple[SchemaDifference, ...]:
        differences: list[SchemaDifference] = []
        for path, kind in donor.schema.items():
            if path not in candidate.schema:
                differences.append(SchemaDifference("error", path, "Required donor field is missing."))
            elif candidate.schema[path] != kind:
                differences.append(SchemaDifference("error", path, f"Type changed from {kind} to {candidate.schema[path]}."))
        for path in candidate.schema:
            if path not in donor.schema:
                differences.append(SchemaDifference("warning", path, "Candidate adds a field not present in the donor."))
        for path, length in donor.arrays.items():
            if path in candidate.arrays and candidate.arrays[path] != length:
                differences.append(SchemaDifference("warning", path, f"Observed array length changed from {length} to {candidate.arrays[path]}; fixed typed arrays must not be appended blindly."))
        return tuple(differences)

    def visual_references(self, record: ResourceRecord) -> list[dict[str, str]]:
        """Extract likely visual dependency fields without mutating resources.

        This heuristic inventory supports donor tracing; it does not prove
        that a referenced asset is replaceable or registerable at runtime.
        """
        tokens = ("visual", "model", "mesh", "texture", "material", "icon", "image", "render")
        found: list[dict[str, str]] = []

        def walk(value: Any, path: str) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    child_path = f"{path}.{key}" if path else str(key)
                    if any(token in str(key).casefold() for token in tokens) and isinstance(child, (str, int, float)) and not isinstance(child, bool):
                        found.append({"path": child_path, "key": str(key), "value": str(child), "kind": self._kind(child)})
                    walk(child, child_path)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, f"{path}[{index}]")

        walk(record.data, "")
        return found

    def visual_substitution_plan(self, donor: ResourceRecord, candidate: ResourceRecord) -> list[dict[str, str]]:
        """Compare visual references by field path for a research proposal."""
        donor_refs = {item["path"]: item for item in self.visual_references(donor)}
        candidate_refs = {item["path"]: item for item in self.visual_references(candidate)}
        plan: list[dict[str, str]] = []
        for path in sorted(set(donor_refs) | set(candidate_refs)):
            original = donor_refs.get(path)
            replacement = candidate_refs.get(path)
            if original and replacement:
                state = "unchanged" if original["value"] == replacement["value"] else "candidate_reference"
                plan.append({"path": path, "state": state, "donor": original["value"], "candidate": replacement["value"]})
            elif original:
                plan.append({"path": path, "state": "missing_in_candidate", "donor": original["value"], "candidate": ""})
            else:
                plan.append({"path": path, "state": "new_candidate_reference", "donor": "", "candidate": replacement["value"]})
        return plan

    def clone_plan(self, donor_path: Path, destination: Path, resource_type: str | None = None, candidate_path: Path | None = None) -> ClonePlan:
        donor = self.inspect(donor_path, resource_type)
        candidate = self.inspect(candidate_path, donor.resource_type) if candidate_path else donor
        differences = self.compare(donor, candidate)
        warnings = []
        if donor.resource_type.split("::")[-1] not in KNOWN_RESOURCE_TYPES:
            warnings.append(f"Resource type requires donor-specific research: {donor.resource_type}")
        metadata = self.metadata_policy(donor.resource_type)
        if metadata.get("state") == "quarantined":
            reason = metadata.get("reason", "runtime metadata access is not safe")
            warnings.append(
                f"Metadata lookup is quarantined for {donor.resource_type}: {reason}. "
                "Use a dedicated research probe before runtime registration."
            )
        if donor.arrays:
            warnings.append("Preserve observed array sizes; use typed-array replacement for UI entries rather than append.")
        fingerprint = hashlib.sha256(json.dumps(donor.schema, sort_keys=True).encode("utf-8")).hexdigest()
        return ClonePlan(donor.resource_type, donor.path, Path(destination), donor.guid, fingerprint, differences, tuple(warnings))

    def _walk(self, value: Any, prefix: str, schema: dict[str, str], arrays: dict[str, int]) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                schema[path] = self._kind(child)
                self._walk(child, path, schema, arrays)
        elif isinstance(value, list):
            arrays[prefix] = len(value)
            for index, child in enumerate(value[:1]):
                self._walk(child, f"{prefix}[]", schema, arrays)

    @staticmethod
    def _kind(value: Any) -> str:
        if value is None: return "null"
        if isinstance(value, bool): return "bool"
        if isinstance(value, dict): return "object"
        if isinstance(value, list): return "array"
        if isinstance(value, int) and not isinstance(value, bool): return "integer"
        if isinstance(value, float): return "number"
        if isinstance(value, str): return "string"
        return type(value).__name__
