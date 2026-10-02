"""Conservative save/world and client-server compatibility analysis."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PersistenceAnalysis:
    status: str
    issues: tuple[str, ...]
    warnings: tuple[str, ...]
    stable_ids: tuple[int, ...]
    requires_matching_clients: bool


class PersistenceAnalyzer:
    """Analyze declarations; runtime save persistence remains unverified."""

    def analyze(self, project: Path, server_manifest: dict[str, Any] | None = None) -> PersistenceAnalysis:
        project = Path(project).resolve()
        manifest = self._load(project / "mod.json")
        issues: list[str] = []
        warnings: list[str] = []
        stable_ids: list[int] = []
        for entry in manifest.get("content", []) if isinstance(manifest, dict) else []:
            if not isinstance(entry, dict):
                continue
            numeric_id = entry.get("numeric_id")
            if isinstance(numeric_id, int) and numeric_id > 0:
                stable_ids.append(numeric_id)
            else:
                warnings.append(f"Content entry lacks a stable numeric_id: {entry.get('id', 'unknown')}")
        if manifest.get("feature_state") != "verified":
            warnings.append("Content is not runtime-verified; save persistence is unproven.")
        if manifest.get("save_persistence_verified") is not True:
            warnings.append("No controlled save/reload evidence is recorded.")
        requires_clients = bool(manifest.get("multiplayer", {}).get("requires_matching_clients", True))
        if server_manifest is not None:
            server_ids = self._ids(server_manifest)
            if set(stable_ids) - server_ids:
                issues.append("Client content IDs are missing from the supplied server manifest.")
            if server_manifest.get("build_id") != manifest.get("game_build"):
                warnings.append("Client and server build declarations do not match or are incomplete.")
        if manifest.get("removal_policy") not in {"safe_if_absent", "migration_required", "blocked"}:
            warnings.append("Removal policy is undeclared; removing content may strand save references.")
        status = "review_required" if issues else ("research_only" if warnings else "declared_compatible")
        return PersistenceAnalysis(status, tuple(issues), tuple(warnings), tuple(sorted(set(stable_ids))), requires_clients)

    @staticmethod
    def _load(path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    @staticmethod
    def _ids(manifest: dict[str, Any]) -> set[int]:
        result: set[int] = set()
        for entry in manifest.get("content", []) if isinstance(manifest, dict) else []:
            if isinstance(entry, dict) and isinstance(entry.get("numeric_id"), int):
                result.add(entry["numeric_id"])
        return result
