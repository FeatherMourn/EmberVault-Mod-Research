"""Verify the source contract for the EML metadata-only asset API."""
from pathlib import Path
import json
import sys

SOURCE_ROOT = Path(r"H:\enshroudedresearch\external\kfc-parser-source")
SOURCE = SOURCE_ROOT / "crates" / "mod-loader-lua" / "src" / "env" / "game" / "assets.rs"
DEFINITION = SOURCE_ROOT / "crates" / "mod-loader-lua" / "definitions" / "assets" / "manager.lua"
TOKENS = ("get_resource_metadata_by_type", "get_resource_metadata_by_guid")

def main() -> int:
    errors = []
    if not SOURCE.is_file(): errors.append(f"missing Rust source: {SOURCE}")
    if not DEFINITION.is_file(): errors.append(f"missing Lua definition: {DEFINITION}")
    if not errors:
        rust = SOURCE.read_text(encoding="utf-8")
        lua = DEFINITION.read_text(encoding="utf-8")
        for token in TOKENS:
            if rust.count(token) < 2: errors.append(f"Rust registration or implementation is missing: {token}")
            if lua.count(token) < 1: errors.append(f"Lua definition is missing: {token}")
    result = {"valid": not errors, "apis": list(TOKENS), "errors": errors}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
