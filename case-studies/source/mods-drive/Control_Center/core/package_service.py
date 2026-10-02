"""Reproducible package manifests, hashes, export, and verification."""
from __future__ import annotations

import hashlib
import json
import os
import zipfile
import re
from pathlib import Path
from typing import Any


class PackageError(RuntimeError):
    pass


class PackageService:
    MANIFEST = "package.json"

    def create_manifest(self, project: Path, package_id: str | None = None, version: str | None = None) -> dict[str, Any]:
        project = Path(project).resolve()
        if not project.is_dir():
            raise PackageError(f"Package source directory does not exist: {project}")
        files: dict[str, str] = {}
        for path in sorted(project.rglob("*")):
            if not path.is_file() or path.name == self.MANIFEST:
                continue
            if path.is_symlink():
                raise PackageError(f"Symbolic links are not allowed in packages: {path}")
            relative = path.relative_to(project).as_posix()
            if relative.startswith("../") or "/../" in relative:
                raise PackageError(f"Unsafe package path: {relative}")
            files[relative] = self._hash(path)
        manifest = {
            "schema": "control_center.package.v1",
            "id": package_id or project.name,
            "version": version or "0.0.0",
            "files": files,
        }
        self._write_manifest(project, manifest)
        return manifest

    def verify(self, project: Path) -> tuple[bool, list[str]]:
        project = Path(project).resolve()
        path = project / self.MANIFEST
        if not path.is_file():
            return False, ["Package manifest is missing."]
        try:
            manifest = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            return False, [f"Package manifest is invalid: {exc}"]
        if not isinstance(manifest, dict) or manifest.get("schema") != "control_center.package.v1":
            return False, ["Package manifest schema is missing or unsupported."]
        if not isinstance(manifest.get("files"), dict):
            return False, ["Package manifest file hashes are missing or invalid."]
        errors: list[str] = []
        if not str(manifest.get("id", "")).strip():
            errors.append("Package manifest id is missing.")
        if not re.fullmatch(r"\d+\.\d+\.\d+", str(manifest.get("version", ""))):
            errors.append("Package manifest version must use semantic version format.")
        declared = {str(relative) for relative in manifest.get("files", {})}
        for relative, expected in manifest.get("files", {}).items():
            relative = str(relative)
            candidate = project / relative
            try:
                candidate.relative_to(project)
            except ValueError:
                errors.append(f"Unsafe manifest path: {relative}")
                continue
            if Path(relative).is_absolute() or "\\" in relative or relative != Path(relative).as_posix():
                errors.append(f"Manifest path is not normalized: {relative}")
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
                errors.append(f"Invalid SHA-256 hash in manifest: {relative}")
                continue
            if candidate.is_symlink():
                errors.append(f"Symbolic links are not allowed in packages: {relative}")
                continue
            if not candidate.is_file():
                errors.append(f"Missing packaged file: {relative}")
            elif self._hash(candidate) != expected:
                errors.append(f"Hash mismatch: {relative}")
        for candidate in sorted(project.rglob("*")):
            if not candidate.is_file() or candidate.name == self.MANIFEST:
                continue
            relative = candidate.relative_to(project).as_posix()
            if candidate.is_symlink():
                errors.append(f"Symbolic links are not allowed in packages: {relative}")
                continue
            if relative not in declared:
                errors.append(f"Unlisted packaged file: {relative}")
        return not errors, errors

    def export_zip(self, project: Path, destination: Path) -> Path:
        project = Path(project).resolve()
        destination = Path(destination).resolve()
        valid, errors = self.verify(project)
        if not valid:
            raise PackageError("Cannot export invalid package: " + "; ".join(errors))
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(project.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(project).as_posix())
        os.replace(temporary, destination)
        return destination

    def _write_manifest(self, project: Path, manifest: dict[str, Any]) -> None:
        temporary = project / (self.MANIFEST + ".tmp")
        temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(project / self.MANIFEST)

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
