"""Collect a read-only snapshot for tuning-adapter review."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


CONFIG_FILES = {
    "loot_and_chests": "src/Config/loot_and_chests.lua",
    "progression_balancing": "src/Config/progression_balancing.lua",
    "survival_qol": "src/Config/survival_qol.lua",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_keys(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return sorted(set(re.findall(r"\[\"([A-Za-z0-9_]+)\"\]\s*=", text)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game_root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    mod_root = args.game_root / "mods" / "enshrouded_mod_hub"
    manifest = mod_root / "mod.json"
    if not manifest.is_file():
        raise SystemExit(f"Expected Mod Hub manifest was not found: {manifest}")

    mod = json.loads(manifest.read_text(encoding="utf-8"))
    files = []
    for name, relative in CONFIG_FILES.items():
        path = mod_root / relative
        if path.is_file():
            files.append({
                "config_id": name,
                "relative_path": relative,
                "sha256": sha256(path),
                "keys": extract_keys(path),
            })

    loader_log = args.game_root / "shroudtopia.log"
    result = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "game_root_name": args.game_root.name,
        "mod": {
            "id": mod.get("id"),
            "name": mod.get("name"),
            "version": mod.get("version"),
            "entrypoint": mod.get("entrypoint"),
        },
        "loader_log": {
            "present": loader_log.is_file(),
            "sha256": sha256(loader_log) if loader_log.is_file() else None,
        },
        "config_files": files,
        "mutation_performed": False,
        "feature_state": "experimental",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
