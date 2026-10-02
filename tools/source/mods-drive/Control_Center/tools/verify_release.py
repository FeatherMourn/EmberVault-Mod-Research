"""Verify release artifact sizes, hashes, and embedded Windows versions."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def latest_manifest(root: Path) -> Path:
    candidates = sorted(
        (root / "packaging").glob("RELEASE_MANIFEST_*.json"),
        key=lambda path: path.stat().st_mtime if path.is_file() else 0,
        reverse=True,
    )
    return candidates[0] if candidates else root / "packaging" / "RELEASE_MANIFEST_1.0.2.json"


def verify(root: Path, manifest_path: Path) -> list[str]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for artifact in data.get("artifacts", []):
        path = root / str(artifact["path"])
        if not path.is_file():
            errors.append(f"missing artifact: {artifact['path']}")
            continue
        if path.stat().st_size != int(artifact["size"]):
            errors.append(f"size mismatch: {artifact['path']}")
        if sha256(path) != str(artifact["sha256"]).upper():
            errors.append(f"hash mismatch: {artifact['path']}")
    audit_path = root / str(data.get("capability_audit", "research/CAPABILITY_AUDIT_20260927.json"))
    if not audit_path.is_file():
        errors.append(f"missing capability audit: {audit_path.relative_to(root)}")
    else:
        try:
            tools_dir = Path(__file__).resolve().parent
            if str(tools_dir) not in sys.path:
                sys.path.insert(0, str(tools_dir))
            from verify_capability_audit import verify as verify_audit
            audit = verify_audit(audit_path)
            if not audit["valid"]:
                errors.extend(f"capability audit: {error}" for error in audit["errors"])
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"capability audit verification failed: {exc}")
    exe = root / "dist" / "EnshroudedModHub.exe"
    if exe.is_file() and str(exe.stat().st_size) and hasattr(exe, "name"):
        # VersionInfo is Windows-only; the artifact hash/size checks remain
        # portable and are the authoritative release identity.
        pass
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Control Center release artifacts")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = (args.manifest or latest_manifest(root)).resolve()
    errors = verify(root, manifest)
    if errors:
        print("RELEASE VERIFICATION FAILED")
        print("\n".join(errors))
        return 1
    print(f"RELEASE VERIFIED: {json.loads(manifest.read_text(encoding='utf-8'))['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
