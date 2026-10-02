"""Read-only Enshrouded KFC archive index. No game/Drive writes.

All extracted field interpretations are scoped to the source archive fingerprint.
Do not infer EML runtime layouts from these static JSON exports.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

SUPPORTED = (
    "ItemInfo", "ItemRegistryResource", "RecipeRegistryResource",
    "ItemKnowledgeResource", "WorkshopRegistryResource",
    "GuidRegistryResource", "LocaTagCollectionResource",
    "VoxelBlueprintItemRegistryResource", "VoxelBlueprintMaterialPoolRegistryResource",
    "BuildingMaterialParametersResource", "ColorPaletteCollectionResource",
    "CharacterPresetCollection", "RenderMaterialResource", "RenderTextureResource",
    "UiTextureResource", "ModelHierarchyResource", "RenderModelChunkModelResource",
    "TemplateCollectionResource", "GameKnowledgeResource",
    "BuildingMaterialBlendingResource", "GiVoxelBuildingMaterialResource",
    "WorldMaterialBlending2Resource", "VoxelModelResource", "SimpleWorldMaterialResource",
    "MidiSongResource", "MidiSongCollection",
)
SCHEMA_VERSION = 1
MAX_MEMBER_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_UNPACKED = 512 * 1024 * 1024
GUID_RE = re.compile(r"^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$", re.I)


class CatalogError(RuntimeError):
    pass


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def as_id(value: Any) -> int | None:
    if isinstance(value, dict):
        value = value.get("value")
    if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 0xFFFFFFFF:
        return value
    return None


def normalize_guid(value: Any) -> str | None:
    if isinstance(value, str) and GUID_RE.fullmatch(value):
        return value.lower()
    return None


def _members(z: zipfile.ZipFile) -> Iterator[zipfile.ZipInfo]:
    items = [i for i in z.infolist() if not i.is_dir() and i.filename.lower().endswith(".json")]
    if sum(i.file_size for i in items) > MAX_ARCHIVE_UNPACKED:
        raise CatalogError("archive exceeds uncompressed safety limit")
    for info in items:
        if info.file_size > MAX_MEMBER_BYTES:
            raise CatalogError(f"member too large: {info.filename}")
        # We read JSON bytes only; no archive extraction and no path traversal.
        yield info


def load_members(archive: Path) -> Iterator[tuple[str, dict]]:
    with zipfile.ZipFile(archive) as z:
        for info in _members(z):
            try:
                obj = json.loads(z.read(info).decode("utf-8-sig"))
            except (ValueError, UnicodeError, RuntimeError) as exc:
                raise CatalogError(f"invalid JSON: {archive.name}:{info.filename}: {exc}") from exc
            if not isinstance(obj, dict):
                raise CatalogError(f"expected resource object: {info.filename}")
            yield info.filename, obj


def connect(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    PRAGMA foreign_keys=ON;
    CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS sources(
        archive TEXT PRIMARY KEY, sha256 TEXT NOT NULL, member_count INTEGER NOT NULL,
        indexed_utc TEXT NOT NULL, kfc_root TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS items(
        guid TEXT PRIMARY KEY, item_id INTEGER, debug_name TEXT, category TEXT,
        name_loca TEXT, description_loca TEXT, icon_image TEXT, icon_model TEXT,
        block_setup_json TEXT, archive TEXT NOT NULL, member TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS registry(
        guid TEXT PRIMARY KEY, debug_name TEXT, position INTEGER NOT NULL,
        archive TEXT NOT NULL, member TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS recipes(
        guid TEXT PRIMARY KEY, recipe_id INTEGER, debug_name TEXT,
        workshop_id INTEGER, workshop_guid TEXT, knowledge_json TEXT,
        ingredients_json TEXT NOT NULL, outputs_json TEXT NOT NULL,
        archive TEXT NOT NULL, member TEXT NOT NULL, position INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS knowledge(
        item_id INTEGER PRIMARY KEY, locked_mask_json TEXT, body_json TEXT,
        archive TEXT NOT NULL, member TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS workshops(
        workshop_id INTEGER PRIMARY KEY, guid TEXT, item_ref TEXT, name_id INTEGER,
        archive TEXT NOT NULL, member TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS extra_resources(
        resource_type TEXT, guid TEXT, member TEXT, archive TEXT,
        top_keys_json TEXT, PRIMARY KEY(archive,member)
    );
    CREATE INDEX IF NOT EXISTS idx_itemid ON items(item_id);
    CREATE INDEX IF NOT EXISTS idx_debugname ON registry(debug_name);
    CREATE INDEX IF NOT EXISTS idx_recipes_workshop ON recipes(workshop_id);
    """)
    return conn


