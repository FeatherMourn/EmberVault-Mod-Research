"""Generate a minimal localization-collection transition probe."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--locale", action="append", default=["En_Us"])
    args = parser.parse_args()
    locales = tuple(dict.fromkeys(item.strip() for item in args.locale if item.strip()))
    if not locales:
        parser.error("at least one locale is required")
    lua_locales = "{" + ", ".join(json.dumps(locale) for locale in locales) + "}"
    source = f'''local registry = require('kfc_localization_registry')
local function log(kind, value) print('[CC-LOCALIZATION-COLLECTION] ' .. kind .. '|' .. tostring(value or '')) end
log('START', 'locales={','.join(locales)}')
local tag_ok, tag = pcall(function()
    return registry.register_tag('Control Center Collection Probe', 'Collection transition probe')
end)
log('TAG', 'ok=' .. tostring(tag_ok) .. '|result=' .. tostring(tag_ok and tag and tag.guid or tag))
if not tag_ok then return {{}} end
log('BEFORE_COLLECTION', 'tag_registered=true')
local collection_ok, collection = pcall(function()
    return registry.register({{['Control Center Collection Probe'] = {{En_Us = 'Control Center Collection Probe'}}}}, '8b1e4f67-2a9d-5c30-b8e1-4d7f6a2c9013', 'En_Us', {lua_locales})
end)
log('COLLECTION', 'ok=' .. tostring(collection_ok) .. '|result=' .. tostring(collection_ok and collection and collection.guid or collection))
log('AFTER_COLLECTION', 'returned=true')
local ok_items, items = pcall(function() return game.assets.get_resources_by_type('keen::ItemInfo') or {{}} end)
log('AFTER_COLLECTION_LOOKUP', 'ok=' .. tostring(ok_items) .. '|count=' .. tostring(ok_items and #items or 0))
return {{}}
'''
    (args.output / "src").mkdir(parents=True, exist_ok=False)
    helper = Path(__file__).resolve().parents[1] / "research" / "runtime" / "kfc_localization_registry.lua"
    (args.output / "src" / "kfc_localization_registry.lua").write_text(helper.read_text(encoding="utf-8"), encoding="utf-8")
    (args.output / "src" / "mod.lua").write_text(source, encoding="utf-8")
    manifest = {
        "schema": "control_center.localization_collection_probe.v1",
        "id": args.output.name,
        "name": "Control Center Localization Collection Transition Probe",
        "version": "0.1.0",
        "author": "Enshrouded Control Center",
        "capabilities": ["patch"],
        "feature_state": "research-only",
        "entrypoint": "src/mod.lua",
        "locales": list(locales),
        "mode": "collection_transition_only"
    }
    (args.output / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated localization collection probe: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
