"""Safe import/export helpers for existing Enshrouded mod layouts."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any


class LayoutMigrationError(RuntimeError):
    pass


class ModLayoutMigrationService:
    MANIFEST_NAMES = ("mod.json", "module.json", "package.json", "manifest.json")
    SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules"}
    SKIP_NAMES = {"nexus_api_key.json", "*.eml.log"}

    @staticmethod
    def _safe_id(value: str) -> str:
        result = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
        return result[:80] or "imported_mod"

    def inspect(self, source: Path) -> dict[str, Any]:
        source = Path(source).resolve()
        if not source.is_dir():
            raise LayoutMigrationError(f"Mod layout folder was not found: {source}")
        manifests = []
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise LayoutMigrationError(f"Symbolic links are not allowed in mod layouts: {path}")
            if path.is_file() and path.name in self.MANIFEST_NAMES:
                record: dict[str, Any] = {"path": str(path.relative_to(source))}
                try:
                    payload = json.loads(path.read_text(encoding="utf-8-sig"))
                    if isinstance(payload, dict):
                        record["id"] = payload.get("id") or payload.get("name")
                        record["schema"] = payload.get("schema")
                except (OSError, ValueError):
                    record["parse_error"] = True
                manifests.append(record)
        return {"source": str(source), "manifest_count": len(manifests), "manifests": manifests}

    def import_layout(self, source: Path, destination_root: Path, mod_id: str | None = None) -> Path:
        source = Path(source).resolve(); destination_root = Path(destination_root).resolve()
        inspection = self.inspect(source)
        chosen = mod_id or next((str(item["id"]) for item in inspection["manifests"] if item.get("id")), source.name)
        destination = destination_root / self._safe_id(chosen)
        if destination.exists():
            raise LayoutMigrationError(f"Import destination already exists: {destination}")
        destination.mkdir(parents=True, exist_ok=False)
        copied: list[dict[str, Any]] = []
        try:
            for path in sorted(source.rglob("*")):
                if path.is_symlink():
                    raise LayoutMigrationError(f"Symbolic links are not allowed in mod layouts: {path}")
                if not path.is_file() or any(part in self.SKIP_DIRS for part in path.relative_to(source).parts):
                    continue
                if path.name == "nexus_api_key.json" or path.name.endswith(".eml.log"):
                    continue
                relative = path.relative_to(source)
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                copied.append({"path": str(relative), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
            report = {"schema": "control_center.layout_import.v1", "source": str(source), "mod_id": self._safe_id(chosen), "files": copied, "warnings": ["Imported layout requires validation before activation."]}
            (destination / "control_center_import.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            return destination
        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise

    def export_layout(self, source: Path, archive: Path) -> Path:
        source = Path(source).resolve(); archive = Path(archive).resolve()
        if not source.is_dir():
            raise LayoutMigrationError(f"Mod layout folder was not found: {source}")
        if archive.exists():
            raise LayoutMigrationError(f"Archive already exists: {archive}")
        archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
            for path in sorted(source.rglob("*")):
                if path.is_symlink():
                    raise LayoutMigrationError(f"Symbolic links are not allowed in mod layouts: {path}")
                if path.is_file() and path.name != "nexus_api_key.json" and not path.name.endswith(".eml.log"):
                    zipped.write(path, path.relative_to(source).as_posix())
        return archive