def index_archives(kfc_dir: Path, db: Path, on_progress=None) -> dict[str, Any]:
    """Replace only this app's derived SQLite index, never source archives.

    Existing DB is preserved on input validation errors via a transaction.
    """
    kfc_dir = kfc_dir.expanduser().resolve()
    db = db.expanduser().resolve()
    if not kfc_dir.is_dir():
        raise CatalogError(f"KFC directory not found: {kfc_dir}")
    if db == kfc_dir or kfc_dir in db.parents:
        raise CatalogError("derived database must be outside the read-only KFC directory")
    paths = [(name, kfc_dir / (name + ".zip")) for name in SUPPORTED]
    missing = [name for name, path in paths if not path.is_file()]
    required = ("ItemInfo", "ItemRegistryResource", "RecipeRegistryResource", "ItemKnowledgeResource", "WorkshopRegistryResource")
    required_missing = [name for name in required if name in missing]
    if required_missing:
        raise CatalogError("missing required archives: " + ", ".join(required_missing))

    conn = connect(db)
    counts: dict[str, int] = {}
    try:
        with conn:
            for tbl in ("sources", "items", "registry", "recipes", "knowledge", "workshops", "extra_resources"):
                conn.execute("DELETE FROM " + tbl)
            for name, path in paths:
                if name in missing:
                    continue
                if on_progress:
                    on_progress("Indexing " + name)
                sha = hash_file(path)
                n = 0
                for member, obj in load_members(path):
                    n += 1
                    if name == "ItemInfo":
                        guid = normalize_guid(obj.get("$guid") or obj.get("objectId"))
                        if guid is None:
                            raise CatalogError(f"ItemInfo missing/invalid GUID: {member}")
                        conn.execute("""INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (
                            guid, as_id(obj.get("itemId")), obj.get("debugName"), obj.get("category"),
                            obj.get("name"), obj.get("description"), obj.get("iconImage"),
                            obj.get("iconModel"), json.dumps(obj.get("blockSetup")), name, member,
                        ))
                    elif name == "ItemRegistryResource":
                        refs = obj.get("itemRefs") or []
                        names = obj.get("dbgNames") or []
                        if len(refs) != len(names):
                            raise CatalogError("itemRefs/dbgNames registry lengths differ; no positional join")
                        for idx, (ref, dbg) in enumerate(zip(refs, names)):
                            guid = normalize_guid(ref)
                            if guid:
                                conn.execute("INSERT INTO registry VALUES (?,?,?,?,?)",
                                             (guid, dbg, idx, name, member))
                    elif name == "RecipeRegistryResource":
                        for idx, recipe in enumerate(obj.get("recipes") or []):
                            guid = normalize_guid(recipe.get("recipeGuid"))
                            if not guid:
                                raise CatalogError(f"recipe missing GUID at index {idx}")
                            conn.execute("INSERT INTO recipes VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
                                guid, as_id(recipe.get("recipeId")), recipe.get("debugName"),
                                as_id(recipe.get("workshopId")), normalize_guid(recipe.get("workshopGuid")),
                                json.dumps(recipe.get("knowledgeRequirement")),
                                json.dumps(recipe.get("input") or []), json.dumps(recipe.get("output") or []),
                                name, member, idx,
                            ))
                    elif name == "ItemKnowledgeResource":
                        for rec in obj.get("knowledgeArray") or []:
                            iid = as_id(rec.get("itemId"))
                            if iid is not None:
                                conn.execute("INSERT OR REPLACE INTO knowledge VALUES (?,?,?,?,?)",
                                    (iid, json.dumps(rec.get("lockedKnowledgeMask")), json.dumps(rec), name, member))
                    elif name == "WorkshopRegistryResource":
                        for ws in obj.get("workshops") or []:
                            iid = as_id(ws.get("workshopId"))
                            if iid is not None:
                                conn.execute("INSERT OR REPLACE INTO workshops VALUES (?,?,?,?,?,?)", (
                                    iid, normalize_guid(ws.get("workshopGuid")), normalize_guid(ws.get("itemRef")),
                                    as_id(ws.get("name")), name, member,
                                ))
                    else:
                        conn.execute("INSERT INTO extra_resources VALUES (?,?,?,?,?)", (
                            name, normalize_guid(obj.get("$guid")), member, name,
                            json.dumps([k for k in obj if not k.startswith("$")]),
                        ))
                counts[name] = n
                conn.execute("INSERT INTO sources VALUES (?,?,?,?,?)",
                             (name, sha, n, datetime.now(timezone.utc).isoformat(), str(kfc_dir)))
            conn.execute("INSERT OR REPLACE INTO meta VALUES ('schema_version',?)", (str(SCHEMA_VERSION),))
            conn.execute("INSERT OR REPLACE INTO meta VALUES ('kfc_root',?)", (str(kfc_dir),))
    finally:
        conn.close()
    return {"source_archives": counts, "optional_missing": [n for n in missing if n not in required],
            "db": str(db), "kfc_root": str(kfc_dir)}


def _require_index(conn: sqlite3.Connection) -> None:
    if not conn.execute("SELECT 1 FROM sources LIMIT 1").fetchone():
        raise CatalogError("catalog not indexed; run index first")


def search_items(db: Path, term: str, limit=100) -> list[dict]:
    conn = connect(db)
    try:
        _require_index(conn)
        term = "%%" + term.lower().replace("%", "\\%").replace("_", "\\_") + "%%"
        rows = conn.execute("""SELECT i.guid,i.item_id,COALESCE(r.debug_name,i.debug_name) AS debug_name,
                                   i.category, i.name_loca, i.icon_model, i.icon_image,
                                   CASE WHEN r.guid IS NOT NULL THEN 1 ELSE 0 END in_registry
                                   FROM items i LEFT JOIN registry r USING(guid)
                                   WHERE LOWER(COALESCE(r.debug_name,i.debug_name,'')) LIKE ? ESCAPE '\\'
                                     OR LOWER(COALESCE(i.category,'')) LIKE ? ESCAPE '\\'
                                     OR CAST(i.item_id AS TEXT) LIKE ? ESCAPE '\\'
                                   ORDER BY in_registry DESC, debug_name COLLATE NOCASE LIMIT ?""",
                            (term, term, term, min(max(int(limit), 1), 500))).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_item(db: Path, identity: str | int) -> dict:
    conn = connect(db)
    try:
        _require_index(conn)
        if isinstance(identity, int) or str(identity).isdigit():
            where, val = "i.item_id=?", int(identity)
        else:
            where, val = "i.guid=?", str(identity).lower()
        row = conn.execute(f"""SELECT i.*,COALESCE(r.debug_name,i.debug_name) AS resolved_name,
                              CASE WHEN r.guid IS NULL THEN 0 ELSE 1 END AS in_registry,
                              k.body_json AS knowledge_json
                              FROM items i LEFT JOIN registry r USING(guid)
                              LEFT JOIN knowledge k ON k.item_id=i.item_id
                              WHERE {where}""", (val,)).fetchone()
        if row is None:
            raise CatalogError(f"unknown ItemInfo item: {identity}")
        item = dict(row)
        item["knowledge"] = json.loads(item.pop("knowledge_json")) if item["knowledge_json"] else None
        item["block_setup"] = json.loads(item.pop("block_setup_json"))
        recipes = []
        # The recipe JSON is preserved only as compact inputs/outputs, not source mutation.
        for recipe in conn.execute("SELECT * FROM recipes"):
            outputs = json.loads(recipe["outputs_json"])
            if any(normalize_guid(o.get("itemRef")) == item["guid"] or as_id(o.get("item")) == item["item_id"]
                   for o in outputs):
                d = dict(recipe)
                d["ingredients"] = json.loads(d.pop("ingredients_json"))
                d["outputs"] = json.loads(d.pop("outputs_json"))
                d["knowledge_requirement"] = json.loads(d.pop("knowledge_json"))
                recipes.append(d)
        item["producing_recipes"] = recipes
        item["observed_visual_resource_matches"] = {}
        for key, value in (("icon_image", item["icon_image"]),
                           ("icon_model", item["icon_model"])):
            guid = normalize_guid(value)
            if guid:
                item["observed_visual_resource_matches"][key] = [
                    dict(r) for r in conn.execute(
                        "SELECT resource_type,guid,archive,member FROM extra_resources WHERE guid=?",
                        (guid,))
                ]
        return item
    finally:
        conn.close()


def diagnostics(db: Path) -> dict:
    conn = connect(db)
    try:
        _require_index(conn)
        cnt = lambda t: conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
        reg_missing = conn.execute("""SELECT COUNT(*) FROM registry r LEFT JOIN items i ON r.guid=i.guid
                                      WHERE i.guid IS NULL""").fetchone()[0]
        items_not_in_reg = conn.execute("""SELECT COUNT(*) FROM items i LEFT JOIN registry r USING(guid)
                                           WHERE r.guid IS NULL""").fetchone()[0]
        dup_ids = [dict(x) for x in conn.execute("""SELECT item_id, COUNT(*) AS n FROM items
                                   WHERE item_id IS NOT NULL GROUP BY item_id HAVING n>1 LIMIT 25""")]
        ids = {x[0] for x in conn.execute("SELECT item_id FROM items WHERE item_id IS NOT NULL")}
        guids = {x[0] for x in conn.execute("SELECT guid FROM items")}
        missing_in, missing_out, examined_in, examined_out = {}, {}, 0, 0
        contradictory_refs = []
        guid_ids = {r[0]: r[1] for r in conn.execute("SELECT guid,item_id FROM items")}
        for r in conn.execute("SELECT guid,ingredients_json,outputs_json FROM recipes"):
            for kind, key, missing in (("in", "ingredients_json", missing_in), ("out", "outputs_json", missing_out)):
                elements = json.loads(r[key]); stacks = [x.get("itemStack", {}) if kind == "in" else x for x in elements]
                for entry in stacks:
                    # Category ingredients without explicit item id are valid and tracked separately.
                    iid = as_id(entry.get("item")); guid = normalize_guid(entry.get("itemRef"))
                    if (iid is None or iid == 0) and not guid:
                        continue
                    if kind == "in": examined_in += 1
                    else: examined_out += 1
                    if guid in guid_ids and iid and guid_ids[guid] not in (None, iid):
                        contradictory_refs.append({
                            "recipe_guid": r["guid"], "direction": kind,
                            "item_guid": guid, "declared_item_id": iid,
                            "catalog_item_id": guid_ids[guid],
                        })
                    if (guid and guid in guids) or (iid and iid in ids):
                        continue
                    missing[r["guid"]] = missing.get(r["guid"], 0) + 1
        return {"indexed_archives": [dict(r) for r in conn.execute("SELECT * FROM sources ORDER BY archive")],
                "item_info": cnt("items"), "registered_items": cnt("registry"),
                "recipes": cnt("recipes"), "knowledge_entries": cnt("knowledge"),
                "workshops": cnt("workshops"),
                "registered_without_iteminfo": reg_missing, "iteminfo_not_registered": items_not_in_reg,
                "duplicate_numeric_item_ids_sample": dup_ids,
                "recipe_inputs_examined": examined_in, "recipe_outputs_examined": examined_out,
                "recipes_with_unresolved_ingredient_refs": len(missing_in),
                "recipes_with_unresolved_output_refs": len(missing_out),
                "unresolved_ingredient_recipe_guids_sample": list(missing_in)[:20],
                "unresolved_output_recipe_guids_sample": list(missing_out)[:20],
                "contradictory_guid_numeric_refs": len(contradictory_refs),
                "contradictory_guid_numeric_refs_sample": contradictory_refs[:20],
                "note": "Static reference coverage only. An unresolved reference may be an external/partial resource, not necessarily a game error."}
    finally:
        conn.close()


def load_raw_resource(db: Path, archive: str, member: str) -> dict:
    conn = connect(db)
    try:
        _require_index(conn)
        src = conn.execute("SELECT * FROM sources WHERE archive=?", (archive,)).fetchone()
        if src is None:
            raise CatalogError("archive not indexed: " + archive)
        path = Path(src["kfc_root"]) / (archive + ".zip")
        if hash_file(path) != src["sha256"]:
            raise CatalogError("source archive fingerprint changed: re-index before reading")
        with zipfile.ZipFile(path) as z:
            names = {i.filename for i in _members(z)}
            if member not in names:
                raise CatalogError("indexed resource missing from source archive")
            return json.loads(z.read(member).decode("utf-8-sig"))
    finally:
        conn.close()
