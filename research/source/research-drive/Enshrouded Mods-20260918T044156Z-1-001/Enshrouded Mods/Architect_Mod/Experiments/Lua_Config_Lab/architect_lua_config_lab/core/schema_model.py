"""Internal schema model.

The parser (`schema_parser`) produces these objects. The rest of the program
operates on this model rather than on raw ``types.lua`` text.

Model objects
-------------
* :class:`TypeExpression` - a parsed field type.
* :class:`FieldDefinition` - a single ``---@field``.
* :class:`ClassDefinition` - a single ``---@class``.
* :class:`AliasDefinition` - a single ``---@alias`` (enum-like choices).
* :class:`TypeDatabase` - the whole reflected type graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Type expression kinds
# ---------------------------------------------------------------------------

# Primitive scalar kinds (mirror base.lua aliases).
PRIMITIVE_KINDS = {
    "bool", "u8", "u16", "u32", "u64",
    "i8", "i16", "i32", "i64",
    "f16", "f32", "f64",
    "string",
}

SIGNED_RANGES = {
    "i8": (-128, 127),
    "i16": (-32768, 32767),
    "i32": (-2147483648, 2147483647),
    "i64": (-9223372036854775808, 9223372036854775807),
}

UNSIGNED_RANGES = {
    "u8": (0, 255),
    "u16": (0, 65535),
    "u32": (0, 4294967295),
    "u64": (0, 18446744073709551615),
}

FLOAT_KINDS = {"f16", "f32", "f64"}
INTEGER_KINDS = set(SIGNED_RANGES) | set(UNSIGNED_RANGES)


@dataclass(frozen=True)
class TypeExpression:
    """A parsed field type expression.

    ``kind`` is one of:

    * a primitive scalar name (``"u32"``, ``"f32"``, ``"string"``, ...)
    * ``"guid"``
    * ``"reference"``     - ``ObjectReference<T>``
    * ``"array"``         - ``Array<T>``
    * ``"static_array"``  - ``StaticArray<T, N>``
    * ``"bitmask"``       - ``Bitmask<T>``
    * ``"variant"``       - ``Variant<T>``
    * ``"named"``         - a reflected class / alias by (dotted) name
    * ``"unknown"``       - anything the parser did not recognise
    """

    raw: str
    kind: str
    name: Optional[str] = None            # for "named" / "reference" / element names
    inner: Optional["TypeExpression"] = None   # element type for wrappers
    size: Optional[int] = None            # for "static_array"
    nullable: bool = False                # trailing "?"

    def is_primitive(self) -> bool:
        return self.kind in PRIMITIVE_KINDS

    def is_integer(self) -> bool:
        return self.kind in INTEGER_KINDS

    def is_float(self) -> bool:
        return self.kind in FLOAT_KINDS

    def is_numeric(self) -> bool:
        return self.is_integer() or self.is_float()

    def is_enum_like(self) -> bool:
        return self.kind == "named"


@dataclass
class FieldDefinition:
    name: str
    declared_type: str
    type_expr: TypeExpression
    owner_class: str


@dataclass
class ClassDefinition:
    name: str                        # dotted Lua name, e.g. "keen.BalancingTable"
    parent: Optional[str] = None
    fields: List[FieldDefinition] = dc_field(default_factory=list)
    is_resource_root: bool = False
    resource_family: Optional[str] = None

    @property
    def short_name(self) -> str:
        return self.name.rsplit(".", 1)[-1]


@dataclass
class AliasDefinition:
    name: str
    choices: List[str] = dc_field(default_factory=list)

    @property
    def is_enum(self) -> bool:
        return bool(self.choices)

    @property
    def short_name(self) -> str:
        return self.name.rsplit(".", 1)[-1]


class TypeDatabase:
    """The whole reflected type graph parsed from ``types.lua``."""

    def __init__(self) -> None:
        self.classes: Dict[str, ClassDefinition] = {}
        self.aliases: Dict[str, AliasDefinition] = {}
        self._order: List[str] = []

    # -- registration -------------------------------------------------------

    def add_class(self, definition: ClassDefinition) -> None:
        self.classes[definition.name] = definition
        self._order.append(definition.name)

    def add_alias(self, definition: AliasDefinition) -> None:
        self.aliases[definition.name] = definition

    # -- lookups ------------------------------------------------------------

    def get_class(self, name: str) -> Optional[ClassDefinition]:
        return self.classes.get(name)

    def get_alias(self, name: str) -> Optional[AliasDefinition]:
        return self.aliases.get(name)

    def has_class(self, name: str) -> bool:
        return name in self.classes

    def has_alias(self, name: str) -> bool:
        return name in self.aliases

    # -- summary metrics ----------------------------------------------------

    def class_count(self) -> int:
        return len(self.classes)

    def alias_count(self) -> int:
        return len(self.aliases)

    def field_count(self) -> int:
        return sum(len(c.fields) for c in self.classes.values())

    def short_name_lookup(self) -> Dict[str, List[str]]:
        """Map a class short name (last dotted segment) to class names."""
        lookup: Dict[str, List[str]] = {}
        for name in self.classes:
            lookup.setdefault(name.rsplit(".", 1)[-1], []).append(name)
        return lookup

    def enum_choices(self, name: str) -> Optional[List[str]]:
        """Return the discrete string choices for an enum alias, if any."""
        alias = self.aliases.get(name)
        if alias is not None:
            return list(alias.choices) if alias.choices else None
        return None

    def resolve_named(self, name: str) -> Tuple[Optional[ClassDefinition],
                                                Optional[AliasDefinition]]:
        return self.classes.get(name), self.aliases.get(name)
