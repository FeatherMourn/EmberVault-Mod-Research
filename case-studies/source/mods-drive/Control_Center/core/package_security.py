"""Deterministic package lockfiles and provenance verification."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PackageSecurityError(RuntimeError):
    pass


@dataclass(frozen=True)
class LockVerification:
    valid: bool
    errors: tuple[str, ...]


class PackageSecurityService:
    LOCKFILE = "package.lock.json"

    def create_lock(self, package: Path, author: str | None = None, license_name: str | None = None,
                    build_fingerprint: str | None = None) -> Path:
        package = Path(package).resolve()
        manifest_path = package / "mod.json"
        if not manifest_path.is_file():
            raise PackageSecurityError("Package mod.json is missing.")
        files: dict[str, str] = {}
        for path in sorted(package.rglob("*")):
            if not path.is_file() or path.is_symlink() or path.name == self.LOCKFILE:
                continue
            relative = path.relative_to(package).as_posix()
            files[relative] = self._hash(path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        data: dict[str, Any] = {
            "schema": "control_center.package_lock.v1",
            "package_id": str(manifest.get("id", package.name)),
            "version": str(manifest.get("version", "unknown")),
            "author": author if author is not None else manifest.get("author", manifest.get("authors")),
            "license": license_name if license_name is not None else manifest.get("license"),
            "build_fingerprint": build_fingerprint,
            "files": files,
        }
        data["lock_hash"] = self._lock_hash(data)
        destination = package / self.LOCKFILE
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(destination)
        return destination

    def verify(self, package: Path) -> LockVerification:
        package = Path(package).resolve()
        path = package / self.LOCKFILE
        if not path.is_file():
            return LockVerification(False, ("Package lockfile is missing.",))
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            return LockVerification(False, (f"Lockfile is invalid: {exc}",))
        errors: list[str] = []
        if data.get("schema") != "control_center.package_lock.v1":
            errors.append("Unsupported lockfile schema.")
        expected_lock_hash = data.get("lock_hash")
        unsigned = dict(data); unsigned.pop("lock_hash", None)
        if expected_lock_hash != self._lock_hash(unsigned):
            errors.append("Lockfile metadata hash mismatch.")
        listed = data.get("files", {})
        if not isinstance(listed, dict):
            errors.append("Lockfile files must be an object.")
            listed = {}
        for relative, expected in listed.items():
            file_path = package / str(relative)
            try:
                file_path.resolve().relative_to(package)
            except ValueError:
                errors.append(f"Unsafe locked path: {relative}")
                continue
            if not file_path.is_file() or file_path.is_symlink():
                errors.append(f"Missing or symbolic-link locked file: {relative}")
            elif self._hash(file_path) != expected:
                errors.append(f"Locked file hash mismatch: {relative}")
        for file_path in package.rglob("*"):
            if file_path.is_file() and not file_path.is_symlink() and file_path.name != self.LOCKFILE:
                if file_path.relative_to(package).as_posix() not in listed:
                    errors.append(f"Unlisted package file: {file_path.relative_to(package).as_posix()}")
        return LockVerification(not errors, tuple(errors))

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _lock_hash(data: dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
