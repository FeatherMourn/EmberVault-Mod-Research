"""Create self-contained, validator-ready EML/KFC content projects."""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from .content_identity import ContentIdentityService
from .content_validation import ContentProjectValidator
from .package_service import PackageService
from .sdk import DeveloperSdk, SdkError
from .localization import LocalizationService


class ContentProjectError(RuntimeError):
    pass


class ContentProjectGenerator:
    """Generate a reversible project without modifying the game installation."""

    def __init__(self, base_dir: Path, identity_registry_path: Path | None = None):
        self.base_dir = Path(base_dir)
        self.template_dir = self.base_dir / "research" / "runtime"
        self.identity = ContentIdentityService(identity_registry_path or (self.base_dir / "profiles" / "content-identities.json"))
        self.validator = ContentProjectValidator()
        self.packages = PackageService()
        self.sdk = DeveloperSdk(self.base_dir)
        self.localization = LocalizationService()

    def create(
        self,
        destination: Path,
        namespace: str,
        name: str,
        author: str,
        project_id: str | None = None,
        version: str = "0.1.0",
        overwrite: bool = False,
    ) -> Path:
        destination = Path(destination).resolve()
        existed = destination.exists()
        identity_path = self.identity.registry_path
        old_identity = identity_path.read_bytes() if identity_path.is_file() else None
        try:
            return self._create_unchecked(destination, namespace, name, author, project_id, version, overwrite)
        except Exception:
            try:
                if not existed and destination.exists():
                    shutil.rmtree(destination)
                if old_identity is None:
                    if identity_path.exists(): identity_path.unlink()
                else:
                    identity_path.write_bytes(old_identity)
                self.identity._data = self.identity._load()
            except OSError:
                pass
            raise

    def _create_unchecked(
        self,
        destination: Path,
        namespace: str,
        name: str,
        author: str,
        project_id: str | None = None,
        version: str = "0.1.0",
        overwrite: bool = False,
    ) -> Path:
        destination = Path(destination).resolve()
        namespace = self.identity.validate_namespace(namespace)
        project_id = self._slug(project_id or name)
        name = str(name).strip()
        author = str(author).strip()
        if not name or not author:
            raise ContentProjectError("Project name and author are required.")
        if not re.fullmatch(r"\d+\.\d+\.\d+", version):
            raise ContentProjectError("Version must use semantic version format, for example 0.1.0.")
        if destination.exists() and any(destination.iterdir()) and not overwrite:
            raise ContentProjectError(f"Refusing to overwrite non-empty project directory: {destination}")

        destination.mkdir(parents=True, exist_ok=True)
        src = destination / "src"
        content = destination / "content"
        src.mkdir(exist_ok=True)
        content.mkdir(exist_ok=True)
        for asset_kind in ("icons", "textures", "models", "audio"):
            (destination / "assets" / asset_kind).mkdir(parents=True, exist_ok=True)
        identity = self.identity.identity(namespace, project_id)
        self.identity.claim(identity, author)

        manifest = {
            "id": project_id,
            "namespace": namespace,
            "name": name,
            "version": version,
            "author": author,
            "loader": "EML",
            "feature_state": "research-only",
            "entrypoint": "src/mod.lua",
            # EML validates this field against its loader-level capability
            # enum. Control Center-specific features belong in metadata below.
            "capabilities": ["patch"],
            "control_center_capabilities": [
                "runtime_resource_registration",
                "content_validation",
                "localization_payload",
                "asset_dependency_tracking",
                "template_graph_planning",
            ],
            "dependencies": [],
            "compatible_game_builds": [],
            "required_loader_api": "assets.register_resource",
            "content": [],
            "generated_by": "Enshrouded Control Center",
            "identity": {"numeric_id": identity.numeric_id, "guid": identity.guid},
        }
        self._write_json(destination / "mod.json", manifest)
        self._write_json(content / "content.json", {"schema": "control_center.content.v1", "namespace": namespace, "entries": []})
        self._write_json(content / "localization.json", {
            "schema": "control_center.localization.v1",
            "namespace": namespace,
            "default_language": "en",
            "feature_state": "research-only",
            "entries": {},
        })
        self._write_json(destination / "assets.json", {"schema": "control_center.assets.v1", "assets": []})
        self._write_text(src / "mod.lua", self._starter_lua(namespace, project_id))
        try:
            self.sdk.package_helper(destination)
        except (OSError, SdkError) as exc:
            raise ContentProjectError(f"Reusable KFC helper could not be packaged: {exc}") from exc
        self.localization.save_lua_payload(self.localization.build(namespace, {}), src / "localization_payload.lua")
        self._write_text(destination / "README.md", self._readme(name, namespace, project_id))
        self.packages.create_manifest(destination, project_id, version)
        report = self.validator.validate(destination)
        if not report.valid:
            raise ContentProjectError("Generated project did not validate: " + "; ".join(issue.message for issue in report.issues))
        return destination

    def import_resource(self, project: Path, source: Path, resource_type: str, slug: str | None = None) -> dict[str, Any]:
        """Import one extracted JSON resource with identity and rollback safety."""
        project = Path(project).resolve()
        source = Path(source).resolve()
        if not source.is_file() or source.is_symlink():
            raise ContentProjectError("Resource source must be a regular file.")
        if source.suffix.lower() != ".json":
            raise ContentProjectError("Only JSON resources can be imported into a content project.")
        try:
            data = json.loads(source.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise ContentProjectError(f"Resource JSON is invalid: {exc}") from exc
        if not isinstance(data, dict):
            raise ContentProjectError("Resource JSON must be an object.")
        manifest_path = project / "mod.json"
        if not manifest_path.is_file():
            raise ContentProjectError("Content project mod.json is missing.")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise ContentProjectError(f"Project manifest is invalid: {exc}") from exc
        namespace = str(manifest.get("namespace", "")).strip()
        if not namespace:
            raise ContentProjectError("Project namespace is required for resource identity.")
        resource_type = str(resource_type).strip()
        folder = resource_type.split("::")[-1]
        folder = re.sub(r"[^A-Za-z0-9_.-]+", "_", folder).strip("_.")
        if not folder:
            raise ContentProjectError("Resource type is required.")
        identity_path = self.identity.registry_path
        old_identity = identity_path.read_bytes() if identity_path.is_file() else None
        identity = self.identity.identity(namespace, slug or source.stem)
        destination = project / "content" / "resources" / folder / source.name
        if destination.exists():
            raise ContentProjectError(f"Imported resource already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        old_manifest = manifest_path.read_bytes()
        package_path = project / self.packages.MANIFEST
        old_package = package_path.read_bytes() if package_path.is_file() else None
        relative = destination.relative_to(project).as_posix()
        entry = {"id": f"{namespace}:{identity.slug}", "numeric_id": identity.numeric_id,
                 "guid": identity.guid, "resource_type": resource_type, "path": relative}
        entries = manifest.setdefault("content", [])
        if not isinstance(entries, list):
            raise ContentProjectError("Project manifest content must be a list.")
        if any(isinstance(item, dict) and item.get("id") == entry["id"] for item in entries):
            raise ContentProjectError(f"Content identity already exists: {entry['id']}")
        try:
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            shutil.copy2(source, temporary)
            os.replace(temporary, destination)
            entries.append(entry)
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            self.packages.create_manifest(project, str(manifest.get("id", project.name)), str(manifest.get("version", "0.0.0")))
            report = self.validator.validate(project)
            if not report.valid:
                raise ContentProjectError("Imported resource failed validation: " + "; ".join(issue.message for issue in report.issues))
        except Exception:
            try:
                if destination.exists(): destination.unlink()
                manifest_path.write_bytes(old_manifest)
                if old_package is None:
                    if package_path.exists(): package_path.unlink()
                else:
                    package_path.write_bytes(old_package)
                if old_identity is None:
                    if identity_path.exists(): identity_path.unlink()
                else:
                    identity_path.write_bytes(old_identity)
                self.identity._data = self.identity._load()
            except OSError:
                pass
            raise
        return entry

    def import_icon(self, project: Path, source: Path, slug: str | None = None) -> dict[str, Any]:
        """Import a validated PNG icon using the canonical asset manifest contract."""
        from .asset_service import AssetError, AssetService
        project = Path(project).resolve(); source = Path(source).resolve()
        if source.suffix.lower() != ".png":
            raise ContentProjectError("Icon source must be a PNG file.")
        try:
            if source.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                raise ContentProjectError("Icon does not contain a valid PNG signature.")
        except OSError as exc:
            raise ContentProjectError(f"Icon could not be read: {exc}") from exc
        manifest_path = project / "mod.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise ContentProjectError(f"Project manifest is invalid: {exc}") from exc
        namespace = str(manifest.get("namespace", "")).strip()
        if not namespace:
            raise ContentProjectError("Project namespace is required for icon identity.")
        identity = self.identity.identity(namespace, slug or source.stem)
        assets_path = project / "assets.json"
        package_path = project / self.packages.MANIFEST
        old_assets = assets_path.read_bytes()
        old_package = package_path.read_bytes() if package_path.is_file() else None
        try:
            destination = AssetService().import_file(source, project, "icons")
        except AssetError as exc:
            raise ContentProjectError(str(exc)) from exc
        entry = next(item for item in json.loads((project / "assets.json").read_text(encoding="utf-8"))["assets"]
                     if item.get("path") == destination.relative_to(project).as_posix())
        entry.update({"id": f"{namespace}:{identity.slug}", "guid": identity.guid})
        assets_path = project / "assets.json"
        assets = json.loads(assets_path.read_text(encoding="utf-8"))
        for item in assets["assets"]:
            if item.get("path") == entry["path"]:
                item.update(entry)
        try:
            assets_path.write_text(json.dumps(assets, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            self.packages.create_manifest(project, str(manifest.get("id", project.name)), str(manifest.get("version", "0.0.0")))
            report = self.validator.validate(project)
            if not report.valid:
                raise ContentProjectError("Imported icon failed validation: " + "; ".join(issue.message for issue in report.issues))
        except Exception:
            try:
                if destination.exists(): destination.unlink()
                assets_path.write_bytes(old_assets)
                if old_package is None:
                    if package_path.exists(): package_path.unlink()
                else:
                    package_path.write_bytes(old_package)
            except OSError:
                pass
            raise
        return entry

    @staticmethod
    def _slug(value: str) -> str:
        value = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value).strip()).strip("_").lower()
        if not value:
            raise ContentProjectError("Project ID cannot be empty.")
        return value[:64]

    @staticmethod
    def _write_json(path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @staticmethod
    def _write_text(path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")

    @staticmethod
    def _starter_lua(namespace: str, project_id: str) -> str:
        return f"""-- {project_id}: generated EML/KFC content project
-- Namespace: {namespace}
-- This starter is intentionally research-only until donor schemas are validated.
local kfc = require('kfc_content_registry')
local Module = {{}}

function Module.OnInit(config, context)
    context.Log('{project_id}: project loaded; no resources registered yet.')
    -- Add donor-specific cloning here only after validating the staged project.
    -- Use kfc.clone_resource and kfc.clone_recipe_set for the known safe paths.
end

return Module
"""

    @staticmethod
    def _readme(name: str, namespace: str, project_id: str) -> str:
        return f"""# {name}

Control Center content project: `{project_id}`  
Namespace: `{namespace}`

This project is generated for EML runtime registration. It is research-only by
default. Validate donor resources and the generated package before enabling it.

## Layout

- `mod.json` — module manifest and capabilities.
- `src/mod.lua` — runtime entry point.
- `src/kfc_content_registry.lua` — packaged reusable registration helper.
- `src/kfc_localization_registry.lua` — research-only binary localization registry helper.
- `src/localization_payload.lua` — deterministic custom localization payload scaffold.
- `content/content.json` — content entries to be added by the author.
- `assets/icons/` — validated PNG icons imported through Content Studio.
- `assets.json` — hashed asset inventory and reference metadata.

Use Content Studio's **Import Custom Icon** action (or
`ContentProjectGenerator.import_icon`) to add an icon safely. Packaging an icon
only proves that the project contains a valid, integrity-tracked PNG; assigning
it to a live `keen::ItemInfo.iconImage` and confirming visible rendering remains
build-specific research work and must be verified with an EML log plus fresh
in-game evidence.

The generator does not alter the vanilla game installation.
"""
