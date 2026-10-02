"""Find likely catalog-preview fields in a KFC inventory JSON document."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


KEYWORDS = ("icon", "preview", "picker", "render", "thumbnail", "catalog")


def find_fields(value: object, path: str = "$") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(key, str) and any(word in key.lower() for word in KEYWORDS):
                found.append({"path": child_path, "field": key, "value_type": type(child).__name__})
            if key == "name" and isinstance(child, str) and any(word in child.lower() for word in KEYWORDS):
                found.append({"path": child_path, "field": child, "value_type": "reflected_field"})
            found.extend(find_fields(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_fields(child, f"{path}[{index}]"))
    return found


def search(path: Path, family: str | None = None, reflected_type: str | None = None) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    source = data
    if family:
        source = dict(data)
        families = [item for item in data.get("families", []) if item.get("family") == family]
        if reflected_type:
            families = [
                {**item, "reflected_types": [t for t in item.get("reflected_types", []) if t.get("name") == reflected_type]}
                for item in families
            ]
        source["families"] = families
    fields = find_fields(source)
    unique = {(item["field"], item["value_type"]): item for item in fields}
    return {
        "schema": "control_center.ui_preview_field_candidates.v1",
        "inventory": str(path.resolve()),
        "family_filter": family,
        "reflected_type_filter": reflected_type,
        "keywords": list(KEYWORDS),
        "candidate_count": len(unique),
        "candidates": sorted(unique.values(), key=lambda item: (item["field"].lower(), item["value_type"])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--family", help="limit results to one KFC family, such as FbUiBundle")
    parser.add_argument("--reflected-type", help="limit results to one reflected type")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(search(args.inventory, args.family, args.reflected_type), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
