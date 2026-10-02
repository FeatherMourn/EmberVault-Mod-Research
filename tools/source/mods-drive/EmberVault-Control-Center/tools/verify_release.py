"""Verify the required non-Python assets in an EmberVault wheel."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile


REQUIRED = (
    "ui/Main.qml",
    "contracts/catalog.schema.json",
    "contracts/integration-context.schema.json",
    "contracts/promotion-evidence.schema.json",
    "contracts/content-project.schema.json",
    "contracts/knowledge-entry.schema.json",
    "contracts/research-summary.schema.json",
    "contracts/trainer-plan.schema.json",
    "contracts/game-settings.schema.json",
    "contracts/tuning-adapter.schema.json",
    "modules/example/module.json",
    "modules/example/module.py",
    "modules/trainer/module.json",
    "modules/trainer/trainer_stub.py",
    "modules/research/module.json",
    "modules/research/research_stub.py",
    "modules/content-creator/module.json",
    "modules/content-creator/content_stub.py",
    "modules/tuning-audit/module.json",
    "modules/tuning-audit/tuning_stub.py",
    "knowledge/entries.json",
    "packages/example-mod/package.json",
    "adapters/eml-balancing-table.json",
    "packages/eml-tuning-adapter/package.json",
    "packages/eml-tuning-adapter/mod.json",
    "packages/eml-tuning-adapter/mod.lua",
    "templates/module/module.json",
    "templates/module/module.py",
    "templates/module/README.md",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    with zipfile.ZipFile(args.wheel) as archive:
        names = set(archive.namelist())
    missing = [path for path in REQUIRED if not any(name.endswith(".data/data/" + path) for name in names)]
    if missing:
        print("Missing release assets:")
        print("\n".join(missing))
        return 1
    with zipfile.ZipFile(args.wheel) as archive:
        def packaged_path(relative: str) -> str:
            return next(name for name in archive.namelist() if name.endswith(".data/data/" + relative))

        for relative in REQUIRED:
            if relative.endswith(".json"):
                try:
                    json.loads(archive.read(packaged_path(relative)).decode("utf-8"))
                except (UnicodeError, json.JSONDecodeError, KeyError) as exc:
                    print(f"Invalid packaged JSON asset: {relative} ({exc})")
                    return 1
        knowledge = json.loads(archive.read(packaged_path("knowledge/entries.json")).decode("utf-8"))
        if not isinstance(knowledge, list) or not knowledge:
            print("Packaged knowledge catalog must contain at least one entry")
            return 1
    print(f"Release asset verification passed: {len(REQUIRED)} assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
