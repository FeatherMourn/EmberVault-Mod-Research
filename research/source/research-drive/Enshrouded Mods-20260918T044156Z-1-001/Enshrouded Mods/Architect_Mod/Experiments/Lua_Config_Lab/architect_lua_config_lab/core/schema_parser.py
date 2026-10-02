"""Parser for the generated EmmyLua annotations in ``types.lua``.

Recognises ``---@class``, ``---@field``, ``---@alias`` and the ``---|``
choice continuations that define enum-like aliases. Inheritance after a class
declaration (``---@class keen.X : keen.Parent``) is captured.

The parser produces a :class:`TypeDatabase` (see :mod:`schema_model`).
"""

from __future__ import annotations

import re
from typing import Optional

from .schema_model import (
    AliasDefinition,
    ClassDefinition,
    FieldDefinition,
    TypeDatabase,
)
from .type_parser import parse_type_expression

_CLASS_RE = re.compile(r"^---@class\s+([A-Za-z_][A-Za-z0-9_.]*)(?:\s*:\s*([A-Za-z_][A-Za-z0-9_.]*))?")
_FIELD_RE = re.compile(r"^---@field\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+)$")
_ALIAS_RE = re.compile(r"^---@alias\s+([A-Za-z_][A-Za-z0-9_.]*)")
_CHOICE_RE = re.compile(r"^---\|\s*(.+)$")

_TRAILING_COMMENT_RE = re.compile(r"\s+--.*$")


def _strip_comment(text: str) -> str:
    return _TRAILING_COMMENT_RE.sub("", text).rstrip()


def _parse_choice(text: str) -> str:
    """Parse a ``---| "ChoiceValue"`` line into the raw choice string."""
    text = _strip_comment(text).strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1]
    # Some enums may be unquoted tokens; keep them verbatim.
    return text


def parse_types_lua(text: str) -> TypeDatabase:
    """Parse the contents of ``types.lua`` into a :class:`TypeDatabase`."""
    db = TypeDatabase()

    current_class: Optional[ClassDefinition] = None
    current_alias: Optional[AliasDefinition] = None

    for line in text.splitlines():
        stripped = line.strip()

        class_match = _CLASS_RE.match(stripped)
        if class_match:
            name = class_match.group(1)
            parent = class_match.group(2)
            current_class = ClassDefinition(name=name, parent=parent)
            current_alias = None
            db.add_class(current_class)
            continue

        field_match = _FIELD_RE.match(stripped)
        if field_match and current_class is not None:
            field_name = field_match.group(1)
            field_type = _strip_comment(field_match.group(2))
            current_class.fields.append(
                FieldDefinition(
                    name=field_name,
                    declared_type=field_type,
                    type_expr=parse_type_expression(field_type),
                    owner_class=current_class.name,
                )
            )
            continue

        alias_match = _ALIAS_RE.match(stripped)
        if alias_match:
            current_alias = AliasDefinition(name=alias_match.group(1))
            current_class = None
            db.add_alias(current_alias)
            continue

        choice_match = _CHOICE_RE.match(stripped)
        if choice_match and current_alias is not None:
            current_alias.choices.append(_parse_choice(choice_match.group(1)))
            continue

    return db


def parse_types_lua_file(path: str) -> TypeDatabase:
    """Parse a ``types.lua`` file from disk."""
    with open(path, "r", encoding="utf-8") as handle:
        return parse_types_lua(handle.read())
