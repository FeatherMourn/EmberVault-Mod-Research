"""Tests for Lua generation: determinism, escaping, and structure."""

from __future__ import annotations

import unittest

from architect_lua_config_lab.core.lab import Lab
from architect_lua_config_lab.core.lua_generator import (
    generate_lua,
    lua_literal,
    lua_number,
    lua_string,
)
from architect_lua_config_lab.core.profile import Edit, Profile, Target

from .helpers import make_lab, require_types_lua


def _stamina_profile(value=500):
    return Profile(
        name="Baseline Stamina Test",
        description="startup experiment",
        game_build="1076226",
        types_lua_sha256="ff345a2eeaf939d13599ce25c4b8cc24aaabe8e36dfcd5ad255533e4637a1c81",
        edits=[
            Edit(
                enabled=True,
                resource_type="keen::BalancingTable",
                target=Target(mode="first"),
                path="playerBaseStamina",
                schema_type="u32",
                value=value,
                evidence_state="EXPERIMENTAL",
            )
        ],
    )


class LuaLiteralTests(unittest.TestCase):
    def test_string_escape(self):
        self.assertEqual(lua_string("abc"), '"abc"')
        self.assertEqual(lua_string('a"b'), '"a\\"b"')
        self.assertEqual(lua_string("a\\b"), '"a\\\\b"')
        self.assertEqual(lua_string("a\nb"), '"a\\nb"')

    def test_string_control_chars(self):
        literal = lua_string("line1\x00line2")
        self.assertNotIn("\x00", literal)
        self.assertIn("\\000", literal)

    def test_number_integer(self):
        self.assertEqual(lua_number(500, "u32"), "500")
        self.assertEqual(lua_number(18446744073709551615, "u64"),
                         "18446744073709551615")

    def test_number_float(self):
        self.assertEqual(lua_number(500.0, "f32"), "500.0")
        self.assertEqual(lua_number(1.5, "f32"), "1.5")

    def test_number_refuses_non_finite(self):
        with self.assertRaises(ValueError):
            lua_number(float("inf"), "f32")

    def test_bool_literal(self):
        self.assertEqual(lua_literal(True, "bool"), "true")
        self.assertEqual(lua_literal(False, "bool"), "false")


class LuaGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_types_lua(cls)
        cls.lab = make_lab()

    def test_deterministic_output(self):
        profile = _stamina_profile()
        first = self.lab.generate(profile)
        second = self.lab.generate(profile)
        self.assertEqual(first, second)

    def test_contains_expected_elements(self):
        lua = self.lab.generate(_stamina_profile())
        self.assertIn("game.assets.get_resources_by_type", lua)
        self.assertIn('"keen::BalancingTable"', lua)
        self.assertIn('"playerBaseStamina"', lua)
        self.assertIn("io.export", lua)
        self.assertIn("precondition mismatch", lua)

    def test_value_emitted(self):
        lua = self.lab.generate(_stamina_profile(value=777))
        self.assertIn("value = 777", lua)

    def test_float_value_emitted_with_dot(self):
        profile = Profile(
            name="slope",
            game_build="1076226",
            types_lua_sha256="",
            edits=[Edit(
                enabled=True,
                resource_type="keen::SlopeDefinition",
                target=Target(mode="first"),
                path="slidingAngle",
                schema_type="f32",
                value=50.0,
                evidence_state="EXPERIMENTAL",
            )],
        )
        lua = self.lab.generate(profile)
        self.assertIn("value = 50.0", lua)

    def test_string_value_escaped(self):
        profile = Profile(
            name="name_edit",
            game_build="1076226",
            types_lua_sha256="",
            edits=[Edit(
                enabled=True,
                resource_type="keen::ItemInfo",
                target=Target(mode="match", selector={
                    "field": "debugName", "operator": "eq", "value": "x",
                }),
                path="debugName",
                schema_type="string",
                value='quote"slash\\newline\n',
                evidence_state="EXPERIMENTAL",
            )],
        )
        lua = self.lab.generate(profile)
        self.assertNotIn('quote"slash\\newline\n', lua)
        self.assertIn('\\"', lua)
        self.assertIn('\\\\', lua)

    def test_match_selector_generated(self):
        profile = Profile(
            name="item_match",
            game_build="1076226",
            types_lua_sha256="",
            edits=[Edit(
                enabled=True,
                resource_type="keen::ItemInfo",
                target=Target(mode="match", selector={
                    "field": "itemId.value", "operator": "eq", "value": 123,
                }),
                path="maxStackSize",
                schema_type="u16",
                value=999,
                evidence_state="EXPERIMENTAL",
            )],
        )
        lua = self.lab.generate(profile)
        self.assertIn('selectorField', lua)
        self.assertIn('selectorValue = 123', lua)

    def test_precondition_generated(self):
        profile = _stamina_profile()
        profile.edits[0].expected_original = 250
        lua = self.lab.generate(profile)
        self.assertIn("hasExpected = true", lua)
        self.assertIn("expected = 250", lua)

    def test_invalid_path_raises(self):
        profile = _stamina_profile()
        profile.edits[0].path = "doesNotExist"
        with self.assertRaises(ValueError):
            self.lab.generate(profile)


if __name__ == "__main__":
    unittest.main()
