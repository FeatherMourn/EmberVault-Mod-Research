"""Build a bounded offline dependency map for exported VoxelWorld resources."""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


GUID_RE = re.compile(r"(?i)([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
SCHEMA = "control_center.voxel_world_dependency_map.v1"


def entry_guid(name: str) -> str | None:
    match = GUID_RE.search(name)
    return match.group(1).lower() if match else None


def content_hash(value: object) -> tuple[int, int, int, int] | None:
    if not isinstance(value, dict):
        return None
    try:
        result = tuple(int(value[key]) for key in ("size", "hash0", "hash1", "hash2"))
    except (KeyError, TypeError, ValueError):
        return None
    return result


def analyze(voxel_archive: Path, scene_archive: Path) -> dict:
    scene_guids: set[str] = set()
    with zipfile.ZipFile(scene_archive) as archive:
        scene_guids = {guid for item in archive.infolist() if (guid := entry_guid(item.filename))}

    worlds: list[dict] = []
    unique_materials: set[str] = set()
    unique_hashes: set[tuple[int, int, int, int]] = set()
    type_counts: Counter[str] = Counter()
    guid_parts: defaultdict[str, list[int]] = defaultdict(list)
    invalid_entries: list[str] = []
    with zipfile.ZipFile(voxel_archive) as archive:
        for item in archive.infolist():
            if item.is_dir() or not item.filename.lower().endswith(".json"):
                continue
            try:
                data = json.loads(archive.read(item).decode("utf-8-sig"))
            except (UnicodeDecodeError, ValueError, OSError):
                invalid_entries.append(item.filename)
                continue
            guid = str(data.get("$guid") or entry_guid(item.filename) or "").lower()
            part = int(data.get("$part", 0))
            world_type = str(data.get("type", "unknown"))
            materials = [str(value).lower() for value in data.get("materialGuids", []) if value]
            hashes: list[tuple[int, int, int, int]] = []
            for level in data.get("voxelLevels", []):
                if not isinstance(level, dict):
                    continue
                for value in level.get("tiles", []):
                    if (parsed := content_hash(value)) is not None and parsed[0] > 0:
                        hashes.append(parsed)
            for field in ("cpuDisplacement", "voxelHashes"):
                if (parsed := content_hash(data.get(field))) is not None and parsed[0] > 0:
                    hashes.append(parsed)
            unique_materials.update(materials)
            unique_hashes.update(hashes)
            type_counts[world_type] += 1
            guid_parts[guid].append(part)
            size = data.get("size", {}) if isinstance(data.get("size"), dict) else {}
            worlds.append({
                "guid": guid,
                "part": part,
                "type": world_type,
                "size": {axis: int(size.get(axis, 0)) for axis in ("x", "y", "z")},
                "scene_owned": guid in scene_guids,
                "material_dependency_count": len(set(materials)),
                "content_hash_count": len(hashes),
                "content_bytes": sum(value[0] for value in hashes),
            })

    return {
        "schema": SCHEMA,
        "read_only": True,
        "voxel_archive": str(Path(voxel_archive).resolve()),
        "scene_archive": str(Path(scene_archive).resolve()),
        "world_count": len(worlds),
        "world_type_counts": dict(sorted(type_counts.items())),
        "unique_world_guid_count": len(guid_parts),
        "multi_part_world_guids": [
            {"guid": guid, "parts": sorted(parts)}
            for guid, parts in sorted(guid_parts.items()) if len(parts) > 1
        ],
        "scene_owned_world_count": sum(1 for world in worlds if world["scene_owned"]),
        "standalone_world_count": sum(1 for world in worlds if not world["scene_owned"]),
        "unique_material_guid_count": len(unique_materials),
        "unique_content_hash_count": len(unique_hashes),
        "referenced_content_bytes": sum(value[0] for value in unique_hashes),
        "invalid_entries": invalid_entries,
        "worlds": sorted(worlds, key=lambda item: (item["guid"], item["part"])),
        "limitations": [
            "ContentHash identifies binary content, not a typed resource GUID.",
            "Archive overlap suggests scene ownership but does not prove runtime attachment.",
            "This analysis does not decode voxel blobs or mutate game or save data.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("voxel_archive", type=Path)
    parser.add_argument("scene_archive", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.voxel_archive, args.scene_archive)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not result["invalid_entries"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
