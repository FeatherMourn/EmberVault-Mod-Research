"""Value validation.

Validation happens *before* an edit can be added to a profile. Invalid values
are rejected with an explanation rather than silently clamped.

Supported MVP types: booleans, signed/unsigned integers, floats, strings,
enums, GUIDs, object references. Bitmasks and variants are read-only.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Optional

from .schema_model import (
    FLOAT_KINDS,
    INTEGER_KINDS,
    PRIMITIVE_KINDS,
    SIGNED_RANGES,
    UNSIGNED_RANGES,
    TypeDatabase,
    TypeExpression,
)

_GUID_HYPHEN_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_GUID_HEX_RE = re.compile(r"^[0-9a-fA-F]{32}$")


@dataclass
class ValidationResult:
    ok: bool
    value: Any = None          # normalised value on success
    error: str = ""

    def __bool__(self) -> bool:
        return self.ok


def _fail(message: str) -> ValidationResult:
    return ValidationResult(ok=False, error=message)


def validate_guid(value: Any) -> ValidationResult:
    if isinstance(value, str):
        text = value.strip()
        if _GUID_HYPHEN_RE.match(text) or _GUID_HEX_RE.match(text):
            return ValidationResult(ok=True, value=text)
        return _fail(
            "GUID must be 32 hex chars or "
            "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX (got %r)" % value
        )
    return _fail("GUID must be a string (got %r)" % value)


def validate_bool(value: Any) -> ValidationResult:
    if isinstance(value, bool):
        return ValidationResult(ok=True, value=value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "yes", "on"):
            return ValidationResult(ok=True, value=True)
        if lowered in ("false", "0", "no", "off"):
            return ValidationResult(ok=True, value=False)
    return _fail("expected a boolean (true/false), got %r" % value)


def validate_integer(kind: str, value: Any) -> ValidationResult:
    if isinstance(value, bool):
        return _fail("expected an integer for %s, got a boolean" % kind)

    if isinstance(value, int):
        number = value
    elif isinstance(value, float) and value.is_integer():
        number = int(value)
    elif isinstance(value, str):
        try:
            number = int(value.strip(), 0) if value.strip().lower().startswith(("0x", "-0x", "0b", "-0b")) else int(value.strip(), 10)
        except ValueError:
            return _fail("expected an integer for %s, got %r" % (kind, value))
    else:
        return _fail("expected an integer for %s, got %r" % (kind, value))

    low, high = (SIGNED_RANGES if kind in SIGNED_RANGES else UNSIGNED_RANGES)[kind]
    if number < low or number > high:
        return _fail(
            "%s value %d out of range [%d, %d]" % (kind, number, low, high)
        )
    return ValidationResult(ok=True, value=number)


def validate_float(kind: str, value: Any) -> ValidationResult:
    if isinstance(value, bool):
        return _fail("expected a number for %s, got a boolean" % kind)
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return _fail("expected a number for %s, got %r" % (kind, value))
    else:
        return _fail("expected a number for %s, got %r" % (kind, value))

    if not math.isfinite(number):
        return _fail("%s value must be finite (got %r)" % (kind, number))
    return ValidationResult(ok=True, value=number)


def validate_string(value: Any) -> ValidationResult:
    if isinstance(value, str):
        return ValidationResult(ok=True, value=value)
    return _fail("expected a string, got %r" % value)


def validate_enum(choices: list, value: Any) -> ValidationResult:
    if isinstance(value, str):
        text = value.strip()
        if text in choices:
            return ValidationResult(ok=True, value=text)
        return _fail(
            "value %r is not one of the allowed choices: %s"
            % (value, ", ".join(repr(c) for c in choices))
        )
    return _fail("enum value must be a string, got %r" % value)


def validate_value(
    db: TypeDatabase,
    type_expr: TypeExpression,
    value: Any,
) -> ValidationResult:
    """Validate ``value`` against a resolved :class:`TypeExpression`.

    This is the main entry point used by the UI and the profile layer.
    """
    kind = type_expr.kind

    if kind == "bool":
        return validate_bool(value)
    if kind in INTEGER_KINDS:
        return validate_integer(kind, value)
    if kind in FLOAT_KINDS:
        return validate_float(kind, value)
    if kind == "string":
        return validate_string(value)
    if kind == "guid":
        return validate_guid(value)
    if kind == "reference":
        # ObjectReference<T> is represented by a GUID string.
        return validate_guid(value)
    if kind == "named":
        # Named type: enum alias or nested class. Only enum aliases are editable
        # by MVP; a nested class would need a leaf path instead.
        choices = db.enum_choices(type_expr.name or "")
        if choices:
            return validate_enum(choices, value)
        return _fail(
            "field type %r is a nested class, not a scalar; select a leaf field "
            "inside it" % type_expr.raw
        )
    if kind in ("array", "static_array"):
        return _fail("array values are edited by index, not by whole-array value")
    if kind == "bitmask":
        return _fail("bitmask fields are read-only in the MVP")
    if kind == "variant":
        return _fail("variant fields are read-only in the MVP (fail closed)")
    return _fail("unsupported field type %r" % type_expr.raw)


def primitive_range(kind: str) -> Optional[tuple]:
    """Return the (low, high) range for an integer primitive kind, else None."""
    if kind in SIGNED_RANGES:
        return SIGNED_RANGES[kind]
    if kind in UNSIGNED_RANGES:
        return UNSIGNED_RANGES[kind]
    return None
