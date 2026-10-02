"""Tests for field path parsing, traversal, and resolution."""

from __future__ import annotations

import unittest

from architect_lua_config_lab.core.field_paths import (
    lua_access_path,
    parse_path,
    resolve_path,
)
from architect_lua_config_lab.core.lab import Lab

from .helpers import make_lab, require_types_lua


class FieldPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_types_lua(cls)
        cls.lab = make_lab()

    def _resolve(self, resource_type, path):
        return resolve_path(
            self.lab.schema(),
            self.lab.class_for_resource_type(resource_type),
            path,
        )

    def test_parse_simple(self):
        comps = parse_path("playerBaseStamina")
        self.assertEqual(len(comps), 1)
        self.assertEqual(comps[0].kind, "field")
        self.assertEqual(comps[0].name, "playerBaseStamina")

    def test_parse_nested(self):
        comps = parse_path("gliderConfig.accelerationForward")
        self.assertEqual([c.name for c in comps],
                         ["gliderConfig", "accelerationForward"])

    def test_parse_array_index(self):
        comps = parse_path("values[1]")
        self.assertEqual(comps[0].kind, "field")
        self.assertEqual(comps[0].name, "values")
        self.assertEqual(comps[1].kind, "index")
        self.assertEqual(comps[1].index, 1)

    def test_parse_nested_index(self):
        comps = parse_path("components[2].value")
        self.assertEqual(len(comps), 3)
        self.assertEqual(comps[1].kind, "index")
        self.assertEqual(comps[1].index, 2)

    def test_lua_access_path(self):
        comps = parse_path("components[2].value")
        self.assertEqual(lua_access_path(comps), "data.components[2].value")

    def test_nested_valid_path(self):
        resolution = self._resolve(
            "keen::GameSettingsPresetsResource", "minValues.playerStaminaFactor")
        self.assertTrue(resolution.ok)
        self.assertEqual(resolution.kind_label, "f32")
        self.assertTrue(resolution.editable)

    def test_missing_path(self):
        resolution = self._resolve("keen::BalancingTable", "doesNotExist")
        self.assertFalse(resolution.ok)

    def test_missing_nested_field(self):
        resolution = self._resolve(
            "keen::GameSettingsPresetsResource", "minValues.doesNotExist")
        self.assertFalse(resolution.ok)

    def test_optional_structure_traversal(self):
        # A path through a non-optional nested struct must resolve cleanly.
        resolution = self._resolve("keen::IngameTimeConfig", "sunSetup.zenithAngle")
        self.assertTrue(resolution.ok)
        self.assertEqual(resolution.kind_label, "f32")

    def test_array_indexed_path_resolves(self):
        # presets is Array<keen.ecs.GameSettingsPresetConfig>; index into it.
        resolution = self._resolve(
            "keen::GameSettingsPresetsResource", "presets[1]")
        # Indexing yields the element type (a named class); that's a leaf that
        # is not itself editable, but the path is structurally valid.
        self.assertTrue(resolution.ok)

    def test_array_requires_index(self):
        resolution = self._resolve(
            "keen::GameSettingsPresetsResource", "presets")
        self.assertFalse(resolution.ok)

    def test_enum_field_classified(self):
        # keen.ecs.GameSettings.tombstoneMode is an enum-like named type.
        resolution = self._resolve(
            "keen::GameSettingsPresetsResource", "minValues.tombstoneMode")
        self.assertTrue(resolution.ok)
        self.assertEqual(resolution.kind_label, "enum")
        self.assertTrue(resolution.editable)
        self.assertTrue(resolution.choices)


if __name__ == "__main__":
    unittest.main()
