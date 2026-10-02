#!/usr/bin/env python3
"""Generate the read-only semantic building catalog from ArchitectDataIndex."""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

REVISION = 1076226
EXE_SHA256 = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"


def classify(row: sqlite3.Row, has_blueprint: bool) -> tuple[str, str, str]:
    material = row["place_voxel_material_id"]
    category = (row["category"] or "").strip()
    slot = (row["equipment_slot"] or "").strip()
    # BlueprintMaterial_* records can also have voxel payload mappings, but
    # their equipment slot identifies them as material records rather than
    # geometric Construction Hammer blueprints.
    if slot == "BlueprintMaterial_Roof":
        return "Roof Material", "PROVEN", "BlueprintMaterial_Roof equipment slot"
    if slot.startswith("BlueprintMaterial_"):
        return "Building Block Material", "PROVEN", "BlueprintMaterial_* equipment slot"
    if has_blueprint:
        return "Voxel Blueprint", "PROVEN", "blueprint registry mapping exists"
    if material is not None and int(material) >= 128 and row["is_building_voxel"] == 1:
        return "Building Block Material", "PROVEN", "placeVoxelMaterialId >= 128; isBuildingVoxel relationship supported"
    if material is not None and int(material) > 0 and int(material) < 128 and row["is_building_voxel"] == 0:
        return "Terrain Material", "PROVEN", "placeVoxelMaterialId < 128; terrain relationship supported"
    if slot == "BuildTool" and category == "Blueprints":
        return "Build Tool", "INFERRED", "Blueprints category and BuildTool equipment slot"
    if slot == "BuildTool":
        return "Special Building Tool", "INFERRED", "BuildTool equipment slot without blueprint mapping"
    if category in {"BuildTools", "Materials"}:
        return "Other Building-Related", "INFERRED", "building-related category without stronger material/blueprint fields"
    return "Other Building-Related", "UNKNOWN", "no stronger local semantic fields"


