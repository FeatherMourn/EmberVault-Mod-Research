"""Read-only migration diagnostics for old Control Center definitions.

Never import or execute legacy Python; inspect its AST and validate referenced
numeric IDs against the KFC-derived index. This does not modify the old app.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from .catalog import CatalogError, connect, _require_index, as_id


def audit_legacy(db: Path, *, importer: Path | None = None,
                 registry: Path | None = None) -> dict:
    if importer is None and registry is None:
        raise CatalogError("supply a path to at least one legacy importer or registry")
    result = {"status": "STATIC_SOURCE_AUDIT", "legacy_modified": False,
              "ingredient_presets": [], "registry_ingredients": [],
              "warnings": ["Presence in static KFC exports does not establish current-game build compatibility."]}
    conn = connect(db)
    try:
        _require_index(conn)
        def look(iid: object, label: str, source: str) -> dict:
            value = as_id(iid)
            if value is None:
                return {"label": label, "provided_item_id": iid, "state": "INVALID_ID", "source": source}
            rows = conn.execute("SELECT guid,debug_name,category FROM items WHERE item_id=?", (value,)).fetchall()
            return {"label": label, "provided_item_id": value,
                    "state": "FOUND_IN_EXPORTED_ITEMINFO" if rows else "NOT_IN_EXPORTED_ITEMINFO",
                    "matches": [dict(row) for row in rows], "source": source}
        if importer is not None:
            source = importer.expanduser().resolve()
            tree = ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(source))
            presets = None
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "MATERIAL_PRESETS":
                            presets = ast.literal_eval(node.value)
            if presets is None or not isinstance(presets, dict):
                raise CatalogError("legacy importer contains no literal MATERIAL_PRESETS map")
            result["ingredient_presets"] = [look(v, str(k), str(source)) for k,v in presets.items()]
        if registry is not None:
            source = registry.expanduser().resolve()
            records = json.loads(source.read_text(encoding="utf-8-sig"))
            if not isinstance(records, list):
                raise CatalogError("legacy registry expected a list of item definitions")
            for rec in records:
                for ingredient in rec.get("ingredients") or []:
                    result["registry_ingredients"].append(look(
                        ingredient.get("itemId"), ingredient.get("name", "(unnamed)"),
                        str(source) + "#" + str(rec.get("id", "unknown"))))
        for key in ("ingredient_presets", "registry_ingredients"):
            result[key + "_missing"] = sum(x["state"] != "FOUND_IN_EXPORTED_ITEMINFO" for x in result[key])
        return result
    finally:
        conn.close()
