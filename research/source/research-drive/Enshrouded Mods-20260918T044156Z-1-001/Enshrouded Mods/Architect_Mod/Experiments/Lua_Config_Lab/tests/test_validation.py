"""Tests for value validation."""

from __future__ import annotations

import unittest

from architect_lua_config_lab.core.schema_model import TypeDatabase
from architect_lua_config_lab.core.type_parser import parse_type_expression
from architect_lua_config_lab.core.validation import (
    validate_bool,
    validate_enum,
    validate_float,
    validate_guid,
    validate_integer,
    validate_value,
)


class IntegerValidationTests(unittest.TestCase):
    def test_u8_range(self):
        self.assertTrue(validate_integer("u8", 0).ok)
        self.assertTrue(validate_integer("u8", 255).ok)
        self.assertFalse(validate_integer("u8", -1).ok)
        self.assertFalse(validate_integer("u8", 256).ok)

    def test_i8_range(self):
        self.assertTrue(validate_integer("i8", -128).ok)
        self.assertTrue(validate_integer("i8", 127).ok)
        self.assertFalse(validate_integer("i8", -129).ok)
        self.assertFalse(validate_integer("i8", 128).ok)

    def test_u16_range(self):
        self.assertTrue(validate_integer("u16", 0).ok)
        self.assertTrue(validate_integer("u16", 65535).ok)
        self.assertFalse(validate_integer("u16", 65536).ok)

    def test_u32_range(self):
        self.assertTrue(validate_integer("u32", 4294967295).ok)
        self.assertFalse(validate_integer("u32", 4294967296).ok)

    def test_u64_range(self):
        self.assertTrue(validate_integer("u64", 18446744073709551615).ok)
        self.assertFalse(validate_integer("u64", -1).ok)

    def test_i64_range(self):
        self.assertTrue(validate_integer("i64", -9223372036854775808).ok)
        self.assertTrue(validate_integer("i64", 9223372036854775807).ok)

    def test_rejects_boolean_for_integer(self):
        self.assertFalse(validate_integer("u32", True).ok)

    def test_rejects_non_integer(self):
        self.assertFalse(validate_integer("u32", 3.5).ok)
        self.assertFalse(validate_integer("u32", "abc").ok)


class OtherValidationTests(unittest.TestCase):
    def test_bool(self):
        self.assertTrue(validate_bool(True).ok)
        self.assertTrue(validate_bool(False).ok)
        self.assertTrue(validate_bool("true").ok)
        self.assertFalse(validate_bool(1).ok)

    def test_float_finite(self):
        self.assertTrue(validate_float("f32", 1.5).ok)
        self.assertTrue(validate_float("f32", 500.0).ok)
        self.assertFalse(validate_float("f32", float("inf")).ok)
        self.assertFalse(validate_float("f32", float("nan")).ok)

    def test_enum(self):
        choices = ["Clear", "Rain"]
        self.assertTrue(validate_enum(choices, "Clear").ok)
        self.assertFalse(validate_enum(choices, "Sunny").ok)

    def test_guid(self):
        self.assertTrue(
            validate_guid("85e90fd8-e11f-4737-8e21-ce1cd0acaa50").ok)
        self.assertTrue(
            validate_guid("85e90fd8e11f47378e21ce1cd0acaa50").ok)
        self.assertFalse(validate_guid("not-a-guid").ok)
        self.assertFalse(validate_guid("85e90fd8-e11f-4737-8e21-ce1cd0acaa5Z").ok)


class ValidateValueDispatchTests(unittest.TestCase):
    def _db(self):
        db = TypeDatabase()
        from architect_lua_config_lab.core.schema_model import AliasDefinition
        db.add_alias(AliasDefinition(name="keen.WeatherState",
                                     choices=["Clear", "Rain"]))
        return db

    def test_enum_via_named_type(self):
        db = self._db()
        expr = parse_type_expression("keen.WeatherState")
        result = validate_value(db, expr, "Rain")
        self.assertTrue(result.ok)
        self.assertFalse(validate_value(db, expr, "Nope").ok)

    def test_bitmask_readonly(self):
        db = self._db()
        expr = parse_type_expression("Bitmask<keen.WeatherState>")
        self.assertFalse(validate_value(db, expr, "Clear").ok)


if __name__ == "__main__":
    unittest.main()
