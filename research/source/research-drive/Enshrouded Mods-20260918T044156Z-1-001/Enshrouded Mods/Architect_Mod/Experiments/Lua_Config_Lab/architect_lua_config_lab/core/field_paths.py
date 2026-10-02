"""Field path parsing and resolution.

A field path is a dotted string optionally including ``[n]`` array indices,
for example ``gliderConfig.accelerationForward`` or ``values[1]``. This module
parses such strings into components, resolves them against the schema, and
produces a Lua access expression relative to ``resource.data``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from typing import List, Optional, Tuple

from .schema_model import FieldDefinition, TypeDatabase, TypeExpression
from .type_parser import parse_type_expression

_TOKEN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)|(\[\s*(\d+)\s*\])")


@dataclass(frozen=True)
class PathComponent:
    kind: str        # "field" or "index"
    name: Optional[str] = None
    index: Optional[int] = None


@dataclass
class PathResolution:
    ok: bool
    path: str = ""
    components: List[PathComponent] = dc_field(default_factory=list)
    leaf_type: Optional[TypeExpression] = None
    leaf_class: Optional[str] = None
    editable: bool = False
    kind_label: str = "unknown"
    choices: List[str] = dc_field(default_factory=list)
    error: str = ""


def parse_path(path: str) -> List[PathComponent]:
    """Parse a dotted path string into components."""
    components: List[PathComponent] = []
    for match in _TOKEN_RE.finditer(path or ""):
        if match.group(1) is not None:
            components.append(PathComponent(kind="field", name=match.group(1)))
        else:
            components.append(PathComponent(kind="index", index=int(match.group(3))))
    return components


def format_path(components: List[PathComponent]) -> str:
    """Render components back into the canonical dotted path string."""
    parts: List[str] = []
    for component in components:
        if component.kind == "field":
            parts.append(component.name or "")
        else:
            parts.append("[%d]" % (component.index or 0))
    return ".".join(parts)


def lua_access_path(components: List[PathComponent], base: str = "data") -> str:
    """Produce a Lua access expression relative to ``resource.<base>``."""
    parts = [base]
    for component in components:
        if component.kind == "field":
            parts.append(component.name or "")
        else:
            parts[-1] = "%s[%d]" % (parts[-1], component.index or 0)
    return ".".join(parts)


def find_field(
    db: TypeDatabase,
    class_name: str,
    field_name: str,
) -> Optional[FieldDefinition]:
    """Find a field on a class, walking the inheritance chain."""
    current: Optional[str] = class_name
    seen = set()
    while current is not None and current not in seen:
        seen.add(current)
        cls = db.get_class(current)
        if cls is None:
            return None
        for field in cls.fields:
            if field.name == field_name:
                return field
        current = cls.parent
    return None


def classify_leaf(
    db: TypeDatabase,
    type_expr: TypeExpression,
) -> Tuple[bool, str, List[str]]:
    """Classify a leaf type expression for editability.

    Returns ``(editable, kind_label, choices)``.
    """
    kind = type_expr.kind
    if kind in ("bool", "u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64",
                "f16", "f32", "f64", "string"):
        return True, kind, []
    if kind == "guid":
        return True, "guid", []
    if kind == "reference":
        return True, "reference", []
    if kind == "named":
        choices = db.enum_choices(type_expr.name or "") or []
        if choices:
            return True, "enum", choices
        return False, "nested", []
    if kind in ("array", "static_array"):
        return False, kind, []
    if kind == "bitmask":
        return False, "bitmask", []
    if kind == "variant":
        return False, "variant", []
    return False, "unknown", []


def resolve_path(
    db: TypeDatabase,
    root_class_name: str,
    path: str,
) -> PathResolution:
    """Resolve ``path`` against ``root_class_name``.

    Returns a :class:`PathResolution` describing the leaf type and whether it
    is editable by the MVP.
    """
    components = parse_path(path)
    if not components:
        return PathResolution(ok=False, path=path, error="empty field path")

    # We walk the type graph. `current_expr` is the type expression produced by
    # the previous step; `current_class` is the reflected class for traversal.
    current_class: Optional[str] = root_class_name
    current_expr: Optional[TypeExpression] = None
    last_field: Optional[FieldDefinition] = None

    expecting_index = False
    element_expr: Optional[TypeExpression] = None

    for component in components:
        if component.kind == "index":
            if not expecting_index:
                return PathResolution(
                    ok=False, path=path, components=components,
                    error="array index used without a preceding array field",
                )
            # Move into the array element type.
            current_expr = element_expr
            current_class = (
                current_expr.name
                if current_expr is not None
                and current_expr.kind in ("named", "array", "static_array",
                                          "bitmask", "variant", "reference")
                and current_expr.name and db.has_class(current_expr.name)
                else None
            )
            if current_expr is not None and current_expr.kind in ("array", "static_array"):
                # After indexing into an array-of-array, further indexing handled
                # by the same element type.
                inner = current_expr
                if inner.kind in ("array", "static_array"):
                    element_expr = inner.inner
                    expecting_index = True
                else:
                    element_expr = None
                    expecting_index = False
            else:
                element_expr = None
                expecting_index = False
            last_field = None
            continue

        # component.kind == "field"
        field_name = component.name
        if current_class is None:
            return PathResolution(
                ok=False, path=path, components=components,
                error="cannot traverse into non-class type for field %r"
                % field_name,
            )

        field = find_field(db, current_class, field_name)
        if field is None:
            return PathResolution(
                ok=False, path=path, components=components,
                error="field %r not found on %s" % (field_name, current_class),
            )

        current_expr = field.type_expr
        last_field = field

        if current_expr.kind in ("array", "static_array"):
            element_expr = current_expr.inner
            expecting_index = True
            current_class = None
        elif current_expr.kind in ("named", "reference", "bitmask", "variant"):
            # A named class can be traversed; a reference is a GUID leaf.
            if current_expr.kind == "named" and db.has_class(current_expr.name or ""):
                current_class = current_expr.name
                expecting_index = False
            elif current_expr.kind == "reference":
                current_class = None
                expecting_index = False
            else:
                # bitmask / variant / unknown named: leaf, stop traversal
                current_class = None
                expecting_index = False
        else:
            # primitive leaf
            current_class = None
            expecting_index = False

    if expecting_index:
        return PathResolution(
            ok=False, path=path, components=components,
            error="array field %r requires an index" % (last_field.name if last_field else path),
        )

    if current_expr is None:
        return PathResolution(
            ok=False, path=path, components=components,
            error="could not resolve field path",
        )

    editable, kind_label, choices = classify_leaf(db, current_expr)
    return PathResolution(
        ok=True,
        path=format_path(components),
        components=components,
        leaf_type=current_expr,
        leaf_class=current_expr.name,
        editable=editable,
        kind_label=kind_label,
        choices=choices,
    )
