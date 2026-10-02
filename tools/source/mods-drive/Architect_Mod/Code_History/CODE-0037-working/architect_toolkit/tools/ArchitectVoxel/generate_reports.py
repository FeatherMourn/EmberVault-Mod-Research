"""Generate reproducible offline audit artifacts; never touches game files."""

from __future__ import annotations

import json
from pathlib import Path

try:  # Support both ``python generate_reports.py`` and package imports.
    from .architect_voxel import baseline_shapes, shape_payload_report, sphere, hollow_square, hollow_cylinder, dome, spiral_stairs, make_shape
    from .chunk_planner import plan_voxel_set, plan_voxels_v2
except ImportError:  # pragma: no cover - direct script invocation
    from architect_voxel import baseline_shapes, shape_payload_report, sphere, hollow_square, hollow_cylinder, dome, spiral_stairs, make_shape
    from chunk_planner import plan_voxel_set, plan_voxels_v2


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    shape_reports = {
        name: {
            **shape_payload_report(shape),
            "exactExportAvailable": False,
            "exactExportNote": "No existing source payload export was present in this repository; payloadHex is the deterministic Lua-compatible generation result.",
        }
        for name, shape in baseline_shapes().items()
    }
    write_json(ARTIFACTS / "shape_payload_audit.json", {
        "format": 1,
        "generator": "ArchitectVoxel offline library",
        "coordinateOrder": "y,z,x; bits LSB-first",
        "sourceSemantics": "mirrors src/mod.lua compression and six baseline predicates",
        "shapes": shape_reports,
    })

    v2_shape_specs = {
        "line": {"start": [0, 0, 0], "end": [7, 3, 7]},
        "wall": {}, "floor": {}, "rectangle": {"filled": False}, "box": {"filled": False},
        "ellipse": {}, "ellipsoid": {}, "dome": {}, "cone": {}, "arch": {}, "ramp": {},
        "stairs": {}, "spiral_stairs": {}, "tunnel": {}, "road_strip": {},
    }
    v2_shape_reports = {}
    for name, spec in v2_shape_specs.items():
        shape = make_shape(name, (8, 8, 8), **spec)
        v2_shape_reports[name] = {**shape_payload_report(shape), "parameters": spec}
    write_json(ARTIFACTS / "shape_engine_v2_audit.json", {
        "format": 2, "engine": "ArchitectVoxel", "dimensions": [8, 8, 8], "shapes": v2_shape_reports,
    })

    cases = {
        "sphere_16m": sphere((32, 32, 32)),
        "long_wall": hollow_square((32, 1, 8)),
        "hollow_cylinder": hollow_cylinder((16, 16, 16)),
    }
    case_reports = {}
    for name, shape in cases.items():
        tiles = plan_voxel_set(shape, (8, 8, 8))
        case_reports[name] = {
            "sourceDimensions": list(shape.dimensions),
            "sourceOccupiedVoxelCount": shape.occupied_count,
            "tileDimensions": [8, 8, 8],
            "tileCount": len(tiles),
            "nonemptyTileCount": sum(not tile.is_empty for tile in tiles),
            "tiles": [tile.as_dict() for tile in tiles],
        }
    write_json(ARTIFACTS / "chunk_planner_audit.json", {
        "format": 1,
        "planner": "ArchitectVoxel offline 8x8x8 tile planner",
        "cases": case_reports,
    })

    v2_cases = {
        "hollow_sphere_32m": sphere((32, 32, 32)),
        "wall_50m": hollow_square((50, 1, 8)),
        "dome_24m": dome((24, 24, 24)),
        "tunnel_40m": hollow_cylinder((40, 16, 16), axis="x"),
        "spiral_staircase": spiral_stairs((32, 16, 32)),
    }
    v2_reports = {}
    for name, shape in v2_cases.items():
        plan = plan_voxels_v2(shape.dimensions, shape.occupied, (8, 8, 8), suppress_empty=True, anchor="min")
        v2_reports[name] = {
            "sourceDimensions": list(shape.dimensions),
            "sourceOccupiedVoxelCount": shape.occupied_count,
            "tileCount": len(plan["tiles"]),
            "nonemptyTileCount": len(plan["tiles"]),
            "estimatedPlacementOperations": plan["estimatedPlacementOperations"],
            "overlapCount": len(plan["overlaps"]),
            "boundingBoxes": plan["boundingBoxes"],
            "tiles": [{k: v for k, v in tile.items() if k != "occupied"} for tile in plan["tiles"]],
        }
    write_json(ARTIFACTS / "chunk_planner_v2_audit.json", {
        "format": 2, "planner": "ArchitectVoxel v2", "tileDimensions": [8, 8, 8], "cases": v2_reports,
    })


if __name__ == "__main__":
    main()
