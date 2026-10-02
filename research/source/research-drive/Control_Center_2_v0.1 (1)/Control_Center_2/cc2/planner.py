"""Validate and export non-deployable experimental new-item plans.

No invented Enshrouded numeric IDs, runtime hooks, API calls or JSON schemas.
"""
from __future__ import annotations
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from .catalog import CatalogError, connect, get_item, normalize_guid, as_id

SLUG = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


def plan_new_item(db: Path, vanilla_identity: str | int, *, slug: str, name: str,
                  recipe_guid: str | None = None, notes: str = "") -> dict:
    if not SLUG.fullmatch(slug):
        raise CatalogError("slug must be 3–64 lowercase alphanumeric/underscore chars, starting with a letter")
    if not name.strip() or len(name.strip()) > 120:
        raise CatalogError("display name must be 1–120 characters")
    base = get_item(db, vanilla_identity)
    if not base["in_registry"]:
        raise CatalogError("base item is not in observed ItemRegistryResource; choose a registered vanilla item")
    recipes = base["producing_recipes"]
    if recipe_guid:
        chosen = [r for r in recipes if r["guid"] == recipe_guid.lower()]
        if not chosen:
            raise CatalogError("recipe GUID does not produce the selected vanilla item")
        recipe = chosen[0]
    else:
        recipe = recipes[0] if len(recipes) == 1 else None
    proposed_item_guid = str(uuid.uuid4())
    proposed_recipe_guid = str(uuid.uuid4()) if recipe else None
    graph = {
        "ItemInfo": {"source_guid": base["guid"], "proposed_guid": proposed_item_guid,
                     "observed_numeric_item_id": base["item_id"], "new_numeric_item_id": None,
                     "name_loca_source": base["name_loca"], "icon_image": base["icon_image"],
                     "icon_model": base["icon_model"], "category": base["category"]},
        "ItemRegistryResource": {"source_item_registered": bool(base["in_registry"]),
                                 "proposed_item_guid": proposed_item_guid, "new_entry_verified": False},
        "ItemKnowledgeResource": {"source_entry_present": base["knowledge"] is not None,
                                  "proposed_entry_verified": False},
        "RecipeRegistryResource": None,
    }
    if recipe:
        graph["RecipeRegistryResource"] = {
            "source_guid": recipe["guid"], "proposed_guid": proposed_recipe_guid,
            "workshop_id": recipe["workshop_id"], "source_recipe_id": recipe["recipe_id"],
            "new_numeric_recipe_id": None, "input": recipe["ingredients"],
            "output": recipe["outputs"], "source_recipe_position": recipe["position"]
        }
    source_archive_info = []
    conn = connect(db)
    try:
        for r in conn.execute("SELECT archive,sha256,member_count,indexed_utc,kfc_root FROM sources ORDER BY archive"):
            source_archive_info.append(dict(r))
    finally:
        conn.close()
    blockers = [
        "Confirm EML version/build and supported resource registration APIs by observation.",
        "Determine safe new numeric itemId allocation; a random GUID alone is insufficient evidence.",
        "Validate ItemInfo creation and independent registry insertion at runtime.",
        "Validate localization binding and crafting/knowledge visibility.",
        "Test in an isolated disposable world with all other custom-content modules disabled.",
    ]
    if recipe is None:
        blockers.append("Choose a known producing recipe by GUID or a different vanilla item; this item has "
                        + str(len(recipes)) + " observed producing recipes.")
    else:
        blockers.append("Determine numeric recipeId allocation and confirm workshop/knowledge registration for selected recipe.")
    return {
        "format": "control-center-2/new-item-plan/v0.1", "status": "EXPERIMENTAL_NOT_DEPLOYABLE",
        "created_utc": datetime.now(timezone.utc).isoformat(), "slug": slug,
        "display_name": name.strip(), "notes": notes,
        "source_item": {"guid": base["guid"], "item_id": base["item_id"],
                        "debug_name": base["resolved_name"], "category": base["category"],
                        "archive": base["archive"], "member": base["member"]},
        "proposed_item_guid": proposed_item_guid,
        "observed_producing_recipes": [
            {"guid": r["guid"], "debug_name": r["debug_name"], "workshop_id": r["workshop_id"]}
            for r in recipes
        ],
        "resource_graph": graph, "source_archive_fingerprints": source_archive_info,
        "blockers": blockers,
        "safety": {"original_control_center_untouched": True, "kfc_read_only": True,
                   "no_eml_deploy": True, "no_game_mutation": True},
    }


def save_plan(plan: dict, destination: Path) -> Path:
    if plan.get("status") != "EXPERIMENTAL_NOT_DEPLOYABLE":
        raise CatalogError("only experimental non-deployable plans are supported")
    destination = destination.expanduser().resolve()
    # A plan must never be written into any original KFC source folder.
    for source in plan.get("source_archive_fingerprints", []):
        kfc_root = source.get("kfc_root")
        if kfc_root:
            root = Path(kfc_root).expanduser().resolve()
            if destination == root or root in destination.parents:
                raise CatalogError("refusing to write a plan inside a KFC source folder")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise CatalogError(f"refusing to overwrite an existing plan: {destination}")
    # No deployment path accepted. Caller controls output workspace.
    with destination.open("x", encoding="utf-8") as out:
        json.dump(plan, out, indent=2, ensure_ascii=False)
        out.write("\n")
    return destination
