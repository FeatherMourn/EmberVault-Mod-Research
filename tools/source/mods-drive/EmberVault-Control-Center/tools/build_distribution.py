"""Build reviewable portable Windows and Linux release bundles."""
from __future__ import annotations
import argparse, hashlib, json, shutil, zipfile
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    if not args.wheel.is_file() or args.wheel.suffix != ".whl":
        raise SystemExit("A built wheel is required")
    args.destination.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(args.wheel.read_bytes()).hexdigest()
    for platform in ("windows", "linux"):
        bundle = args.destination / f"embervault-control-center-1.0.0rc1-{platform}.zip"
        manifest = {"schema_version": 1, "version": "1.0.0rc1", "channel": "stable",
                    "platform": platform, "wheel": args.wheel.name, "sha256": digest,
                    "application_state": "release-candidate",
                    "live_mutation_supported": False, "data_preserving_uninstall": True}
        with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(args.wheel, args.wheel.name)
            archive.writestr("release-manifest.json", json.dumps(manifest, indent=2) + "\n")
            archive.writestr("INSTALL.txt", "Install the included wheel in an isolated environment.\n"
                            "This release candidate does not claim unsupported live gameplay mutation.\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
