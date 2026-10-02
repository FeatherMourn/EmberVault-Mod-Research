"""Find ItemInfo iconImage references and matching UiTextureResource exports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_pairs(item_root: Path, texture_root: Path) -> list[dict]:
    textures = {}
    for path in texture_root.rglob("*.json"):
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        guid = data.get("$guid")
        if guid:
            textures[guid.lower()] = (path, data)

    pairs = []
    for path in item_root.rglob("*.json"):
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        icon = data.get("iconImage")
        if not isinstance(icon, str):
            continue
        texture = textures.get(icon.lower())
        pairs.append(
            {
                "item_file": str(path),
                "icon_reference": icon,
                "texture_file": str(texture[0]) if texture else None,
                "texture": texture[1] if texture else None,
            }
        )
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--item-root", type=Path, required=True)
    parser.add_argument("--texture-root", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    pairs = find_pairs(args.item_root, args.texture_root)
    print(json.dumps(pairs[: args.limit], indent=2))
    print(f"matched={sum(p['texture_file'] is not None for p in pairs)} total={len(pairs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

