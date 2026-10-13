"""Versioned, hash-verified offline research bundles."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from typing import Any

BUNDLE_VERSION = 1


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_sqlite(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("research catalog integrity check failed")
    finally:
        connection.close()


def create_bundle(catalog: str | Path, destination: str | Path, notebook: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a deterministic local bundle without changing the catalog."""
    source = Path(catalog)
    target = Path(destination)
    if not source.is_file():
        raise FileNotFoundError(source)
    _check_sqlite(source)
    manifest = {
        "bundle_version": BUNDLE_VERSION,
        "catalog_name": "catalog.sqlite",
        "catalog_sha256": _sha256(source),
        "read_only": True,
        "runtime_approval": False,
    }
    notebook_bytes = None
    if notebook is not None:
        if notebook.get("read_only") is not True or notebook.get("runtime_approval") is not False:
            raise ValueError("only read-only notebooks may be bundled")
        notebook_bytes = (json.dumps(notebook, indent=2, sort_keys=True) + "\n").encode("utf-8")
        manifest["notebook_name"] = "notebook.json"
        manifest["notebook_sha256"] = hashlib.sha256(notebook_bytes).hexdigest()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        manifest_path = Path(directory) / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in (manifest_path, source):
                info = zipfile.ZipInfo(path.name, date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(info, path.read_bytes())
            if notebook_bytes is not None:
                info = zipfile.ZipInfo("notebook.json", date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(info, notebook_bytes)
    return manifest


def verify_bundle(bundle: str | Path) -> dict[str, Any]:
    """Verify bundle structure, catalog hash, and SQLite integrity."""
    path = Path(bundle)
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if not {"manifest.json", "catalog.sqlite"}.issubset(names) or names - {"manifest.json", "catalog.sqlite", "notebook.json"}:
            raise ValueError("research bundle contains unexpected files")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("bundle_version") != BUNDLE_VERSION or manifest.get("read_only") is not True:
            raise ValueError("unsupported or unsafe research bundle")
        with tempfile.TemporaryDirectory() as directory:
            catalog = Path(directory) / "catalog.sqlite"
            catalog.write_bytes(archive.read("catalog.sqlite"))
            if _sha256(catalog) != manifest.get("catalog_sha256"):
                raise ValueError("research bundle catalog hash mismatch")
            _check_sqlite(catalog)
        if "notebook.json" in names:
            if manifest.get("notebook_name") != "notebook.json":
                raise ValueError("research bundle notebook metadata is invalid")
            notebook_bytes = archive.read("notebook.json")
            if hashlib.sha256(notebook_bytes).hexdigest() != manifest.get("notebook_sha256"):
                raise ValueError("research bundle notebook hash mismatch")
            notebook = json.loads(notebook_bytes)
            if notebook.get("read_only") is not True or notebook.get("runtime_approval") is not False:
                raise ValueError("research bundle notebook is not read-only")
    return manifest


def recover_bundle(bundle: str | Path, destination: str | Path, notebook_destination: str | Path | None = None) -> dict[str, Any]:
    """Recover a verified catalog to a caller-selected local destination."""
    manifest = verify_bundle(bundle)
    target = Path(destination)
    if target.exists():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle) as archive:
        target.write_bytes(archive.read("catalog.sqlite"))
        if notebook_destination is not None and "notebook.json" in archive.namelist():
            notebook_target = Path(notebook_destination)
            if notebook_target.exists():
                raise FileExistsError(notebook_target)
            notebook_target.parent.mkdir(parents=True, exist_ok=True)
            notebook_target.write_bytes(archive.read("notebook.json"))
    _check_sqlite(target)
    return manifest
