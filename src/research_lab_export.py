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


def create_snapshot_bundle(snapshot: dict[str, Any], destination: Path) -> None:
    """Write a recoverable snapshot bundle without changing the source snapshot."""
    if snapshot.get("read_only") is not True or snapshot.get("runtime_approval") is not False:
        raise ValueError("Lab snapshot must be read-only and runtime-unapproved")
    payload = _canonical(snapshot)
    manifest = {"schema_version": 1, "snapshot_sha256": hashlib.sha256(payload).hexdigest(),
                "read_only": True, "runtime_approval": False, "recovery": "verify-before-extract"}
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", _canonical(manifest))
            archive.writestr("snapshot.json", payload)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def verify_snapshot_bundle(bundle: Path) -> dict[str, Any]:
    """Verify a snapshot bundle and return its manifest without extracting it."""
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        payload = archive.read("snapshot.json")
    if manifest.get("snapshot_sha256") != hashlib.sha256(payload).hexdigest():
        raise ValueError("snapshot bundle hash mismatch")
    if manifest.get("read_only") is not True or manifest.get("runtime_approval") is not False:
        raise ValueError("snapshot bundle safety metadata is invalid")
    return manifest
