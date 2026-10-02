"""Tests for the types.lua schema parser."""

from __future__ import annotations

import unittest

from architect_lua_config_lab.core.schema_parser import parse_types_lua_file
from architect_lua_config_lab.config import types_lua_path

from .helpers import require_types_lua


class SchemaParserTests(unittest.TestCase):
    def test_parses_without_error(self):
        require_types_lua(self)
        db = parse_types_lua_file(types_lua_path())
        self.assertGreater(db.class_count(), 0)

    def test_regression_counts(self):
        require_types_lua(self)
        db = parse_types_lua_file(types_lua_path())
        # Expected for the current supplied types.lua (build 1076226).
        self.assertEqual(db.class_count(), 4854)
        self.assertEqual(db.alias_count(), 768)
        self.assertEqual(db.field_count(), 21442)

    def test_balanced_table_fields(self):
        require_types_lua(self)
        db = parse_types_lua_file(types_lua_path())
        cls = db.get_class("keen.BalancingTable")
        self.assertIsNotNone(cls)
        names = {f.name for f in cls.fields}
        self.assertIn("playerBaseStamina", names)
        self.assertIn("playerBaseHealth", names)
        stamina = next(f for f in cls.fields if f.name == "playerBaseStamina")
        self.assertEqual(stamina.type_expr.kind, "u32")

    def test_inheritance_captured(self):
        require_types_lua(self)
        db = parse_types_lua_file(types_lua_path())
        cls = db.get_class("keen.AchievementDirectory")
        self.assertIsNotNone(cls)
        self.assertEqual(cls.parent, "keen.AchievementSubDirectory")

    def test_enum_alias_choices(self):
        require_types_lua(self)
        db = parse_types_lua_file(types_lua_path())
        alias = db.get_alias("keen.WeatherState")
        self.assertIsNotNone(alias)
        self.assertEqual(alias.choices, ["Clear", "Rain", "Snow", "Blizzard"])


if __name__ == "__main__":
    unittest.main()
