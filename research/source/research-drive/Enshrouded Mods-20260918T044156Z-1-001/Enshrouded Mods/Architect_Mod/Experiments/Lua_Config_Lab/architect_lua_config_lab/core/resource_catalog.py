"""Resource catalog: the user-facing metadata layer over the 131 KFC roots.

`known_resource_roots.json` remains the technical identity/source list. This
module loads `resource_catalog.json`, which adds friendly names, categories,
descriptions and tags, and provides search/lookup helpers.

The catalog is validated against the technical root list and the live schema;
validation fails closed if they become inconsistent.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field as dc_field
from typing import Dict, List, Optional

# Approved primary categories (the user-facing taxonomy).
CATEGORIES = [
    "Building & Blueprints",
    "Player & Game Balance",
    "Items & Inventory",
    "Crafting & Progression",
    "Combat, Enemies & Buffs",
    "World, Time & Survival",
    "Weather & Environment",
    "Terrain, Water & Materials",
    "Camera & Movement",
    "Map, Knowledge & Navigation",
    "Characters, NPCs & Customization",
    "UI & Interface",
    "Audio, Music & Voice",
    "Visuals, Rendering & Effects",
    "Animation & Sequences",
    "Developer, System & Advanced",
]

ACCESS_LEVELS = {"STANDARD", "ADVANCED"}


def _package_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_catalog_path() -> str:
    return os.path.join(_package_dir(), "data", "resource_catalog.json")


@dataclass
class CatalogEntry:
    resource_type: str
    family: str
    friendly_name: str
    primary_category: str
    description: str
    tags: List[str] = dc_field(default_factory=list)
    access_level: str = "STANDARD"
    friendly_controls_available: bool = False

    @staticmethod
    def from_dict(data: Dict) -> "CatalogEntry":
        return CatalogEntry(
            resource_type=data.get("resource_type", ""),
            family=data.get("family", ""),
            friendly_name=data.get("friendly_name", ""),
            primary_category=data.get("primary_category", ""),
            description=data.get("description", ""),
            tags=list(data.get("tags", [])),
            access_level=data.get("access_level", "STANDARD"),
            friendly_controls_available=bool(data.get("friendly_controls_available", False)),
        )

    def to_dict(self) -> Dict:
        return {
            "resource_type": self.resource_type,
            "family": self.family,
            "friendly_name": self.friendly_name,
            "primary_category": self.primary_category,
            "description": self.description,
            "tags": list(self.tags),
            "access_level": self.access_level,
            "friendly_controls_available": self.friendly_controls_available,
        }


class ResourceCatalog:
    def __init__(self, entries: List[CatalogEntry]) -> None:
        self.entries = entries
        self._by_resource_type = {e.resource_type: e for e in entries}
        self._by_family = {e.family: e for e in entries}

    # -- loading -------------------------------------------------------------

    @staticmethod
    def load(path: Optional[str] = None) -> "ResourceCatalog":
        path = path or default_catalog_path()
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        raw_entries = data.get("entries", data if isinstance(data, list) else [])
        entries = [CatalogEntry.from_dict(item) for item in raw_entries]
        return ResourceCatalog(entries)

    # -- lookups -------------------------------------------------------------

    def get(self, resource_type: str) -> Optional[CatalogEntry]:
        return self._by_resource_type.get(resource_type)

    def get_by_family(self, family: str) -> Optional[CatalogEntry]:
        return self._by_family.get(family)

    def entries_in_category(self, category: str) -> List[CatalogEntry]:
        return [e for e in self.entries if e.primary_category == category]

    def categories_present(self) -> List[str]:
        present = {e.primary_category for e in self.entries}
        return [c for c in CATEGORIES if c in present]

    # -- search --------------------------------------------------------------

    def search(self, query: str) -> List[Dict]:
        """Case-insensitive substring search across friendly + technical metadata.

        Returns a list of ``{"entry", "reasons"}`` dicts, best matches first.
        """
        query = (query or "").strip().lower()
        if not query:
            return []
        results = []
        for entry in self.entries:
            reasons = []
            if query in entry.friendly_name.lower():
                reasons.append("name")
            if query in entry.family.lower():
                reasons.append("family")
            if query in entry.resource_type.lower():
                reasons.append("type")
            if query in entry.primary_category.lower():
                reasons.append("category")
            if query in entry.description.lower():
                reasons.append("description")
            if any(query in tag.lower() for tag in entry.tags):
                reasons.append("tag")
            if reasons:
                results.append({"entry": entry, "reasons": reasons})
        # Rank: name/family/category matches first, then description/tag.
        def score(item):
            reasons = set(item["reasons"])
            primary = len(reasons & {"name", "family", "category", "type"})
            return (-primary, item["entry"].friendly_name.lower())
        results.sort(key=score)
        return results

    # -- validation ----------------------------------------------------------

    def validate(self, known_roots: List[Dict], db=None) -> List[str]:
        """Validate the catalog against the technical root list (and schema).

        ``known_roots`` is the list from ``known_resource_roots.json`` (each a
        dict with ``family``, ``lua_class``, ``resource_type``). ``db`` is an
        optional :class:`TypeDatabase` used to confirm each mapped Lua class
        still exists.

        Returns a list of error strings (empty == valid).
        """
        errors: List[str] = []

        known_types = {r["resource_type"] for r in known_roots}
        known_families = {r["family"] for r in known_roots}
        family_to_class = {r["family"]: r["lua_class"] for r in known_roots}

        # 1. exactly one entry per known root, no extras, no duplicates
        seen_types = set()
        for entry in self.entries:
            if entry.resource_type in seen_types:
                errors.append("duplicate resource_type in catalog: %s" % entry.resource_type)
            seen_types.add(entry.resource_type)

            # 3. no unknown resource types
            if entry.resource_type not in known_types:
                errors.append("catalog has unknown resource_type: %s" % entry.resource_type)

            # family consistency
            if entry.family and entry.family not in known_families:
                errors.append("catalog has unknown family: %s" % entry.family)

            # 5. required fields present
            if not entry.friendly_name:
                errors.append("entry missing friendly_name: %s" % entry.resource_type)
            if not entry.primary_category:
                errors.append("entry missing primary_category: %s" % entry.resource_type)
            if not entry.description:
                errors.append("entry missing description: %s" % entry.resource_type)
            if not isinstance(entry.tags, list):
                errors.append("entry tags must be a list: %s" % entry.resource_type)

            # 6. category from approved list
            if entry.primary_category and entry.primary_category not in CATEGORIES:
                errors.append(
                    "entry has unapproved category %r: %s"
                    % (entry.primary_category, entry.resource_type))

            # access level
            if entry.access_level not in ACCESS_LEVELS:
                errors.append(
                    "entry has invalid access_level %r: %s"
                    % (entry.access_level, entry.resource_type))

            # 7. mapped Lua class still exists in types.lua
            if db is not None:
                lua_class = family_to_class.get(entry.family)
                if lua_class and not db.has_class(lua_class):
                    errors.append(
                        "mapped Lua class missing from types.lua: %s (%s)"
                        % (lua_class, entry.resource_type))

        # 2. every known root appears exactly once
        missing = known_types - seen_types
        for rt in sorted(missing):
            errors.append("known root missing from catalog: %s" % rt)

        # 1. count check
        if len(self.entries) != len(known_roots):
            errors.append(
                "catalog has %d entries but %d known roots"
                % (len(self.entries), len(known_roots)))

        return errors
