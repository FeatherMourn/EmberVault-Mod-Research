"""Schema cache.

Caches the parsed :class:`TypeDatabase` as JSON so subsequent startups are
faster. The cache key includes the SHA-256 of ``types.lua``; if the hash
changes, the cache is rebuilt.
"""

from __future__ import annotations

import json
import os

from .provenance import sha256_file
from .schema_model import (
    AliasDefinition,
    ClassDefinition,
    FieldDefinition,
    TypeDatabase,
)
from .schema_parser import parse_types_lua_file
from .type_parser import parse_type_expression


def types_lua_hash(types_path: str) -> str:
    digest = sha256_file(types_path)
    if digest is None:
        return ""
    return digest


def _cache_path_for(cache_dir: str, hash_value: str) -> str:
    return os.path.join(cache_dir, "types_%s.json" % hash_value)


def _db_to_cache(db: TypeDatabase) -> dict:
    return {
        "schema": "architect.lua_config_lab.schema_cache.v1",
        "classes": [
            {
                "name": cls.name,
                "parent": cls.parent,
                "fields": [
                    {"name": f.name, "type": f.declared_type}
                    for f in cls.fields
                ],
            }
            for cls in db.classes.values()
        ],
        "aliases": [
            {"name": alias.name, "choices": alias.choices}
            for alias in db.aliases.values()
        ],
    }


def _db_from_cache(data: dict) -> TypeDatabase:
    db = TypeDatabase()
    for entry in data["classes"]:
        cls = ClassDefinition(name=entry["name"], parent=entry.get("parent"))
        for field in entry["fields"]:
            raw_type = field["type"]
            cls.fields.append(
                FieldDefinition(
                    name=field["name"],
                    declared_type=raw_type,
                    type_expr=parse_type_expression(raw_type),
                    owner_class=entry["name"],
                )
            )
        db.add_class(cls)
    for entry in data["aliases"]:
        db.add_alias(
            AliasDefinition(name=entry["name"], choices=list(entry["choices"]))
        )
    return db


def load_or_build(
    types_path: str,
    cache_dir: str,
    force_rebuild: bool = False,
) -> TypeDatabase:
    """Return a :class:`TypeDatabase`, using the cache when valid."""
    hash_value = types_lua_hash(types_path)
    if not hash_value:
        raise FileNotFoundError("types.lua not found at %r" % types_path)

    cache_path = _cache_path_for(cache_dir, hash_value)
    if not force_rebuild and os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as handle:
                return _db_from_cache(json.load(handle))
        except (json.JSONDecodeError, KeyError, OSError, TypeError):
            pass  # fall through and rebuild

    db = parse_types_lua_file(types_path)
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as handle:
        json.dump(_db_to_cache(db), handle, ensure_ascii=False)
    return db
