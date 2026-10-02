#!/usr/bin/env python3
"""Emit relationship and provenance validation for the build-focused index."""
from __future__ import annotations

import argparse
import json
import sqlite3
import re
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=root / "data" / "architect_game_data_1076226.sqlite")
    parser.add_argument("--output", type=Path, default=root / "bridge" / "build_catalog_validation.json")
    args = parser.parse_args()
    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    build = db.execute("SELECT revision,executable_sha256,schema_version,source_bundle_sha256,generated_at_utc FROM builds LIMIT 1").fetchone()
    counts = {
        "itemRegistryToItemInfo": db.execute("SELECT COUNT(*) FROM item_registry WHERE item_id IS NOT NULL").fetchone()[0],
        "recipeInputToItemInfo": db.execute("SELECT COUNT(*) FROM recipe_inputs WHERE item_id IN (SELECT item_id FROM items)").fetchone()[0],
        "recipeOutputToItemInfo": db.execute("SELECT COUNT(*) FROM recipe_outputs WHERE item_id IN (SELECT item_id FROM items)").fetchone()[0],
        "blueprintToItemInfo": db.execute("SELECT COUNT(*) FROM blueprints WHERE item_id IN (SELECT item_id FROM items)").fetchone()[0],
        "terrainMaterialToConfig": db.execute("SELECT COUNT(*) FROM items i JOIN terrain_configs t ON t.material_id=i.place_voxel_material_id WHERE i.place_voxel_material_id < 128").fetchone()[0],
        "buildingMaterialToConfig": db.execute("SELECT COUNT(*) FROM items i JOIN building_configs b ON b.layer=(i.place_voxel_material_id-128) WHERE i.place_voxel_material_id >= 128").fetchone()[0],
        "materialFeedbackResources": db.execute("SELECT COUNT(*) FROM material_feedback").fetchone()[0],
        "provenResourceRelationships": db.execute("SELECT COUNT(*) FROM resource_relationships WHERE confidence='PROVEN'").fetchone()[0],
        "snapRuleTargets": db.execute("SELECT COUNT(*) FROM blueprint_snap_rules").fetchone()[0],
    }
    compression_valid = 0
    compression_invalid = 0
    for row in db.execute("SELECT dimensions,payload_length,compressed FROM blueprints WHERE compressed=1"):
        match=re.fullmatch(r'\{"x":(\d+),"y":(\d+),"z":(\d+)\}', row["dimensions"] or "")
        if not match: continue
        expected=(int(match.group(1))*int(match.group(2))*int(match.group(3))+7)//8
        if expected == row["payload_length"]: compression_valid += 1
        else: compression_invalid += 1
    unresolved = {row["source_family"]: row["count"] for row in db.execute("SELECT source_family,COUNT(*) AS count FROM unresolved_refs GROUP BY source_family ORDER BY source_family")}
    duplicate_ids = [dict(row) for row in db.execute("SELECT item_id,COUNT(*) AS count,GROUP_CONCAT(DISTINCT resource_id) AS resources FROM items GROUP BY item_id HAVING COUNT(*)>1")]
    duplicate_guid_ids = [dict(row) for row in db.execute("SELECT r.guid,COUNT(DISTINCT i.item_id) AS item_ids,GROUP_CONCAT(DISTINCT i.item_id) AS item_values FROM items i JOIN resources r ON r.id=i.resource_id WHERE r.guid IS NOT NULL GROUP BY r.guid HAVING COUNT(DISTINCT i.item_id)>1")]
    duplicate_registry = [dict(row) for row in db.execute("SELECT registry_kind,item_id,COUNT(*) AS count FROM item_registry GROUP BY registry_kind,item_id HAVING COUNT(*)>1")]
    sources = [dict(row) for row in db.execute("SELECT path,sha256,kind FROM input_sources ORDER BY kind,path")]
    report = {
        "schemaVersion": 1,
        "gameBuild": {"revision": build["revision"], "executableSha256": build["executable_sha256"], "databaseSchemaVersion": build["schema_version"], "sourceBundleSha256": build["source_bundle_sha256"], "generatedAtUtc": build["generated_at_utc"]},
        "validRelationshipCounts": counts,
        "blueprintCompressionValidation": {"valid": compression_valid, "invalid": compression_invalid},
        "unresolvedReferenceCounts": unresolved,
        "duplicateIdentities": {"itemIds": duplicate_ids, "itemInfoGuids": duplicate_guid_ids, "registryLinks": duplicate_registry},
        "invalidCardinalities": {"buildingConfigRows": db.execute("SELECT COUNT(*) FROM building_configs").fetchone()[0], "terrainConfigRows": db.execute("SELECT COUNT(*) FROM terrain_configs").fetchone()[0], "snapConfigurationCount": db.execute("SELECT COUNT(DISTINCT config_guid) FROM blueprint_snap_rules").fetchone()[0]},
        "sourceFiles": sources,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"validationRelationships={sum(counts.values())} unresolved={sum(unresolved.values())}")


if __name__ == "__main__":
    main()
