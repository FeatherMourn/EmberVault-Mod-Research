"""Generate a research-only localization probe for a selected locale subset."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--locale", action="append", default=["En_Us"], dest="locales")
    args = parser.parse_args()
    locales = tuple(dict.fromkeys(item.strip() for item in args.locales if item.strip()))
    if not locales:
        parser.error("at least one locale is required")
    source_path = args.template / "src" / "mod.lua"
    source = source_path.read_text(encoding="utf-8")
    marker = "}, '9d0a2a4f-3b7b-5e4c-9aa2-6b8e5f77c1d0', 'En_Us')"
    lua_locales = "{" + ", ".join(json.dumps(locale) for locale in locales) + "}"
    replacement = "}, '9d0a2a4f-3b7b-5e4c-9aa2-6b8e5f77c1d0', 'En_Us', " + lua_locales + ")"
    if marker not in source:
        raise SystemExit("localization collection call marker not found")
    source = source.replace(marker, replacement, 1)
    if args.output.exists():
        raise SystemExit(f"output already exists: {args.output}")
    (args.output / "src").mkdir(parents=True)
    (args.output / "src" / "mod.lua").write_text(source, encoding="utf-8")
    helper = args.template / "src" / "kfc_localization_registry.lua"
    (args.output / "src" / helper.name).write_text(helper.read_text(encoding="utf-8"), encoding="utf-8")
    manifest = {
        "schema": "control_center.localization_locale_probe.v1",
        "id": args.output.name,
        "name": "Control Center Locale-Filtered Localization Probe",
        "version": "0.1.0",
        "author": "Enshrouded Control Center",
        "capabilities": ["patch"],
        "feature_state": "research-only",
        "entrypoint": "src/mod.lua",
        "locales": list(locales),
        "mode": "locale_filtered_collection_registration",
        "rollback": "remove this module while the game is stopped and restore the stable profile"
    }
    (args.output / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated locale-filtered localization probe: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
