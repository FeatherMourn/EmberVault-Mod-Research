"""Safe project-local asset import and manifest management."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any


class AssetError(RuntimeError):
    pass


ALLOWED_EXTENSIONS = {
    "icons": {".png", ".jpg", ".jpeg", ".webp"},
    "textures": {".png", ".jpg", ".jpeg", ".webp", ".tga"},
    "models": {".fbx", ".gltf", ".glb", ".obj"},
    "audio": {".wav", ".ogg", ".mp3"},
}

RUNTIME_STATUS = {
    "icons": "packaged",
    "textures": "packaged",
    "models": "packaged-unverified-engine-import",
    "audio": "packaged-unverified-engine-import",
}


class AssetService:
    MANIFEST = "assets.json"

    def import_file(self, source: Path, project: Path, kind: str, name: str | None = None,
                    max_bytes: int = 256 * 1024 * 1024, provenance: dict[str, Any] | None = None) -> Path:
        source = Path(source).resolve(); project = Path(project).resolve(); kind = str(kind).lower()
        if kind not in ALLOWED_EXTENSIONS: raise AssetError(f"Unsupported asset kind: {kind}")
        if not source.is_file() or source.is_symlink(): raise AssetError("Source asset must be a regular file.")
        if source.suffix.lower() not in ALLOWED_EXTENSIONS[kind]: raise AssetError(f"Unsupported {kind} extension: {source.suffix}")
        if source.stat().st_size > max_bytes: raise AssetError("Asset exceeds the configured size limit.")
        provenance = self._validate_provenance(provenance)
        self._validate_format(source, kind)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name or source.name)
        if not safe_name or safe_name in {".", ".."}: raise AssetError("Invalid asset name.")
        destination = project / "assets" / kind / safe_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists(): raise AssetError(f"Asset already exists: {destination}")
        manifest_path = project / self.MANIFEST
        old_manifest = manifest_path.read_bytes() if manifest_path.is_file() else None
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        try:
            shutil.copy2(source, temporary); os.replace(temporary, destination)
            manifest = self._load(project)
            entry = {"path": destination.relative_to(project).as_posix(), "kind": kind, "source_name": source.name,
                     "sha256": self._hash(destination), "size": destination.stat().st_size,
                     "runtime_status": RUNTIME_STATUS[kind]}
            if provenance:
                entry["provenance"] = provenance
            manifest.setdefault("assets", []).append(entry)
            self._save(project, manifest)
        except Exception as exc:
            try:
                if temporary.exists(): temporary.unlink()
                if destination.exists(): destination.unlink()
                if old_manifest is None:
                    if manifest_path.exists(): manifest_path.unlink()
                else:
                    manifest_path.write_bytes(old_manifest)
            except OSError:
                pass
            if isinstance(exc, AssetError):
                raise
            raise AssetError(f"Asset import could not be committed: {exc}") from exc
        return destination

    def verify(self, project: Path) -> tuple[bool, list[str]]:
        project = Path(project).resolve(); manifest = self._load(project); errors: list[str] = []
        entries = manifest.get("assets", [])
        if not isinstance(entries, list):
            return False, ["Asset manifest assets field must be a list."]
        listed: set[str] = set()
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"Asset entry {index} must be an object.")
                continue
            relative = str(entry.get("path", "")); path = project / relative
            try: path.relative_to(project)
            except ValueError: errors.append(f"Unsafe asset path: {relative}"); continue
            normalized = path.relative_to(project).as_posix()
            if normalized in listed:
                errors.append(f"Duplicate asset path: {relative}")
            listed.add(normalized)
            kind = str(entry.get("kind", "")).lower()
            if kind not in ALLOWED_EXTENSIONS:
                errors.append(f"Unsupported asset kind in manifest: {kind}")
            elif path.suffix.lower() not in ALLOWED_EXTENSIONS[kind]:
                errors.append(f"Asset extension does not match kind: {relative}")
            if entry.get("runtime_status") != RUNTIME_STATUS.get(kind):
                errors.append(f"Asset runtime status is missing or incorrect: {relative}")
            try:
                self._validate_provenance(entry.get("provenance"))
            except AssetError as exc:
                errors.append(f"Asset provenance is invalid: {relative} ({exc})")
            resolved = path.resolve()
            try: resolved.relative_to(project)
            except ValueError: errors.append(f"Asset resolves outside project: {relative}"); continue
            if path.is_symlink() or not path.is_file():
                errors.append(f"Missing or symbolic-link asset: {relative}")
            else:
                try:
                    self._validate_format(path, kind)
                except AssetError as exc:
                    errors.append(f"Asset format is invalid: {relative} ({exc})")
                if self._hash(path) != entry.get("sha256"):
                    errors.append(f"Asset hash mismatch: {relative}")
                if entry.get("size") != path.stat().st_size:
                    errors.append(f"Asset size mismatch: {relative}")
        assets_root = project / "assets"
        if assets_root.is_dir():
            for path in assets_root.rglob("*"):
                if path.is_file() and path.relative_to(project).as_posix() not in listed:
                    errors.append(f"Unlisted asset file: {path.relative_to(project).as_posix()}")
        seen_references: set[tuple[str, str, str, str]] = set()
        bound_fields: dict[tuple[str, str, str], str] = {}
        for index, reference in enumerate(manifest.get("references", [])):
            if not isinstance(reference, dict):
                errors.append(f"Asset reference {index} must be an object.")
                continue
            target = str(reference.get("asset", ""))
            if target not in listed:
                errors.append(f"Asset reference points to an unlisted asset: {target}")
            if not str(reference.get("resource_type", "")).strip() or not str(reference.get("field", "")).strip():
                errors.append(f"Asset reference {index} requires resource_type and field.")
            signature = (target, str(reference.get("resource_type", "")).strip(),
                         str(reference.get("field", "")).strip(), str(reference.get("resource_id", "")).strip())
            if signature in seen_references:
                errors.append(f"Duplicate asset reference: {target}")
            seen_references.add(signature)
            resource_id = signature[3]
            field_key = (signature[1], signature[2], resource_id)
            if resource_id and field_key in bound_fields and bound_fields[field_key] != target:
                errors.append(f"Resource field is bound to multiple assets: {resource_id}")
            elif resource_id:
                bound_fields[field_key] = target
        return not errors, errors

    def register_reference(self, project: Path, asset: Path | str, resource_type: str, field: str,
                           resource_id: str | None = None) -> dict[str, Any]:
        """Record an intended resource-field consumer without claiming engine import."""
        project = Path(project).resolve()
        resource_type = str(resource_type).strip()
        field = str(field).strip()
        if not resource_type or not field:
            raise AssetError("Asset references require resource_type and field.")
        manifest = self._load(project)
        relative = Path(asset).as_posix() if isinstance(asset, str) else Path(asset).resolve().relative_to(project).as_posix()
        if not any(entry.get("path") == relative for entry in manifest.get("assets", []) if isinstance(entry, dict)):
            raise AssetError(f"Asset is not listed in the manifest: {relative}")
        normalized_id = str(resource_id).strip() if resource_id is not None else ""
        for existing in manifest.get("references", []):
            if not isinstance(existing, dict):
                continue
            if (normalized_id and existing.get("resource_id") == normalized_id
                    and existing.get("resource_type") == resource_type and existing.get("field") == field
                    and existing.get("asset") != relative):
                raise AssetError("Resource field is already bound to a different asset.")
            if (existing.get("asset") == relative and existing.get("resource_type") == resource_type
                    and existing.get("field") == field and str(existing.get("resource_id", "")) == normalized_id):
                raise AssetError("Equivalent asset reference is already registered.")
        reference = {"asset": relative, "resource_type": resource_type, "field": field,
                     "status": "reference-only"}
        if normalized_id:
            reference["resource_id"] = normalized_id
        manifest.setdefault("references", []).append(reference)
        self._save(project, manifest)
        return reference

    @staticmethod
    def _validate_provenance(value: dict[str, Any] | None) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise AssetError("provenance must be an object")
        allowed = {"source", "license", "author", "attribution", "url", "notes"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise AssetError("unsupported provenance fields: " + ", ".join(unknown))
        normalized = {}
        for key, item in value.items():
            if not isinstance(item, str) or not item.strip():
                raise AssetError(f"provenance.{key} must be a non-empty string")
            normalized[key] = item.strip()
        return normalized

    @staticmethod
    def _validate_format(path: Path, kind: str) -> None:
        """Perform cheap container checks without pretending to import engine assets."""
        if kind != "models":
            return
        suffix = path.suffix.lower()
        if suffix == ".gltf":
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeDecodeError, ValueError) as exc:
                raise AssetError(f"gltf JSON is invalid: {exc}") from exc
            if not isinstance(data, dict) or not isinstance(data.get("asset"), dict) or not data["asset"].get("version"):
                raise AssetError("gltf asset.version is required")
        elif suffix == ".glb":
            try:
                header = path.read_bytes()[:12]
            except OSError as exc:
                raise AssetError(f"glb could not be read: {exc}") from exc
            if len(header) < 12 or header[:4] != b"glTF" or int.from_bytes(header[4:8], "little") != 2:
                raise AssetError("glb header is invalid")
        elif suffix == ".obj":
            try:
                if not any(line.lstrip().startswith(("v ", "f ")) for line in path.read_text(errors="replace").splitlines()):
                    raise AssetError("obj contains no vertex or face records")
            except OSError as exc:
                raise AssetError(f"obj could not be read: {exc}") from exc

    def _load(self, project: Path) -> dict[str, Any]:
        path = project / self.MANIFEST
        if not path.is_file(): return {"schema": "control_center.assets.v1", "assets": []}
        try: data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc: raise AssetError(f"Asset manifest is invalid: {exc}") from exc
        if not isinstance(data, dict) or data.get("schema") != "control_center.assets.v1": raise AssetError("Unsupported asset manifest schema.")
        return data

    def _save(self, project: Path, data: dict[str, Any]) -> None:
        temporary = project / (self.MANIFEST + ".tmp")
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"); os.replace(temporary, project / self.MANIFEST)

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256();
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""): digest.update(block)
        return digest.hexdigest()
