"""Verify portable release bundles without installing or mutating user data."""
from __future__ import annotations
import argparse, json, zipfile
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    for platform in ("windows", "linux"):
        path = args.directory / f"embervault-control-center-1.0.0rc1-{platform}.zip"
        with zipfile.ZipFile(path) as archive:
            manifest = json.loads(archive.read("release-manifest.json"))
            if manifest["platform"] != platform or manifest["version"] != "1.0.0rc1":
                raise ValueError(f"Invalid {platform} release manifest")
            if manifest["live_mutation_supported"] is not False or manifest["data_preserving_uninstall"] is not True:
                raise ValueError("Release safety flags are invalid")
            if not any(name.endswith(".whl") for name in archive.namelist()):
                raise ValueError("Release bundle does not contain a wheel")
    print("Distribution verification passed: Windows and Linux bundles")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
