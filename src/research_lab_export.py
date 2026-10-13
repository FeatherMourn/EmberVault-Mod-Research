"""Versioned, hash-verified export bundles for read-only Lab snapshots."""
from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def create_snapshot_bundle(snapshot: dict[str, Any], destination: Path,
                          analyzer_runs: list[dict[str, Any]] | tuple[dict[str, Any], ...] = ()) -> None:
    """Write a recoverable snapshot bundle without changing the source snapshot."""
    if snapshot.get("read_only") is not True or snapshot.get("runtime_approval") is not False:
        raise ValueError("Lab snapshot must be read-only and runtime-unapproved")
    payload = _canonical(snapshot)
    runs_payload = _canonical({"schema_version": 1, "runs": list(analyzer_runs),
                               "read_only": True, "runtime_approval": False})
    manifest = {"schema_version": 1, "snapshot_sha256": hashlib.sha256(payload).hexdigest(),
                "analyzer_runs_sha256": hashlib.sha256(runs_payload).hexdigest(),
                "read_only": True, "runtime_approval": False, "recovery": "verify-before-extract"}
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", _canonical(manifest))
            archive.writestr("snapshot.json", payload)
            if analyzer_runs:
                archive.writestr("analyzer-runs.json", runs_payload)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def verify_snapshot_bundle(bundle: Path) -> dict[str, Any]:
    """Verify a snapshot bundle and return its manifest without extracting it."""
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        payload = archive.read("snapshot.json")
        runs_payload = archive.read("analyzer-runs.json") if "analyzer-runs.json" in archive.namelist() else None
    if manifest.get("snapshot_sha256") != hashlib.sha256(payload).hexdigest():
        raise ValueError("snapshot bundle hash mismatch")
    if runs_payload is not None and manifest.get("analyzer_runs_sha256") != hashlib.sha256(runs_payload).hexdigest():
        raise ValueError("analyzer run report hash mismatch")
    if manifest.get("read_only") is not True or manifest.get("runtime_approval") is not False:
        raise ValueError("snapshot bundle safety metadata is invalid")
    return manifest


def recover_snapshot_bundle(bundle: Path, destination: Path) -> dict[str, Any]:
    """Verify then atomically recover a snapshot JSON file."""
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        payload = archive.read("snapshot.json")
        runs_payload = archive.read("analyzer-runs.json") if "analyzer-runs.json" in archive.namelist() else None
    if manifest.get("snapshot_sha256") != hashlib.sha256(payload).hexdigest():
        raise ValueError("snapshot bundle hash mismatch")
    if runs_payload is not None and manifest.get("analyzer_runs_sha256") != hashlib.sha256(runs_payload).hexdigest():
        raise ValueError("analyzer run report hash mismatch")
    snapshot = json.loads(payload)
    if snapshot.get("read_only") is not True or snapshot.get("runtime_approval") is not False:
        raise ValueError("recovered snapshot safety metadata is invalid")
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".tmp", delete=False, mode="wb") as handle:
        temporary = Path(handle.name)
        handle.write(payload)
    try:
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    result = {"destination": str(target), "snapshot_sha256": manifest["snapshot_sha256"],
              "read_only": True, "runtime_approval": False}
    if runs_payload is not None:
        runs_target = target.with_name(target.stem + ".analyzer-runs.json")
        runs_target.write_bytes(runs_payload)
        result["analyzer_runs_destination"] = str(runs_target)
        result["analyzer_runs_sha256"] = manifest["analyzer_runs_sha256"]
    return result


def prune_snapshot_bundles(directory: Path, *, keep: int = 5) -> dict[str, Any]:
    """Retain the newest Lab zip bundles and ignore unrelated files."""
    if keep < 1:
        raise ValueError("keep must be positive")
    root = Path(directory)
    bundles = sorted((path for path in root.glob("*.zip") if path.is_file()),
                     key=lambda path: (path.stat().st_mtime_ns, path.name), reverse=True)
    removed = []
    for path in bundles[keep:]:
        path.unlink()
        removed.append(path.name)
    return {"directory": str(root), "kept": [path.name for path in bundles[:keep]],
            "removed": sorted(removed), "read_only": True, "runtime_approval": False}
