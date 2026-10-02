"""Evidence-backed one-item graphs and fail-closed static validation."""
from __future__ import annotations
import json
from pathlib import Path
from .catalog import connect, get_item, normalize_guid, as_id, CatalogError

REQUIRED = ("ItemInfo", "ItemRegistryResource", "RecipeRegistryResource", "ItemKnowledgeResource", "WorkshopRegistryResource")

def _evidence(archive, member, field, value, status="PROVEN"):
    return {"status": status, "archive": archive, "member": member, "field_path": field, "value": value}

def build_graph(db: Path, identity: str | int) -> dict:
    item = get_item(db, identity)
    if not item["in_registry"]:
        raise CatalogError("selected item is not registered")
    conn = connect(db)
    try:
        reg = conn.execute("SELECT * FROM registry WHERE guid=?", (item["guid"],)).fetchall()
        recipe = item["producing_recipes"]
        if len(recipe) != 1:
            raise CatalogError(f"selected item has {len(recipe)} producing recipes; unique recipe required")
        r = recipe[0]
        ws = conn.execute("SELECT * FROM workshops WHERE workshop_id=?", (r["workshop_id"],)).fetchone()
        nodes = {
            "ItemInfo": {"identity": item["guid"], "item_id": item["item_id"], "source": _evidence(item["archive"], item["member"], "$guid/itemId", item["guid"])},
            "ItemRegistryResource": {"identity": item["guid"], "source": _evidence(reg[0]["archive"], reg[0]["member"], f"itemRefs[{reg[0]['position']}]", item["guid"])},
            "RecipeRegistryResource": {"identity": r["guid"], "recipe_id": r["recipe_id"], "source": _evidence(r["archive"], r["member"], f"recipes[{r['position']}]", r["guid"]), "inputs": r["ingredients"], "outputs": r["outputs"]},
            "ItemKnowledgeResource": {"item_id": item["item_id"], "source": _evidence("ItemKnowledgeResource", "knowledgeArray", "knowledgeArray[].itemId", item["item_id"]) if item["knowledge"] else None},
            "WorkshopRegistryResource": {"workshop_id": r["workshop_id"], "source": _evidence(ws["archive"], ws["member"], "workshops[].workshopId", r["workshop_id"]) if ws else None},
            "localization": {"name": _evidence(item["archive"], item["member"], "name", item["name_loca"])},
            "visual": {"icon_model": _evidence(item["archive"], item["member"], "iconModel", item["icon_model"]) if item["icon_model"] else None, "icon_image": _evidence(item["archive"], item["member"], "iconImage", item["icon_image"]) if item["icon_image"] else None},
        }
        return {"format": "control-center-2/evidence-graph/v1", "item": item["debug_name"], "item_guid": item["guid"], "game_build": "UNKNOWN", "eml_version": "UNKNOWN", "nodes": nodes, "validation": validate_graph(nodes)}
    finally: conn.close()

def validate_graph(graph: dict) -> dict:
    issues=[]
    for name in REQUIRED:
        if not graph.get(name, {}).get("source"): issues.append({"code":"MISSING_DEPENDENCY","node":name})
    r=graph.get("RecipeRegistryResource", {})
    if not r.get("outputs"): issues.append({"code":"MISSING_OUTPUT","node":"RecipeRegistryResource"})
    for direction, entries in (("input",r.get("inputs",[])),("output",r.get("outputs",[]))):
        for i,e in enumerate(entries):
            s=e.get("itemStack",e); ref=normalize_guid(s.get("itemRef")); iid=as_id(s.get("item"))
            if not ref and not iid: issues.append({"code":"UNRESOLVED_REFERENCE","direction":direction,"index":i})
    return {"status":"PASS" if not issues else "FAIL", "issues":issues, "fail_closed":True}

def markdown_report(graph: dict) -> str:
    lines=[f"# Static dependency graph: {graph['item']}", "", f"- Item GUID: `{graph['item_guid']}`", f"- Game build: **{graph['game_build']}**", f"- EML version: **{graph['eml_version']}**", f"- Validation: **{graph['validation']['status']}**", "", "| Node | Status | Source | Field |", "|---|---|---|---|"]
    for name,node in graph["nodes"].items():
        src=node.get("source")
        lines.append(f"| {name} | {src.get('status','UNSOLVED') if src else 'UNSOLVED'} | {src.get('archive','') if src else ''}/{src.get('member','') if src else ''} | `{src.get('field_path','') if src else ''}` |")
    lines += ["", "## Evidence classification", "", "- **PROVEN:** observed in the indexed KFC snapshot and linked by actual GUID/item ID fields.", "- **INFERRED:** a complete custom item likely needs coordinated registration, recipe, knowledge, workshop, localization, and visual dependencies.", "- **EXPERIMENTAL:** runtime creation, registration timing, ID allocation, and API signatures.", "- **UNSOLVED:** game build and installed EML version; no runtime mutation is authorized."]
    return "\n".join(lines)+"\n"
