"""Verify that a patched KFC contains the complete custom-content fixture.

This is intentionally offline and read-only. It validates archive extraction
output, not whether the game client can render the content.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _json_files(root: Path, resource_type: str) -> list[Path]:
    folder = root / resource_type
    return sorted(folder.glob("*.json")) if folder.is_dir() else []


def _matching_files(paths: list[Path], needles: list[str]) -> list[Path]:
    result = []
    for path in paths:
        text = path.read_text(encoding="utf-8-sig")
        if all(needle in text for needle in needles):
            result.append(path)
    return result


def _registry_contains_item(root: Path, item_debug_name: str) -> bool:
    """Resolve ItemRegistryResource GUID refs through staged ItemInfo records.

    The registry stores GUID strings, not ItemInfo debug names.  Searching the
    registry JSON for a debug name therefore produces a false negative even
    when the item is correctly registered.
    """
    item_guid_by_name: set[str] = set()
    for path in _json_files(root, "ItemInfo"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("debugName") == item_debug_name:
            guid = payload.get("$guid")
            if guid:
                item_guid_by_name.add(str(guid).lower())
    # Keep the verifier useful for minimal text fixtures used by unit tests
    # and by authors preparing an archive before the parser emits full JSON.
    if not item_guid_by_name:
        return bool(_matching_files(_json_files(root, "ItemRegistryResource"), [item_debug_name]))
    for path in _json_files(root, "ItemRegistryResource"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        refs = payload.get("itemRefs") or []
        if any(str(ref).lower() in item_guid_by_name for ref in refs):
            return True
    return False


def verify(
    root: Path,
    item_id: int,
    recipe_id: int,
    item_debug_name: str,
    recipe_guid: str | None = None,
) -> dict:
    item_id_text = str(item_id)
    recipe_id_text = str(recipe_id)
    checks = {
        "item_info": bool(_matching_files(_json_files(root, "ItemInfo"), [item_id_text, item_debug_name])),
        "item_registry": _registry_contains_item(root, item_debug_name),
        "recipe_registry": bool(_matching_files(_json_files(root, "RecipeRegistryResource"), [recipe_id_text, item_id_text])),
        "knowledge_link": bool(_matching_files(_json_files(root, "ItemKnowledgeResource"), [item_id_text])),
        "ui_recipe_link": bool(_matching_files(_json_files(root, "FbUiBundle"), [recipe_id_text])),
    }
    if recipe_guid:
        checks["recipe_guid"] = bool(
            _matching_files(_json_files(root, "RecipeRegistryResource"), [recipe_guid])
        )
    return {
        "root": str(root),
        "item_id": item_id,
        "recipe_id": recipe_id,
        "item_debug_name": item_debug_name,
        "checks": checks,
        "archive_registration_complete": all(checks.values()),
        "client_rendering_verified": False,
        "note": "Archive presence does not prove client catalog or visual consumption.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--item-id", type=int, required=True)
    parser.add_argument("--recipe-id", type=int, required=True)
    parser.add_argument("--debug-name", required=True)
    parser.add_argument("--recipe-guid")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(args.root, args.item_id, args.recipe_id, args.debug_name, args.recipe_guid)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["archive_registration_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
