"""Resource-root identification.

Resource roots are the standalone KFC resource families that can be requested
through ``game.assets.get_resources_by_type(...)``. They are distinct from the
thousands of embedded/reflected classes that appear as nested field types.

The default whitelist is the 131 observed KFC root families shipped as
``data/known_resource_roots.json``. When the preferred
``Enshrouded_Lua_KFC_Resource_Map.json`` is available it takes precedence.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from .schema_model import TypeDatabase
from .type_parser import lua_class_to_resource_type


def _package_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_known_roots_path() -> str:
    return os.path.join(_package_dir(), "data", "known_resource_roots.json")


def load_known_roots(path: Optional[str] = None) -> Dict:
    """Load the known resource roots data file (a dict with a ``roots`` list)."""
    path = path or default_known_roots_path()
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def roots_from_kfc_directory(kfc_dir: str) -> List[str]:
    """Derive root family names from the ``ENSHROUDED KFC FILES`` directory.

    Each root family is a ``<Family>.zip`` file name.
    """
    if not os.path.isdir(kfc_dir):
        return []
    families = sorted(
        name[:-4]
        for name in os.listdir(kfc_dir)
        if name.lower().endswith(".zip")
    )
    return families


def resolve_roots(db: TypeDatabase, families: List[str]) -> List[dict]:
    """Resolve each root family name to exactly one reflected class.

    Returns a list of ``{"family", "lua_class", "resource_type"}`` dicts.
    Raises :class:`ValueError` if any family does not resolve to exactly one
    class.
    """
    lookup = db.short_name_lookup()
    resolved: List[dict] = []
    for family in families:
        candidates = lookup.get(family, [])
        if len(candidates) != 1:
            raise ValueError(
                "KFC root family %r does not resolve to exactly one reflected "
                "class (found %d: %s)"
                % (family, len(candidates), candidates)
            )
        lua_class = candidates[0]
        resolved.append({
            "family": family,
            "lua_class": lua_class,
            "resource_type": lua_class_to_resource_type(lua_class),
        })
    return resolved


def mark_resource_roots(db: TypeDatabase, roots: List[dict]) -> None:
    """Flag classes in ``db`` that correspond to resource roots."""
    for entry in roots:
        cls = db.get_class(entry["lua_class"])
        if cls is not None:
            cls.is_resource_root = True
            cls.resource_family = entry["family"]


def load_root_entries(
    db: TypeDatabase,
    kfc_dir: Optional[str] = None,
    resource_map_path: Optional[str] = None,
    known_roots_path: Optional[str] = None,
) -> List[dict]:
    """Load and resolve the resource-root entries, marking ``db`` classes.

    Precedence:
    1. ``resource_map_path`` (``Enshrouded_Lua_KFC_Resource_Map.json``) if given.
    2. ``kfc_dir`` if it is a valid directory (family names derived from zips).
    3. the bundled ``known_resource_roots.json``.

    Raises :class:`FileNotFoundError` if no source is available.
    """
    families: Optional[List[str]] = None
    source = ""

    if resource_map_path and os.path.isfile(resource_map_path):
        with open(resource_map_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        families = _families_from_resource_map(data)
        source = resource_map_path

    if families is None and kfc_dir and os.path.isdir(kfc_dir):
        derived = roots_from_kfc_directory(kfc_dir)
        if derived:
            families = derived
            source = kfc_dir

    if families is None:
        data = load_known_roots(known_roots_path)
        families = [entry["family"] for entry in data.get("roots", [])]
        source = known_roots_path or default_known_roots_path()

    if not families:
        raise FileNotFoundError("No resource-root source available.")

    roots = resolve_roots(db, families)
    mark_resource_roots(db, roots)
    return roots


def _families_from_resource_map(data: Dict) -> List[str]:
    """Extract family names from a ``Enshrouded_Lua_KFC_Resource_Map.json``.

    The map format is not strictly specified, so we accept a few common shapes:
    a top-level list of objects with a ``family``/``name``/``root`` key, or a
    dict keyed by family name.
    """
    roots = data.get("roots", data)
    if isinstance(roots, dict):
        return sorted(roots.keys())
    if isinstance(roots, list):
        names = []
        for item in roots:
            if isinstance(item, str):
                names.append(item)
            elif isinstance(item, dict):
                for key in ("family", "name", "root", "resource_type", "lua_class"):
                    if key in item and isinstance(item[key], str):
                        value = item[key].replace("::", ".")
                        names.append(value.rsplit(".", 1)[-1])
                        break
        return sorted(set(names))
    return []


def direct_field_count(db: TypeDatabase, roots: List[dict]) -> int:
    """Number of fields declared directly on the root resource classes."""
    total = 0
    for entry in roots:
        cls = db.get_class(entry["lua_class"])
        if cls is not None:
            total += len(cls.fields)
    return total


def reachable_nested_class_names(
    db: TypeDatabase,
    roots: List[dict],
    include_references: bool = True,
) -> set:
    """Names of reflected classes reachable (transitively) from root fields.

    ``include_references=False`` ignores classes reachable only through
    ``ObjectReference<T>`` (references rather than inline structs).
    """
    from .type_parser import parse_type_expression  # local import to avoid cycle

    root_set = {entry["lua_class"] for entry in roots}

    def refs(expr):
        found = set()
        if expr is None:
            return found
        if expr.name and db.has_class(expr.name) and expr.name not in root_set:
            found.add(expr.name)
        if expr.inner is not None:
            if include_references or expr.kind != "reference":
                found |= refs(expr.inner)
        return found

    seen = set(root_set)
    stack = list(root_set)
    reachable = set()
    while stack:
        name = stack.pop()
        cls = db.get_class(name)
        if cls is None:
            continue
        for field in cls.fields:
            for ref in refs(field.type_expr):
                if ref not in seen:
                    seen.add(ref)
                    reachable.add(ref)
                    stack.append(ref)
    return reachable