def build(db_path: Path, output: Path, snap_output: Path) -> None:
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    build_row = db.execute("SELECT revision, executable_sha256, generated_at_utc, source_bundle_sha256 FROM builds LIMIT 1").fetchone()
    if not build_row or int(build_row["revision"]) != REVISION or build_row["executable_sha256"].upper() != EXE_SHA256:
        raise SystemExit("INDEX_BUILD_MISMATCH")
    blueprint_ids = {int(r[0]) for r in db.execute("SELECT DISTINCT item_id FROM blueprints WHERE item_id IS NOT NULL")}
    blueprint_by_item: dict[int, list[dict]] = {}
    for row in db.execute("""
        SELECT b.item_id,b.dimensions,b.registry_position,b.payload_hex,b.payload_length,b.compressed,b.evidence_status,
               r.guid,r.debug_name,r.part_index,r.content_hash,r.source_file,
               rt.name AS resource_type,rt.type_hash
        FROM blueprints b
        LEFT JOIN resources r ON r.id=b.resource_id
        LEFT JOIN resource_types rt ON rt.id=r.resource_type_id
        ORDER BY b.item_id,b.registry_position
    """):
        expected_bytes = None
        try:
            d=json.loads(row["dimensions"]); expected_bytes=(int(d.get("x",0))*int(d.get("y",0))*int(d.get("z",0))+7)//8
        except (TypeError,ValueError,json.JSONDecodeError): pass
        blueprint_by_item.setdefault(int(row["item_id"]), []).append({
            "resourceGuid": row["guid"], "resourceType": row["resource_type"],
            "typeHash": row["type_hash"], "partIndex": row["part_index"],
            "contentHash": row["content_hash"], "sourceFile": row["source_file"],
            "debugName": row["debug_name"], "dimensions": row["dimensions"],
            "registryPosition": row["registry_position"],
            "compressedOccupancyBytes": row["payload_length"] if row["compressed"] else None,
            "occupancyVoxelCount": None, "compressionExpectedBytes": expected_bytes,
            "compressionSizeValid": (not row["compressed"]) or expected_bytes == row["payload_length"],
            "payloadHex": row["payload_hex"], "materialBehavior": None,
            "evidence": row["evidence_status"]
        })
    recipes: dict[int, list[dict]] = {}
    recipes_by_item: dict[int, list[dict]] = {}
    for row in db.execute("SELECT recipes.recipe_id,recipes.workshop_id,recipe_outputs.ordinal,recipe_outputs.item_id,recipe_outputs.count,recipe_outputs.source_file,recipe_outputs.evidence_status FROM recipes LEFT JOIN recipe_outputs USING(recipe_id) ORDER BY recipes.recipe_id,recipe_outputs.ordinal"):
        rec = {"recipeId": int(row["recipe_id"]), "workshopId": row["workshop_id"], "itemId": row["item_id"], "count": row["count"], "sourceFile": row["source_file"], "evidence": row["evidence_status"]}
        recipes.setdefault(int(row["recipe_id"]), []).append(rec)
        if row["item_id"] is not None:
            recipes_by_item.setdefault(int(row["item_id"]), []).append(rec)
    links = {int(r[0]) for r in db.execute("SELECT DISTINCT item_id FROM item_registry WHERE item_id IS NOT NULL")}
    terrain_configs = {}
    for row in db.execute("SELECT material_id,id,terrain_item_guid,hardness,health_points,material_feedback_id,metadata_json FROM terrain_configs ORDER BY id"):
        if row["material_id"] is not None and int(row["material_id"]) not in terrain_configs:
            terrain_configs[int(row["material_id"])] = {"configId": row["id"], "terrainItemGuid": row["terrain_item_guid"], "hardness": row["hardness"], "healthPoints": row["health_points"], "materialFeedbackId": row["material_feedback_id"], "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else None}
    building_configs = {}
    for row in db.execute("SELECT material_id,id,layer,material_item_guid,hardness,health_points,is_roof_block,material_feedback_id,metadata_json FROM building_configs ORDER BY id"):
        key = (int(row["layer"]) + 128) if row["layer"] is not None else row["material_id"]
        if key is not None and int(key) not in building_configs:
            building_configs[int(key)] = {"configId": row["id"], "layer": row["layer"], "materialId": row["material_id"], "materialItemGuid": row["material_item_guid"], "hardness": row["hardness"], "healthPoints": row["health_points"], "isRoofBlock": bool(row["is_roof_block"]) if row["is_roof_block"] is not None else None, "materialFeedbackId": row["material_feedback_id"], "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else None}
    items = []
    for row in db.execute("""
        SELECT i.*,r.guid,r.part_index AS resource_part_index,
               r.content_hash AS resource_content_hash,r.source_file AS resource_source_file,
               rt.name AS resource_type,rt.type_hash
        FROM items i
        LEFT JOIN resources r ON r.id=i.resource_id
        LEFT JOIN resource_types rt ON rt.id=r.resource_type_id
        ORDER BY i.item_id
    """):
        item_id = int(row["item_id"])
        bps = blueprint_by_item.get(item_id, [])
        cls, evidence, reason = classify(row, bool(bps))
        item_rec = {
            "itemId": item_id, "debugName": row["debug_name"], "guid": row["guid"],
            "resourceType": row["resource_type"], "typeHash": row["type_hash"],
            "resourcePartIndex": row["resource_part_index"],
            "resourceContentHash": row["resource_content_hash"],
            "resourceSourceFile": row["resource_source_file"],
            "category": row["category"], "equipmentSlot": row["equipment_slot"],
            "classification": cls, "classificationEvidence": evidence,
            "classificationReason": reason,
            "placeVoxelMaterialId": row["place_voxel_material_id"],
            "derivedBuildingLayerCandidate": (int(row["place_voxel_material_id"]) - 128 if row["place_voxel_material_id"] is not None and int(row["place_voxel_material_id"]) >= 128 else None),
            "isBuildingVoxel": bool(row["is_building_voxel"]) if row["is_building_voxel"] is not None else None,
            "terrainConfig": terrain_configs.get(int(row["place_voxel_material_id"])) if row["place_voxel_material_id"] is not None else None,
            "buildingConfig": building_configs.get(int(row["place_voxel_material_id"])) if row["place_voxel_material_id"] is not None else None,
            "terrainConfigId": terrain_configs.get(int(row["place_voxel_material_id"]), {}).get("configId") if row["place_voxel_material_id"] is not None else None,
            "buildingConfigId": building_configs.get(int(row["place_voxel_material_id"]), {}).get("configId") if row["place_voxel_material_id"] is not None else None,
            "hardness": (terrain_configs.get(int(row["place_voxel_material_id"]), {}).get("hardness") or building_configs.get(int(row["place_voxel_material_id"]), {}).get("hardness")) if row["place_voxel_material_id"] is not None else None,
            "health": (terrain_configs.get(int(row["place_voxel_material_id"]), {}).get("healthPoints") or building_configs.get(int(row["place_voxel_material_id"]), {}).get("healthPoints")) if row["place_voxel_material_id"] is not None else None,
            "roofFlag": building_configs.get(int(row["place_voxel_material_id"]), {}).get("isRoofBlock") if row["place_voxel_material_id"] is not None else None,
            "registryMembership": item_id in links,
            "blueprints": bps, "recipes": recipes_by_item.get(item_id, []),
            "snapFamily": None, "snapEvidence": "UNAVAILABLE"
        }
        items.append(item_rec)
    coverage = {str(r[0]): {"status": r[1], "rowCount": int(r[2]), "limitation": r[3]} for r in db.execute("SELECT family,status,row_count,limitation FROM coverage ORDER BY family")}
    generated_at = build_row["generated_at_utc"]
    generated_now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    snap_rows = []
    for row in db.execute("SELECT config_guid,config_name,rule_guid,ordinal,metadata_json,source_file,evidence_status FROM blueprint_snap_rules ORDER BY config_name,config_guid,ordinal"):
        try: metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {}
        except json.JSONDecodeError: metadata={"rawMetadata": row["metadata_json"]}
        snap_rows.append({"configGuid": row["config_guid"], "configName": row["config_name"], "ruleGuid": row["rule_guid"], "ordinal": row["ordinal"], "fields": metadata, "sourceFile": row["source_file"], "evidence": row["evidence_status"]})
    snap_configs = {}
    for rule in snap_rows:
        key=(rule["configGuid"],rule["configName"]); snap_configs.setdefault(key,[]).append(rule)
    report = {"schemaVersion": 1, "catalog": "Architect Semantic Building Catalog", "backendStatus": "read_only_catalog", "generatedAtUtc": generated_now, "gameBuild": {"revision": REVISION, "executableSha256": EXE_SHA256, "sourceBundleSha256": build_row["source_bundle_sha256"]}, "sourceProvenance": {"database": str(db_path.resolve()), "databaseGeneratedAt": generated_at, "identityPolicy": "Item IDs are imported from explicit source fields; no debug-name/GUID derivation"}, "coverage": coverage, "coverageCounts": {"items": len(items), "blueprintItems": sum(bool(x["blueprints"]) for x in items), "terrainItems": sum(x["classification"] == "Terrain Material" for x in items), "buildingMaterialItems": sum(x["classification"] == "Building Block Material" for x in items), "recipes": sum(len(x["recipes"]) for x in items), "recipeResources": db.execute("SELECT COUNT(*) FROM recipes").fetchone()[0], "snapRules": len(snap_rows), "snapConfigurations": len(snap_configs)}, "items": items}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    snap = {"schemaVersion": 1, "catalog": "Vanilla Snap Rule Catalog", "generatedAtUtc": generated_now, "gameBuild": {"revision": REVISION, "executableSha256": EXE_SHA256, "sourceBundleSha256": build_row["source_bundle_sha256"]}, "source": "ArchitectDataIndex.blueprint_snap_rules", "status": "AVAILABLE" if snap_rows else "UNAVAILABLE", "reason": None if snap_rows else "No verified local VoxelBlueprintConfig export is present; no relationships are invented.", "configurationCount": len(snap_configs), "ruleCount": len(snap_rows), "configurations": [{"guid": key[0], "debugName": key[1], "rules": rules} for key,rules in sorted(snap_configs.items(), key=lambda x:(x[0][1] or "",x[0][0] or ""))], "coverage": coverage.get("blueprint_snap_rules", {"status": "UNAVAILABLE", "rowCount": 0})}
    linked_snap_count = int(db.execute("SELECT COUNT(*) FROM blueprint_snap_rules WHERE blueprint_id IS NOT NULL").fetchone()[0])
    if linked_snap_count:
        snap["itemToFamilyLink"] = {"status": "AVAILABLE_PARTIAL", "linkedRuleCount": linked_snap_count, "evidence": "explicit blueprint_id foreign-key links"}
    else:
        snap["itemToFamilyLink"] = {"status": "UNAVAILABLE", "linkedRuleCount": 0, "evidence": "all imported snap rules have null blueprint_id; no item-to-family relationship is fabricated"}
    snap_output.parent.mkdir(parents=True, exist_ok=True)
    snap_output.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    db.close()
    print(f"catalogItems={len(items)} blueprintItems={report['coverageCounts']['blueprintItems']} snapRules={len(snap_rows)}")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser()
    p.add_argument("--database", type=Path, default=root / "data" / "architect_game_data_1076226.sqlite")
    p.add_argument("--output", type=Path, default=root / "bridge" / "build_catalog.json")
    p.add_argument("--snap-output", type=Path, default=root / "bridge" / "snap_rule_catalog.json")
    a = p.parse_args()
    build(a.database.resolve(), a.output.resolve(), a.snap_output.resolve())


if __name__ == "__main__":
    main()
