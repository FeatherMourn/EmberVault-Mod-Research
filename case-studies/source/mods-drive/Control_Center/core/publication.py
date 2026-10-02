"""Build-aware, read-only publication planning for content projects.

The planner does not write to the game directory or claim that the engine
consumed an asset.  It produces a deterministic publication plan from the
project manifest, asset manifest, and declared target build.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .asset_service import AssetService
from .content_validation import ContentProjectValidator


class PublicationError(RuntimeError):
    pass


@dataclass(frozen=True)
class PublicationNode:
    node_id: str
    kind: str
    path: str | None
    status: str


@dataclass(frozen=True)
class PublicationPlan:
    project: Path
    target_build: str | None
    project_fingerprint: str
    nodes: tuple[PublicationNode, ...]
    edges: tuple[tuple[str, str], ...]
    issues: tuple[str, ...]

    @property
    def publishable(self) -> bool:
        return not self.issues and all(node.status != "invalid" for node in self.nodes)


class PublicationPlanner:
    """Create a deterministic plan without mutating the project or game."""

    def __init__(self) -> None:
        self.validator = ContentProjectValidator()
        self.assets = AssetService()

    def plan(self, project: Path, target_build: str | None = None) -> PublicationPlan:
        project = Path(project).resolve()
        if not project.is_dir():
            raise PublicationError(f"Project directory does not exist: {project}")

        validation = self.validator.validate(project)
        issues = [f"{issue.code}: {issue.message}" for issue in validation.issues if issue.severity == "error"]
        manifest = validation.manifest or {}
        nodes: list[PublicationNode] = []
        edges: list[tuple[str, str]] = []

        for entry in manifest.get("content", []):
            if not isinstance(entry, dict):
                continue
            node_id = str(entry.get("id", "")).strip()
            if not node_id:
                continue
            relative = str(entry.get("path", "")).strip() or None
            status = "invalid" if relative and not (project / relative).is_file() else "resource-staged"
            nodes.append(PublicationNode(node_id, "resource", relative, status))

        asset_manifest = self._load_assets(project, issues)
        for entry in asset_manifest.get("assets", []):
            if not isinstance(entry, dict):
                continue
            relative = str(entry.get("path", "")).strip()
            if not relative:
                continue
            status = str(entry.get("runtime_status", "packaged"))
            if not (project / relative).is_file():
                status = "invalid"
            nodes.append(PublicationNode(relative, "content_asset", relative, status))

        resource_ids = {node.node_id for node in nodes if node.kind == "resource"}
        declared_asset_dependencies = manifest.get("asset_dependencies", [])
        if declared_asset_dependencies is not None:
            if not isinstance(declared_asset_dependencies, list):
                issues.append("assets.dependencies_invalid: asset_dependencies must be a list")
            else:
                referenced_resource_ids = {
                    str(reference.get("resource_id", "")).strip()
                    for reference in asset_manifest.get("references", [])
                    if isinstance(reference, dict) and str(reference.get("resource_id", "")).strip()
                }
                for dependency in declared_asset_dependencies:
                    dependency_id = str(dependency).strip()
                    if dependency_id and dependency_id not in referenced_resource_ids:
                        issues.append(f"assets.dependency_unresolved: {dependency_id} has no recorded asset reference")
        for reference in asset_manifest.get("references", []):
            if not isinstance(reference, dict):
                continue
            asset = str(reference.get("asset", "")).strip()
            resource_type = str(reference.get("resource_type", "")).strip()
            resource_id = str(reference.get("resource_id", "")).strip()
            if asset and resource_type and resource_id in resource_ids:
                edges.append((resource_id, asset))
            elif asset and resource_type:
                issues.append(f"assets.reference_unresolved: {asset} requires an explicit resource_id")

        fingerprint = self._fingerprint(project, target_build, nodes, edges)
        return PublicationPlan(project, str(target_build) if target_build else None, fingerprint,
                               tuple(nodes), tuple(sorted(set(edges))), tuple(sorted(set(issues))))

    @staticmethod
    def _load_assets(project: Path, issues: list[str]) -> dict[str, Any]:
        path = project / AssetService.MANIFEST
        if not path.is_file():
            return {"assets": [], "references": []}
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            issues.append(f"assets.manifest_invalid: {exc}")
            return {"assets": [], "references": []}
        if not isinstance(data, dict):
            issues.append("assets.manifest_invalid: manifest must be an object")
            return {"assets": [], "references": []}
        return data

    @staticmethod
    def _fingerprint(project: Path, target_build: str | None,
                     nodes: list[PublicationNode], edges: list[tuple[str, str]]) -> str:
        digest = hashlib.sha256()
        digest.update(str(target_build or "").encode())
        for node in sorted(nodes, key=lambda item: (item.kind, item.node_id)):
            digest.update(f"node|{node.kind}|{node.node_id}|{node.path}|{node.status}\n".encode())
        for source, target in sorted(set(edges)):
            digest.update(f"edge|{source}|{target}\n".encode())
        return digest.hexdigest()
