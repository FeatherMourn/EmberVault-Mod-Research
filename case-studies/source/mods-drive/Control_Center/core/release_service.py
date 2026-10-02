"""Versioned release archives and release-channel metadata."""
from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile
from pathlib import Path
from typing import Any

from .package_service import PackageError, PackageService
from .compatibility import build_satisfies


class ReleaseError(RuntimeError):
    pass


class ReleaseService:
    def __init__(self):
        self.packages = PackageService()

    def build_release(self, project: Path, output_dir: Path, version: str | None = None, channel: str = "stable", compatible_game_builds: list[str] | None = None, notes: list[str] | None = None) -> tuple[Path, Path]:
        project = Path(project).resolve(); output_dir = Path(output_dir).resolve()
        valid, errors = self.packages.verify(project)
        if not valid: raise ReleaseError("Project package is invalid: " + "; ".join(errors))
        try: manifest = json.loads((project / "mod.json").read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc: raise ReleaseError(f"mod.json is invalid: {exc}") from exc
        package_id = str(manifest.get("id", project.name)); version = version or str(manifest.get("version", "0.0.0"))
        if not re.fullmatch(r"\d+\.\d+\.\d+", version): raise ReleaseError("Release version must use semantic version format.")
        if channel not in {"stable", "beta", "nightly"}: raise ReleaseError(f"Unsupported release channel: {channel}")
        output_dir.mkdir(parents=True, exist_ok=True)
        archive = output_dir / f"{package_id}-{version}.zip"
        metadata_path = output_dir / f"{package_id}-{version}.release.json"
        if archive.exists() or metadata_path.exists():
            raise ReleaseError(f"Release already exists: {archive.name}")
        temporary_archive = output_dir / (archive.name + ".tmp")
        temporary_metadata = output_dir / (metadata_path.name + ".tmp")
        try:
            self.packages.export_zip(project, temporary_archive)
            digest = self._hash(temporary_archive)
            archive_name = archive.name
        except (PackageError, OSError) as exc:
            for path in (temporary_archive, temporary_metadata):
                try: path.unlink()
                except OSError: pass
            raise ReleaseError(f"Release archive could not be prepared: {exc}") from exc
        metadata = {
            "schema": "control_center.release.v1", "id": package_id, "version": version, "channel": channel,
            "archive": archive_name, "sha256": digest, "compatible_game_builds": compatible_game_builds or manifest.get("compatible_game_builds", []), "notes": notes or [],
            "feature_state": manifest.get("feature_state", "unspecified"),
            "dependencies": manifest.get("dependencies", []),
            "capabilities": manifest.get("capabilities", []),
        }
        try:
            temporary_metadata.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            os.replace(temporary_archive, archive)
            os.replace(temporary_metadata, metadata_path)
        except OSError as exc:
            for path in (temporary_archive, temporary_metadata, archive):
                try: path.unlink()
                except OSError: pass
            raise ReleaseError(f"Release commit failed: {exc}") from exc
        return archive, metadata_path

    def catalog_releases(self, directory: Path, package_id: str | None = None,
                         channels: set[str] | None = None) -> list[dict[str, Any]]:
        """Return verified local releases, newest version first, without installing them."""
        directory = Path(directory).resolve()
        results: list[dict[str, Any]] = []
        for metadata_path in sorted(directory.glob("*.release.json")) if directory.is_dir() else []:
            try:
                raw = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
                self._validate_metadata(raw)
                if package_id is not None and raw["id"] != package_id:
                    continue
                if channels is not None and raw["channel"] not in channels:
                    continue
                archive = directory / raw["archive"]
                verified = self.verify_release(archive, metadata_path)
                results.append({**verified, "archive_path": str(archive), "metadata_path": str(metadata_path)})
            except (OSError, ValueError, ReleaseError):
                continue
        results.sort(key=lambda item: tuple(int(part) for part in item["version"].split(".")), reverse=True)
        return results

    def verify_release(self, archive: Path, metadata_path: Path, game_build: str | None = None) -> dict[str, Any]:
        archive = Path(archive).resolve(); metadata_path = Path(metadata_path).resolve()
        if not archive.is_file() or not metadata_path.is_file():
            raise ReleaseError("Release archive and metadata are both required.")
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise ReleaseError(f"Release metadata is invalid: {exc}") from exc
        if metadata.get("schema") != "control_center.release.v1": raise ReleaseError("Unsupported release metadata schema.")
        self._validate_metadata(metadata)
        if self._hash(archive) != metadata.get("sha256"): raise ReleaseError("Release archive hash does not match metadata.")
        if metadata.get("archive") != archive.name: raise ReleaseError("Release archive name does not match metadata.")
        try:
            with zipfile.ZipFile(archive) as package:
                names = package.namelist()
                if len(names) != len(set(names)):
                    raise ReleaseError("Release archive contains duplicate entries.")
                for name in names:
                    path = Path(name)
                    if path.is_absolute() or ".." in path.parts:
                        raise ReleaseError(f"Release archive contains an unsafe path: {name}")
                if "package.json" not in names or "mod.json" not in names:
                    raise ReleaseError("Release archive must contain package.json and mod.json.")
        except zipfile.BadZipFile as exc:
            raise ReleaseError(f"Release archive is invalid: {exc}") from exc
        builds = metadata.get("compatible_game_builds", [])
        compatible = build_satisfies(game_build, builds) if game_build else None
        if compatible is False: raise ReleaseError(f"Release is not compatible with game build {game_build}.")
        return {**metadata, "verified": True, "game_build_compatible": compatible}

    def install_release(self, archive: Path, metadata_path: Path, game_dir: Path, game_build: str | None = None,
                        allowed_channels: set[str] | None = None, allow_research: bool = False,
                        allow_downgrade: bool = False) -> dict[str, Any]:
        """Install one verified release through the transactional local-mod installer."""
        verified = self.verify_release(archive, metadata_path, game_build)
        if allowed_channels is not None and verified["channel"] not in allowed_channels:
            raise ReleaseError(f"Release channel '{verified['channel']}' is not enabled for this profile.")
        from .local_mods import LocalModService, LocalModError
        library = LocalModService(Path(game_dir).parent.parent / "EnshroudedModHub")
        package = library.inspect(Path(archive))
        if package.identity != verified["id"] or package.version != verified["version"]:
            raise ReleaseError("Release metadata does not match the package manifest.")
        current_manifest = Path(game_dir) / "mods" / verified["id"] / "mod.json"
        if current_manifest.is_file():
            try:
                current_version = str(json.loads(current_manifest.read_text(encoding="utf-8-sig")).get("version", ""))
            except (OSError, ValueError) as exc:
                raise ReleaseError(f"Installed package manifest is invalid: {exc}") from exc
            if self._version_tuple(verified["version"]) < self._version_tuple(current_version) and not allow_downgrade:
                raise ReleaseError(f"Release {verified['version']} is older than installed version {current_version}; explicit downgrade approval is required.")
        try:
            plan = library.install(package, Path(game_dir), replace=True, allow_research=allow_research)
        except LocalModError as exc:
            raise ReleaseError(f"Verified release could not be installed: {exc}") from exc
        return {**verified, "installed": True, "install_plan": plan}

    @staticmethod
    def _version_tuple(version: str) -> tuple[int, int, int]:
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(version))
        if not match:
            raise ReleaseError(f"Invalid semantic version: {version}")
        return tuple(int(part) for part in match.groups())

    @staticmethod
    def _validate_metadata(metadata: Any) -> None:
        """Reject malformed release records before trusting any artifact fields."""
        if not isinstance(metadata, dict):
            raise ReleaseError("Release metadata must be an object.")
        required = ("id", "version", "channel", "archive", "sha256", "compatible_game_builds", "dependencies", "capabilities")
        missing = [field for field in required if field not in metadata]
        if missing:
            raise ReleaseError("Release metadata is missing: " + ", ".join(missing))
        if not isinstance(metadata["id"], str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", metadata["id"]):
            raise ReleaseError("Release metadata id is invalid.")
        if not isinstance(metadata["version"], str) or not re.fullmatch(r"\d+\.\d+\.\d+", metadata["version"]):
            raise ReleaseError("Release metadata version is invalid.")
        if metadata["channel"] not in {"stable", "beta", "nightly"}:
            raise ReleaseError("Release metadata channel is invalid.")
        if not isinstance(metadata["archive"], str) or not metadata["archive"] or Path(metadata["archive"]).name != metadata["archive"]:
            raise ReleaseError("Release metadata archive name is invalid.")
        if not isinstance(metadata["sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", metadata["sha256"]):
            raise ReleaseError("Release metadata sha256 is invalid.")
        if not isinstance(metadata["compatible_game_builds"], list) or not all(isinstance(item, str) for item in metadata["compatible_game_builds"]):
            raise ReleaseError("Release metadata compatible_game_builds must be a string list.")
        for field in ("dependencies", "capabilities"):
            if not isinstance(metadata[field], list):
                raise ReleaseError(f"Release metadata {field} must be a list.")
        if not all(isinstance(item, (str, dict)) for item in metadata["dependencies"]):
            raise ReleaseError("Release metadata dependencies contain an invalid entry.")
        if not all(isinstance(item, str) and item.strip() for item in metadata["capabilities"]):
            raise ReleaseError("Release metadata capabilities contain an invalid entry.")

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256();
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""): digest.update(block)
        return digest.hexdigest()
