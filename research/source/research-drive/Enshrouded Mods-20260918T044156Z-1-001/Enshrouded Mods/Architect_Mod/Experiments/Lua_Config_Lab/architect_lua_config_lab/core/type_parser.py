"""Type expression parsing and qualified-name conversion.

This module owns the two pieces of type plumbing the rest of the program needs:

1. ``parse_type_expression`` - parse an EmmyLua field type string into a
   :class:`TypeExpression`.
2. ``lua_class_to_resource_type`` / ``resource_type_to_lua_class`` - convert
   between Lua dotted class names (``keen.BalancingTable``) and the qualified
   names used by :class:`AssetManager` (``keen::BalancingTable``).
"""

from __future__ import annotations

import re
from typing import Optional

from .schema_model import (
    PRIMITIVE_KINDS,
    TypeExpression,
)

# Regexes for wrapped generic types. We parse recursively so nesting such as
# ``Array<ObjectReference<keen.X>>`` is handled correctly.
_WRAPPER_RE = re.compile(r"^(ObjectReference|Array|StaticArray|Bitmask|Variant)<(.+)>$")
_STATIC_ARRAY_RE = re.compile(r"^(StaticArray)<(.+)>$")
_GENERIC_SPLIT_RE = re.compile(r",\s*")

_PRIMITIVE_RE = re.compile(r"^(bool|u8|u16|u32|u64|i8|i16|i32|i64|f16|f32|f64|string)$")
_NAMED_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
_GUID_RE = re.compile(r"^Guid$")


def lua_class_to_resource_type(lua_name: str) -> str:
    """Convert a Lua dotted class name to a qualified resource type.

    ``keen.BalancingTable`` -> ``keen::BalancingTable``
    ``keen.ecs.TemplateResource`` -> ``keen::ecs::TemplateResource``
    """
    if "::" in lua_name:
        return lua_name
    return lua_name.replace(".", "::")


def resource_type_to_lua_class(resource_type: str) -> str:
    """Convert a qualified resource type back to a Lua dotted class name."""
    return resource_type.replace("::", ".")


def _split_generic_args(body: str) -> list:
    """Split ``T, N`` style generic argument lists, respecting nested generics."""
    parts = []
    depth = 0
    current = []
    for ch in body:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def parse_type_expression(raw: str) -> TypeExpression:
    """Parse a single field type expression into a :class:`TypeExpression`.

    Recognises the primitive scalars from ``base.lua``, ``Guid``,
    ``ObjectReference<T>``, ``Array<T>``, ``StaticArray<T, N>``,
    ``Bitmask<T>``, ``Variant<T>``, optional ``?`` suffixes and named classes.
    """
    text = (raw or "").strip()
    if not text:
        return TypeExpression(raw=raw, kind="unknown")

    nullable = False
    if text.endswith("?"):
        nullable = True
        text = text[:-1].strip()

    if _PRIMITIVE_RE.match(text):
        return TypeExpression(raw=raw, kind=text, nullable=nullable)

    if _GUID_RE.match(text):
        return TypeExpression(raw=raw, kind="guid", nullable=nullable)

    wrapper = _WRAPPER_RE.match(text)
    if wrapper:
        outer, body = wrapper.group(1), wrapper.group(2)
        args = _split_generic_args(body)

        if outer == "ObjectReference" and args:
            inner = parse_type_expression(args[0])
            return TypeExpression(
                raw=raw, kind="reference",
                name=inner.name if inner.name else None,
                inner=inner, nullable=nullable,
            )

        if outer == "Array" and args:
            inner = parse_type_expression(args[0])
            return TypeExpression(
                raw=raw, kind="array", name=inner.name, inner=inner,
                nullable=nullable,
            )

        if outer == "StaticArray" and args:
            inner = parse_type_expression(args[0])
            size: Optional[int] = None
            if len(args) > 1:
                try:
                    size = int(args[1].strip())
                except ValueError:
                    size = None
            return TypeExpression(
                raw=raw, kind="static_array", name=inner.name, inner=inner,
                size=size, nullable=nullable,
            )

        if outer == "Bitmask" and args:
            inner = parse_type_expression(args[0])
            return TypeExpression(
                raw=raw, kind="bitmask", name=inner.name, inner=inner,
                nullable=nullable,
            )

        if outer == "Variant" and args:
            inner = parse_type_expression(args[0])
            return TypeExpression(
                raw=raw, kind="variant", name=inner.name, inner=inner,
                nullable=nullable,
            )

    # A named class / alias. This can be a dotted name such as
    # ``keen.SomeNestedType`` or a bare name.
    if _NAMED_RE.match(text):
        return TypeExpression(raw=raw, kind="named", name=text, nullable=nullable)

    return TypeExpression(raw=raw, kind="unknown", nullable=nullable)


def is_primitive_kind(kind: str) -> bool:
    return kind in PRIMITIVE_KINDS
