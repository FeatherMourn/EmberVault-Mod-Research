"""Build-locked offline SQLite generator for locally audited Architect data."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REVISION = 1076226
EXE_SHA256 = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
SCHEMA_VERSION = 2
BUNDLE_SHA256 = "153BE9AF6875DB39594FDCAC7A08EE8B316C802BE8A426D24F0A9DFAE713C474"
FAMILIES = ("items", "item_registry", "recipes", "recipe_inputs", "recipe_outputs",
            "terrain_configs", "building_configs", "blueprints", "blueprint_snap_rules",
            "templates", "template_components", "attributes", "attribute_groups", "perks",
            "skill_nodes", "impact_programs", "actor_sequences", "map_markers", "camera_states")
FAMILIES += ("material_feedback", "material_layers", "building_material_layers", "unresolved_refs")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


class Builder:
    def __init__(self, conn: sqlite3.Connection, root: Path, sources: list[Path]):
        self.db, self.root, self.sources = conn, root, sources
        self.types: dict[str, int] = {}
        self.resources: dict[tuple[str, str, int], int] = {}

    def source_name(self, path: Path) -> str:
        try: return path.resolve().relative_to(self.root).as_posix()
        except ValueError: return str(path.resolve())

    def resource_type(self, name: str, size=None, status="PROVEN", type_hash=None) -> int:
        if name not in self.types:
            cur = self.db.execute("INSERT INTO resource_types(name,type_hash,reflected_size,evidence_status) VALUES(?,?,?,?)", (name,type_hash,size,status))
            self.types[name] = cur.lastrowid
        elif size is not None or type_hash is not None:
            self.db.execute("UPDATE resource_types SET type_hash=COALESCE(type_hash,?),reflected_size=COALESCE(reflected_size,?),evidence_status=? WHERE id=?", (type_hash,size,status,self.types[name]))
        return self.types[name]

    def resource(self, kind: str, guid: str | None, debug: str | None, source: Path,
                 status="PROVEN", part=0, content_hash=None, type_hash=None) -> int | None:
        if not guid:
            return None
        guid = guid.lower(); key=(kind,guid,part)
        if key in self.resources:
            rid=self.resources[key]
            if debug: self.db.execute("UPDATE resources SET debug_name=COALESCE(debug_name,?) WHERE id=?",(debug,rid))
            return rid
        cur=self.db.execute("INSERT INTO resources(build_id,resource_type_id,guid,part_index,content_hash,debug_name,source_file,evidence_status) VALUES(1,?,?,?,?,?,?,?)",
                            (self.resource_type(kind,type_hash=type_hash),guid,part,content_hash,debug,self.source_name(source),status))
        self.resources[key]=cur.lastrowid; return cur.lastrowid

    def item(self, item_id, debug, guid, source, category=None, slot=None, status="PROVEN", *, object_id=None, icon_model=None, icon_scene=None, visual_entity=None, metadata=None, type_hash=None, part=0):
        if item_id is None: return
        rid=self.resource("keen::ItemInfo",guid,debug,source,status,part=part,type_hash=type_hash)
        self.db.execute("""INSERT INTO items(item_id,resource_id,debug_name,category,equipment_slot,place_voxel_material_id,is_building_voxel,object_id,icon_model,icon_scene,visual_entity,metadata_json,source_file,evidence_status)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(item_id) DO UPDATE SET
                        resource_id=COALESCE(items.resource_id,excluded.resource_id),debug_name=COALESCE(items.debug_name,excluded.debug_name),
                        category=COALESCE(items.category,excluded.category),equipment_slot=COALESCE(items.equipment_slot,excluded.equipment_slot),
                        place_voxel_material_id=COALESCE(items.place_voxel_material_id,excluded.place_voxel_material_id),is_building_voxel=COALESCE(items.is_building_voxel,excluded.is_building_voxel),
                        object_id=COALESCE(items.object_id,excluded.object_id),icon_model=COALESCE(items.icon_model,excluded.icon_model),
                        icon_scene=COALESCE(items.icon_scene,excluded.icon_scene),visual_entity=COALESCE(items.visual_entity,excluded.visual_entity),
                        metadata_json=COALESCE(items.metadata_json,excluded.metadata_json)""",
                        (int(item_id),rid,debug or None,category or None,slot or None,metadata.get("placeVoxelMaterialId") if metadata else None,(1 if metadata.get("isBuildingVoxel") else 0) if metadata and metadata.get("isBuildingVoxel") is not None else None,object_id,icon_model,icon_scene,visual_entity,json.dumps(metadata,sort_keys=True,separators=(",",":")) if metadata else None,self.source_name(source),status))

    def add_registry_link(self, registry_guid, item_id, position, kind, source, status="PROVEN"):
        if item_id is None: return
        exists=self.db.execute("SELECT 1 FROM item_registry WHERE registry_kind=? AND item_id=? LIMIT 1",(kind,int(item_id))).fetchone()
        if exists: return
        self.db.execute("INSERT INTO item_registry(registry_guid,item_id,position,registry_kind,source_file,evidence_status) VALUES(?,?,?,?,?,?)",
                        (registry_guid,int(item_id),position,kind,self.source_name(source),status))

    def ingest_blueprint_audit(self,path,data):
        for row in data.get("vanillaBuildToolBlueprints",[]):
            item_id=row.get("itemIdValue"); guid=row.get("itemInfoGuid")
            self.item(item_id,row.get("debugName"),guid,path,row.get("category"),row.get("equipmentSlot"))
            if row.get("exactItemRegistryMembership"):
                self.add_registry_link(None,item_id,None,"ItemRegistryResource",path)
            for bp in row.get("matchingVoxelBlueprintItems",[]):
                bguid=row.get("previewVoxelGuid") or None
                brid=self.resource("keen::VoxelBlueprint",bguid,row.get("debugName"),path)
                self.db.execute("INSERT INTO blueprints(resource_id,item_id,dimensions,registry_position,source_file,evidence_status) VALUES(?,?,?,?,?,?)",
                                (brid,item_id,bp.get("dimensions"),bp.get("index"),self.source_name(path),"PROVEN"))

    def ingest_hammer(self,path,data):
        rows=list(data.get("mappedVanillaBlueprintItemInfos",[]))
        for group in data.get("vanillaBlueprintCategorySamples",[]): rows.extend(group.get("samples",[]))
        for row in rows:self.item(row.get("itemId"),row.get("debugName"),row.get("guid"),path,row.get("category"),row.get("equipmentSlot") or row.get("slot"))

    def ingest_workbench(self,path,data):
        for row in data.get("entries",[]):
            recipe=row.get("recipeId")
            self.db.execute("INSERT OR IGNORE INTO recipes(recipe_id,workshop_id,source_path,source_file,evidence_status) VALUES(?,?,?,?,?)",
                            (recipe,row.get("workshopId"),row.get("path"),self.source_name(path),"PROVEN"))
            for ordinal,out in enumerate(row.get("outputs",[])):
                self.item(out.get("itemId"),out.get("debugName"),out.get("itemGuid"),path,out.get("category"),out.get("slot"))
                self.db.execute("INSERT OR REPLACE INTO recipe_outputs(recipe_id,ordinal,item_id,count,source_file,evidence_status) VALUES(?,?,?,?,?,?)",
                                (recipe,ordinal,out.get("itemId"),out.get("count"),self.source_name(path),"PROVEN"))

    def ingest_ui_refs(self,path,data):
        for row in data.get("references",[]):
            target=row.get("targetId")
            if row.get("resourceType") == "keen::ItemRegistryResource" and row.get("field") == "itemRefs" and target is not None:
                self.item(target,None,None,path,status="PROVEN")
                self.add_registry_link(row.get("resourceGuid"),target,row.get("index"),"ItemRegistryResource",path)

    def ingest_backend(self,path,data):
        for row in data.get("shapes",[]):
            self.item(row.get("itemId"),row.get("displayName"),row.get("itemGuid"),path,"Blueprints","BuildTool","EXPERIMENTAL")
            rid=self.resource("keen::VoxelBlueprint",row.get("voxelGuid"),row.get("key"),path,"EXPERIMENTAL")
            self.db.execute("INSERT INTO blueprints(resource_id,item_id,dimensions,source_file,evidence_status) VALUES(?,?,?,?,?)",
                            (rid,row.get("itemId"),row.get("sizeLabel"),self.source_name(path),"EXPERIMENTAL"))

    def ingest_wand_text(self,path,text):
        fields={k.strip():v.strip() for k,v in (line.split(":",1) for line in text.splitlines() if ":" in line)}
        self.item(int(fields["SOURCE ITEM ID"]),fields.get("SOURCE DEBUG NAME"),None,path,fields.get("SOURCE CATEGORY"),status="PROVEN")
        self.item(int(fields["WAND ITEM ID"]),"Architect's Wand",fields.get("WAND ITEM GUID"),path,fields.get("CATEGORY"),fields.get("EQUIPMENT SLOT"),"EXPERIMENTAL")
        recipe=int(fields["WAND RECIPE ID"]); self.db.execute("INSERT OR IGNORE INTO recipes(recipe_id,workshop_id,source_file,evidence_status) VALUES(?,?,?,?)",(recipe,int(fields["RECIPE WORKSHOP ID"]),self.source_name(path),"EXPERIMENTAL"))
        self.db.execute("INSERT OR REPLACE INTO recipe_outputs(recipe_id,ordinal,item_id,count,source_file,evidence_status) VALUES(?,?,?,?,?,?)",(recipe,0,int(fields["RECIPE OUTPUT ITEM ID"]),int(fields["RECIPE OUTPUT COUNT"]),self.source_name(path),"EXPERIMENTAL"))

    def ingest_research(self,path,text):
        match=re.search(r"registered item is `([^`]+)` \(GUID\s+`([0-9a-f-]{36})`\).*?ItemId `([0-9]+)`",text,re.I|re.S)
        if not match:
            # Current prose states ItemId before the registered-item sentence.
            name=re.search(r"registered item is `([^`]+)` \(GUID\s+`([0-9a-f-]{36})`\)",text,re.I)
            ident=re.search(r"ItemId `([0-9]+)`",text)
            if name and ident:self.item(int(ident.group(1)),name.group(1),name.group(2),path,status="PROVEN")
        else:self.item(int(match.group(3)),match.group(1),match.group(2),path,status="PROVEN")
        if re.search(r"ItemStack` size `0x0C`",text):self.resource_type("keen::ItemStack",0x0C,"PROVEN")

    @staticmethod
    def value(value):
        return value.get("value") if isinstance(value, dict) and "value" in value else value

    def kfc_resource(self, data, path, status="PROVEN"):
        typ=data.get("$type") or path.parent.name
        guid=data.get("$guid")
        part=int(data.get("$part", 0) or 0)
        debug=data.get("debugName")
        type_hash=data.get("$typeSignatureHash")
        type_hash=self.value(type_hash)
        if type_hash is None:
            parts=path.stem.split("_")
            if len(parts) >= 2 and re.fullmatch(r"[0-9a-fA-F]{8}", parts[-2]):
                type_hash=parts[-2]
        return self.resource(typ,guid,debug,path,status,part=part,type_hash=str(type_hash) if type_hash is not None else None)

    def ingest_kfc_iteminfo(self, path, data):
        self.kfc_resource(data,path)
        item_id=self.value(data.get("itemId"))
        equipment=data.get("equipment") or {}
        voxel=equipment.get("voxelData") or {}
        metadata={
            "placeVoxelMaterialId": self.value(voxel.get("placeVoxelMaterialId")),
            "isBuildingVoxel": voxel.get("isBuildingVoxel"),
            "placeVoxelMaterial": voxel.get("placeVoxelMaterial"),
            "voxelBlueprintConfig": equipment.get("voxelBlueprintConfig"),
            "voxelObject": equipment.get("voxelObject"),
            "voxelSnappingConfig": equipment.get("voxelSnappingConfig"),
        }
        self.item(item_id,data.get("debugName"),data.get("$guid"),path,data.get("category"),equipment.get("slot"),
                  object_id=data.get("objectId"),icon_model=data.get("iconModel"),icon_scene=data.get("iconScene"),
                  visual_entity=equipment.get("visualEntity"),metadata=metadata,type_hash=self.value(data.get("$typeSignatureHash")),part=int(data.get("$part",0) or 0))

    def ingest_kfc_item_registry(self, path, data):
        rid=self.kfc_resource(data,path)
        refs=data.get("itemRefs") or []
        for pos,ref in enumerate(refs):
            guid=ref if isinstance(ref,str) else (ref.get("$guid") if isinstance(ref,dict) else None)
            item_id=self.item_guid_to_id.get(str(guid).lower()) if guid else None
            self.db.execute("INSERT OR IGNORE INTO item_registry(registry_guid,item_id,position,registry_kind,source_file,evidence_status) VALUES(?,?,?,?,?,?)",
                            (data.get("$guid"),item_id,pos,"ItemRegistryResource",self.source_name(path),"PROVEN" if item_id is not None else "UNRESOLVED"))
            if item_id is None:
                self.unresolved("ItemRegistryResource",data.get("$guid"),"itemRefs", "ItemInfoGuid",guid,path)

    def unresolved(self,family,identity,field,target_kind,target_value,path,status="UNRESOLVED"):
        self.db.execute("INSERT INTO unresolved_refs(source_family,source_identity,field_name,target_kind,target_value,source_file,evidence_status) VALUES(?,?,?,?,?,?,?)",
                        (family,identity,field,target_kind,str(target_value) if target_value is not None else None,self.source_name(path),status))

    def ingest_kfc_blueprints(self,path,data):
        rid=self.kfc_resource(data,path)
        for pos,row in enumerate(data.get("blueprintItems") or []):
            item_id=self.value(row.get("itemId")); size=row.get("size") or {}
            dims=json.dumps({"x":size.get("x"),"y":size.get("y"),"z":size.get("z")},sort_keys=True,separators=(",",":"))
            payload=bytes(int(x)&255 for x in (row.get("data") or []))
            if item_id is not None and item_id not in self.item_ids:
                self.unresolved("VoxelBlueprintItemRegistryResource",data.get("$guid"),f"blueprintItems[{pos}].itemId","ItemId",item_id,path)
            self.db.execute("INSERT INTO blueprints(resource_id,item_id,dimensions,registry_position,payload_hex,payload_length,compressed,source_file,evidence_status) VALUES(?,?,?,?,?,?,?,?,?)",
                            (rid,item_id,dims,pos,payload.hex(),len(payload),1 if row.get("isDataCompressed") else 0,self.source_name(path),"PROVEN"))

    def ingest_kfc_recipe(self,path,data):
        rid=self.kfc_resource(data,path)
        for row in data.get("recipes") or []:
            recipe_id=self.value(row.get("recipeId")); workshop=self.value(row.get("workshopId"))
            self.db.execute("INSERT OR REPLACE INTO recipes(recipe_id,resource_id,workshop_id,source_path,source_file,evidence_status) VALUES(?,?,?,?,?,?)",
                            (recipe_id,rid,workshop,None,self.source_name(path),"PROVEN"))
            for ordinal,inp in enumerate(row.get("input") or []):
                stack=inp.get("itemStack") or {}; iid=self.value(stack.get("item")); count=stack.get("count")
                self.db.execute("INSERT OR REPLACE INTO recipe_inputs(recipe_id,ordinal,item_id,count,source_file,evidence_status) VALUES(?,?,?,?,?,?)",(recipe_id,ordinal,iid,count,self.source_name(path),"PROVEN" if iid in self.item_ids else "UNRESOLVED"))
                if iid not in self.item_ids:self.unresolved("RecipeRegistryResource",data.get("$guid"),f"recipes[{recipe_id}].input[{ordinal}]","ItemId",iid,path)
            for ordinal,out in enumerate(row.get("output") or []):
                iid=self.value(out.get("item")); count=out.get("count")
                self.db.execute("INSERT OR REPLACE INTO recipe_outputs(recipe_id,ordinal,item_id,count,source_file,evidence_status) VALUES(?,?,?,?,?,?)",(recipe_id,ordinal,iid,count,self.source_name(path),"PROVEN" if iid in self.item_ids else "UNRESOLVED"))
                if iid not in self.item_ids:self.unresolved("RecipeRegistryResource",data.get("$guid"),f"recipes[{recipe_id}].output[{ordinal}]","ItemId",iid,path)

    def ingest_kfc_terraforming(self,path,data):
        rid=self.kfc_resource(data,path)
        for pos,row in enumerate(data.get("terrainConfigs") or []):
            mid=self.value(row.get("terrainMaterial")); self.db.execute("INSERT INTO terrain_configs(id,resource_id,material_id,terrain_item_guid,hardness,health_points,material_feedback_id,metadata_json,source_file,evidence_status) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (pos,rid,mid,row.get("terrainItem"),row.get("hardness"),row.get("healthPoints"),self.value(row.get("materialFeedbackId")),json.dumps(row,sort_keys=True,separators=(",",":")),self.source_name(path),"PROVEN"))
            feedback=self.feedback_resources.get(self.value(row.get("materialFeedbackId"))) if hasattr(self,"feedback_resources") else None
            if feedback: self.db.execute("INSERT INTO resource_relationships(source_resource_id,relationship,target_resource_id,confidence,source_file) VALUES(?,?,?,?,?)",(rid,"terrainConfig.materialFeedback",feedback,"PROVEN",self.source_name(path)))
            target=self.resources.get(("keen::ItemInfo",str(row.get("terrainItem") or "").lower(),0))
            if target: self.db.execute("INSERT INTO resource_relationships(source_resource_id,relationship,target_resource_id,confidence,source_file) VALUES(?,?,?,?,?)",(rid,"terrainConfig.materialItem",target,"PROVEN",self.source_name(path)))
        for pos,row in enumerate(data.get("buildingConfigs") or []):
            mid=self.value(row.get("buildingMaterial")) or self.value(row.get("material")) or self.value(row.get("materialId")); self.db.execute("INSERT INTO building_configs(id,resource_id,material_id,layer,material_item_guid,hardness,health_points,is_roof_block,material_feedback_id,metadata_json,source_file,evidence_status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (pos,rid,mid,pos,row.get("materialItem"),row.get("hardness"),row.get("healthPoints"),1 if row.get("isRoofBlock") else 0 if "isRoofBlock" in row else None,self.value(row.get("materialFeedbackId")),json.dumps(row,sort_keys=True,separators=(",",":")),self.source_name(path),"PROVEN"))
            feedback=self.feedback_resources.get(self.value(row.get("materialFeedbackId"))) if hasattr(self,"feedback_resources") else None
            if feedback: self.db.execute("INSERT INTO resource_relationships(source_resource_id,relationship,target_resource_id,confidence,source_file) VALUES(?,?,?,?,?)",(rid,"buildingConfig.materialFeedback",feedback,"PROVEN",self.source_name(path)))
            target=self.resources.get(("keen::ItemInfo",str(row.get("materialItem") or "").lower(),0))
            if target: self.db.execute("INSERT INTO resource_relationships(source_resource_id,relationship,target_resource_id,confidence,source_file) VALUES(?,?,?,?,?)",(rid,"buildingConfig.materialItem",target,"PROVEN",self.source_name(path)))

    def ingest_kfc_blueprint_config(self,path,data):
        rid=self.kfc_resource(data,path); guid=data.get("$guid"); name=data.get("debugName")
        rules=(data.get("snappingConfig") or {}).get("rules") or []
        for pos,row in enumerate(rules):
            self.db.execute("INSERT INTO blueprint_snap_rules(blueprint_id,config_guid,config_name,rule_guid,ordinal,metadata_json,source_file,evidence_status) VALUES(?,?,?,?,?,?,?,?)",
                (None,guid,name,None,pos,json.dumps(row,sort_keys=True,separators=(",",":")),self.source_name(path),"PROVEN"))

    def ingest_kfc_feedback(self,path,data):
        rid=self.kfc_resource(data,path); fid=self.value(data.get("id")); self.feedback_resources=getattr(self,"feedback_resources",{}); self.feedback_resources[int(fid) if fid is not None else -1]=rid; self.db.execute("INSERT INTO material_feedback(resource_id,feedback_id,debug_name,metadata_json,source_file,evidence_status) VALUES(?,?,?,?,?,?)",
            (rid,fid,data.get("debugName"),json.dumps(data,sort_keys=True,separators=(",",":")),self.source_name(path),"PROVEN"))

    def ingest_kfc_material_layers(self, path, data):
        rid=self.kfc_resource(data,path)
        if isinstance(data.get("materials"), list):
            for layer,row in enumerate(data["materials"]):
                self.db.execute("INSERT INTO material_layers(resource_id,layer,material_id,parameters_json,source_file,evidence_status) VALUES(?,?,?,?,?,?)",
                    (rid,layer,None,json.dumps(row,sort_keys=True,separators=(",",":")),self.source_name(path),"PROVEN"))
        elif data.get("layerCount") is not None:
            for layer in range(int(data.get("layerCount",0))):
                self.db.execute("INSERT INTO material_layers(resource_id,layer,material_id,blend_json,source_file,evidence_status) VALUES(?,?,?,?,?,?)",
                    (rid,layer,layer,json.dumps({"layerCount":data.get("layerCount"),"layerSizeInBytes":data.get("layerSizeInBytes")},sort_keys=True,separators=(",",":")),self.source_name(path),"INFERRED"))
        elif data.get("materialCount") is not None:
            for layer in range(int(data.get("materialCount",0))):
                self.db.execute("INSERT INTO material_layers(resource_id,layer,material_id,gi_json,source_file,evidence_status) VALUES(?,?,?,?,?,?)",
                    (rid,layer,layer,json.dumps({"materialCount":data.get("materialCount")},sort_keys=True,separators=(",",":")),self.source_name(path),"INFERRED"))

    def ingest_kfc_sources(self, root: Path):
        self.item_guid_to_id={}; self.item_ids=set()
        item_files=sorted((root/"ItemInfo").rglob("*.json"))
        for path in item_files:
            data=load_json(path); guid=str(data.get("$guid") or "").lower(); iid=self.value(data.get("itemId"));
            if guid and iid is not None:self.item_guid_to_id[guid]=int(iid)
        self.item_ids=set(self.item_guid_to_id.values())
        for path in item_files:self.ingest_kfc_iteminfo(path,load_json(path))
        for path in sorted((root/"ItemRegistryResource").rglob("*.json")):self.ingest_kfc_item_registry(path,load_json(path))
        for path in sorted((root/"VoxelBlueprintItemRegistryResource").rglob("*.json")):self.ingest_kfc_blueprints(path,load_json(path))
        for path in sorted((root/"RecipeRegistryResource").rglob("*.json")):self.ingest_kfc_recipe(path,load_json(path))
        for path in sorted((root/"MaterialFeedback").rglob("*.json")):self.ingest_kfc_feedback(path,load_json(path))
        for path in sorted((root/"TerraformingEfficiencyRegistryResource").rglob("*.json")):self.ingest_kfc_terraforming(path,load_json(path))
        for path in sorted((root/"VoxelBlueprintConfig").rglob("*.json")):self.ingest_kfc_blueprint_config(path,load_json(path))
        for family in ("BuildingMaterialParametersResource","BuildingMaterialBlendingResource","GiVoxelBuildingMaterialResource"):
            for path in sorted((root/family).rglob("*.json")):self.ingest_kfc_material_layers(path,load_json(path))
        print(f"kfcItemInfo={len(item_files)} kfcBlueprintConfigs={self.db.execute('SELECT COUNT(*) FROM blueprint_snap_rules').fetchone()[0]} kfcRecipes={self.db.execute('SELECT COUNT(*) FROM recipes').fetchone()[0]}")

    def run(self, kfc_root: Path | None = None):
        if kfc_root is not None:
            self.ingest_kfc_sources(kfc_root)
        for path in self.sources:
            name=path.name
            if name=="blueprint_identity_audit.json":self.ingest_blueprint_audit(path,load_json(path))
            elif name=="hammer_category_audit.json":self.ingest_hammer(path,load_json(path))
            elif name=="workbench_reference_audit.json":self.ingest_workbench(path,load_json(path))
            elif name=="ui_reference_audit.json":self.ingest_ui_refs(path,load_json(path))
            elif name=="backend_manifest.json":self.ingest_backend(path,load_json(path))
            elif name=="architect_item_identity_audit.json":
                for row in load_json(path).get("items",[]):self.item(row.get("itemId"),row.get("debugName"),row.get("guid"),path,row.get("category"),row.get("slot"))
            elif name=="architect_wand_v09.txt":self.ingest_wand_text(path,path.read_text(encoding="utf-8-sig"))
            elif name=="SemanticActionObserver-v4.md":self.ingest_research(path,path.read_text(encoding="utf-8-sig"))


def prepare_kfc_sources(root: Path) -> tuple[Path | None, str | None, list[tuple[str, str]]]:
    bundle=root/"data"/"incoming"/"architect_building_kfc_bundle_1076226.zip"
    if not bundle.is_file():
        return None, None, []
    bundle_sha=digest(bundle)
    if bundle_sha != BUNDLE_SHA256:
        raise SystemExit(f"KFC_BUNDLE_MISMATCH: expected {BUNDLE_SHA256}, got {bundle_sha}")
    target=root/"data"/"kfc_sources"/"building_1076226"
    required=("ItemInfo","ItemRegistryResource","RecipeRegistryResource","VoxelBlueprintItemRegistryResource","VoxelBlueprintConfig","TerraformingEfficiencyRegistryResource","BuildingMaterialParametersResource","BuildingMaterialBlendingResource","GiVoxelBuildingMaterialResource","MaterialFeedback")
    if not all(any((target/name).rglob("*.json")) for name in required):
        tmp=target.with_name(target.name+".tmp")
        if tmp.exists(): shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        with zipfile.ZipFile(bundle) as outer:
            for member in sorted(n for n in outer.namelist() if n.lower().endswith(".zip")):
                family=Path(member).stem
                out=tmp/family
                out.mkdir(parents=True,exist_ok=True)
                with zipfile.ZipFile(outer.open(member)) as nested:
                    nested.extractall(out)
        if target.exists(): shutil.rmtree(target)
        tmp.replace(target)
    archive_paths=[(str(bundle.resolve()), bundle_sha)]
    with zipfile.ZipFile(bundle) as outer:
        for name in sorted(n for n in outer.namelist() if n.lower().endswith(".zip")):
            archive_paths.append((f"{bundle.resolve()}!{name}", hashlib.sha256(outer.read(name)).hexdigest().upper()))
    return target, bundle_sha, archive_paths


def source_paths(root: Path) -> list[Path]:
    export=root.parent.parent/"export"/"architect_toolkit"
    names=("architect_item_identity_audit.json","backend_manifest.json","blueprint_identity_audit.json",
           "hammer_category_audit.json","ui_reference_audit.json","workbench_reference_audit.json",
           "architect_wand_v09.txt")
    result=[export/name for name in names if (export/name).is_file()]
    research=root/"docs"/"research"/"SemanticActionObserver-v4.md"
    if research.is_file():result.append(research)
    return sorted(result,key=lambda p:str(p).lower())


def build(output: Path, root: Path, replace_incompatible=False):
    exe=root.parent.parent/"enshrouded.exe"
    if digest(exe)!=EXE_SHA256:raise SystemExit("BUILD_MISMATCH: enshrouded.exe is not revision 1076226")
    if output.exists():
        try:
            old=sqlite3.connect(output); row=old.execute("SELECT revision,executable_sha256,schema_version FROM builds").fetchone();old.close()
        except sqlite3.Error:row=None
        if row and row!=(REVISION,EXE_SHA256,SCHEMA_VERSION) and not replace_incompatible:
            raise SystemExit(f"INCOMPATIBLE_EXISTING_INDEX: {row}")
    kfc_root,bundle_sha,kfc_inputs=prepare_kfc_sources(root)
    sources=source_paths(root); output.parent.mkdir(parents=True,exist_ok=True)
    temp=output.with_suffix(output.suffix+".tmp")
    if temp.exists():temp.unlink()
    db=sqlite3.connect(temp);db.executescript((Path(__file__).with_name("schema.sql")).read_text(encoding="utf-8"))
    newest=max([p.stat().st_mtime for p in sources]+[exe.stat().st_mtime])
    generated=datetime.fromtimestamp(newest,tz=timezone.utc).isoformat().replace("+00:00","Z")
    db.execute("INSERT INTO builds VALUES(1,?,?,?,?,?,?,?)",(REVISION,EXE_SHA256,None,None,SCHEMA_VERSION,generated,bundle_sha))
    for path in [exe,*sources]:db.execute("INSERT OR IGNORE INTO input_sources(build_id,path,sha256,kind) VALUES(1,?,?,?)",(str(path.resolve()),digest(path),"executable" if path==exe else "local_export_or_research"))
    for label,sha in kfc_inputs:db.execute("INSERT OR IGNORE INTO input_sources(build_id,path,sha256,kind) VALUES(1,?,?,?)",(label,sha,"kfc_bundle"))
    Builder(db,root,sources).run(kfc_root)
    for family in FAMILIES:
        count=db.execute(f"SELECT COUNT(*) FROM {family}").fetchone()[0]
        limitation="locally audited records indexed" if count else "no verified local export for this family; schema reserved, no records invented"
        db.execute("INSERT INTO coverage(family,status,row_count,limitation) VALUES(?,?,?,?)",(family,"AVAILABLE_PARTIAL" if count else "UNAVAILABLE",count,limitation))
    db.commit();db.execute("VACUUM");db.close();os.replace(temp,output)
    return output


def main():
    root=Path(__file__).resolve().parents[2]
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=root/"data"/"architect_game_data_1076226.sqlite");p.add_argument("--replace-incompatible",action="store_true");a=p.parse_args()
    path=build(a.output.resolve(),root,a.replace_incompatible);print(path);print(f"sha256={digest(path)}")
if __name__=="__main__":main()
