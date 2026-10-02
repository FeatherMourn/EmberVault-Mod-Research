"""Build one read-only probe for all verified metadata resource families."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    types = [str(item["type"]) for item in policy.get("verified_types", [])]
    if not types:
        raise SystemExit("The metadata policy contains no verified types.")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "src").mkdir()
    lines = ["-- Generated read-only metadata policy probe.", "local PREFIX = '[CC-METADATA-SUITE] '", "local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end", ""]
    for type_name in types:
        encoded = json.dumps(type_name)
        lines.extend([
            f"local TYPE_NAME = {encoded}",
            "log('BEFORE|' .. TYPE_NAME)",
            "local ok, rows = pcall(function() return game.assets.get_resource_metadata_by_type(TYPE_NAME) or {} end)",
            "local count = 0; for _ in pairs(rows or {}) do count = count + 1 end",
            "log('RESULT|' .. TYPE_NAME .. '|ok=' .. tostring(ok) .. '|count=' .. tostring(count))",
            "",
        ])
    lines.append("return {}")
    (args.output / "src" / "mod.lua").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "schema": "control_center.metadata_probe_suite.v1",
        "id": args.output.name,
        "name": "Control Center Safe Metadata Probe Suite",
        "version": "0.1.0",
        "feature_state": "research-only",
        "mode": "read_only_metadata_suite",
        "capabilities": ["patch"],
        "entrypoint": "src/mod.lua",
        "research_build": policy.get("target_build"),
        "verified_types": types,
        "quarantined_types": [item.get("type") for item in policy.get("quarantined_types", [])],
    }
    (args.output / "mod.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Generated metadata probe suite for {len(types)} types: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
