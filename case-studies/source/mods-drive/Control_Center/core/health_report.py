"""Unified machine-readable Control Center health reports."""
from __future__ import annotations

import json
import hashlib
import time
from pathlib import Path
from typing import Any

from .compatibility import CompatibilityEngine
from .content_validation import ContentProjectValidator
from .diagnostics import DiagnosticService
from .platform_services import PlatformService
from .recovery import ModQuarantineService
from .package_service import PackageService
from .publication import PublicationPlanner, PublicationError
from .build_profiles import BuildProfileService


class HealthReportService:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.platform = PlatformService(self.base_dir)
        self.compatibility = CompatibilityEngine()
        self.content = ContentProjectValidator()
        self.diagnostics = DiagnosticService()
        self.quarantine = ModQuarantineService(self.base_dir / "profiles")
        self.publication = PublicationPlanner()
        self.build_profiles = BuildProfileService()

    def generate(self, game_dir: Path | None = None) -> dict[str, Any]:
        self.platform.game_dir = Path(game_dir) if game_dir else None
        status = self.platform.status(set(self.platform.modules.build().modules))
        build_id = status.game.build_id
        self.compatibility = CompatibilityEngine(loader_api_version=status.loader_api_version)
        build_profile = self.build_profiles.snapshot(game_dir) if game_dir else None
        compatibility = self.compatibility.evaluate_all(status.graph.modules, build_id, enabled=set(status.graph.modules))
        projects = self._projects()
        content = []
        for project in projects:
            report = self.content.validate(project)
            item = {"project": str(project), "valid": report.valid,
                    "issues": [issue.message for issue in report.issues]}
            try:
                plan = self.publication.plan(project, build_id)
                item["publication"] = {
                    "publishable": plan.publishable,
                    "target_build": plan.target_build,
                    "fingerprint": plan.project_fingerprint,
                    "node_count": len(plan.nodes),
                    "edge_count": len(plan.edges),
                    "issues": list(plan.issues),
                }
            except PublicationError as exc:
                item["publication"] = {"publishable": False, "issues": [str(exc)]}
            content.append(item)
        logs_dir = Path(game_dir) / "logs" if game_dir else None
        return {
            "schema": "control_center.health.v1",
            "generated_at": time.time(),
            "game": {"build_id": build_id, "path": str(game_dir) if game_dir else None,
                     "build_profile": self.build_profiles.to_dict(build_profile) if build_profile else None},
            "runtime": {"status": status.runtime.status, "log": str(status.runtime.log_path) if status.runtime.log_path else None,
                        "loader_api_version": status.loader_api_version, "errors": list(status.runtime.errors)},
            "modules": {"count": len(status.graph.modules), "order": status.graph.order, "issues": [issue.message for issue in status.graph.issues]},
            "compatibility": {module_id: {"compatible": report.compatible, "issues": [issue.message for issue in report.issues]} for module_id, report in compatibility.items()},
            "content": content,
            "mods": self._mod_inventory(game_dir),
            "diagnostics": self.diagnostics.summarize(logs_dir) if logs_dir else {"status": "unknown", "current_runtime_status": "unknown", "historical_errors": 0},
            "quarantine": {"count": len(self.quarantine.records())},
        }

    def write(self, destination: Path, game_dir: Path | None = None) -> Path:
        destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(self.generate(game_dir), indent=2) + "\n", encoding="utf-8")
        temporary.replace(destination)
        return destination

    def _projects(self) -> list[Path]:
        roots = []
        for parent in (self.base_dir / "research" / "staging", self.base_dir / "custom_content" / "projects", self.base_dir / "custom_content" / "imports"):
            if parent.is_dir():
                roots.extend(path for path in sorted(parent.iterdir()) if path.is_dir() and any((path / name).is_file() for name in ("mod.json", "content.json", "CLONE_MANIFEST.json")))
        return roots

    @staticmethod
    def _mod_inventory(game_dir: Path | None) -> list[dict[str, Any]]:
        if not game_dir:
            return []
        mods_dir = Path(game_dir) / "mods"
        if not mods_dir.is_dir():
            return []
        result: list[dict[str, Any]] = []
        for directory in sorted(mods_dir.iterdir()):
            if not directory.is_dir() or directory.is_symlink():
                continue
            manifest_path = directory / "mod.json"
            if not manifest_path.is_file():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                result.append({"id": directory.name, "path": str(directory), "status": "invalid_manifest"})
                continue
            entry: dict[str, Any] = {
                "id": str(manifest.get("id", directory.name)),
                "name": str(manifest.get("name", directory.name)),
                "version": str(manifest.get("version", "unknown")),
                "path": str(directory),
                "feature_state": str(manifest.get("feature_state", "unspecified")),
                "content_origin": "experimental" if str(manifest.get("feature_state", "")).lower() == "research-only" else "unknown",
                "dependencies": manifest.get("dependencies", []),
                "load_order": manifest.get("load_order"),
                "status": "installed",
            }
            if (directory / PackageService.MANIFEST).is_file():
                valid, errors = PackageService().verify(directory)
                entry["integrity"] = "verified" if valid else "failed"
                entry["integrity_state"] = "verified" if valid else "user_modified"
                if errors:
                    entry["integrity_errors"] = errors
            else:
                owner = directory / ".emh-owner.json"
                owner_kind = "control_center"
                if not owner.is_file():
                    owner = directory / ".emh-third-party-owner.json"
                    owner_kind = "third_party"
                if owner.is_file():
                    try:
                        record = json.loads(owner.read_text(encoding="utf-8-sig"))
                        raw_backup = str(record.get("backup", "")).strip()
                        if raw_backup:
                            backup_path = Path(raw_backup).resolve()
                            backup_root = backup_path.parent if backup_path.name and backup_path.parent.is_dir() else backup_path
                            entry["restore_points"] = sum(1 for item in backup_root.iterdir() if item.is_dir()) if backup_root.is_dir() else 0
                        else:
                            entry["restore_points"] = 0
                        errors = []
                        missing = []
                        modified = []
                        for relative, expected in record.get("files", {}).items():
                            path = directory / relative
                            try:
                                path.resolve().relative_to(directory.resolve())
                            except ValueError:
                                errors.append(f"Unsafe owned path: {relative}")
                                continue
                            if path.is_symlink():
                                errors.append(f"Symbolic-link owned file: {relative}")
                                continue
                            if not path.is_file():
                                missing.append(relative)
                                errors.append(f"Missing owned file: {relative}")
                                continue
                            digest = hashlib.sha256(path.read_bytes()).hexdigest()
                            if digest != expected:
                                modified.append(relative)
                                errors.append(f"Owned file hash mismatch: {relative}")
                        entry["integrity"] = "verified" if not errors else "failed"
                        if errors:
                            entry["integrity_state"] = "missing" if missing and not modified else "user_modified"
                        elif owner_kind == "control_center" and record.get("updated_by") == "control_center":
                            entry["integrity_state"] = "updated_by_control_center"
                        else:
                            entry["integrity_state"] = "verified"
                        entry["ownership"] = "control_center_managed" if record.get("managed") else owner_kind
                        entry["managed"] = bool(record.get("managed", owner_kind == "control_center"))
                        entry["change_source"] = str(record.get("change_source", "third_party" if owner_kind == "third_party" else "control_center"))
                        if errors: entry["integrity_errors"] = errors
                    except (OSError, ValueError, TypeError):
                        entry["integrity"] = "failed"
                        entry["integrity_state"] = "user_modified"
                        entry["integrity_errors"] = ["Ownership manifest is invalid."]
                else:
                    entry["integrity"] = "not_available"
                    entry["integrity_state"] = "untracked"
            result.append(entry)
        return result
