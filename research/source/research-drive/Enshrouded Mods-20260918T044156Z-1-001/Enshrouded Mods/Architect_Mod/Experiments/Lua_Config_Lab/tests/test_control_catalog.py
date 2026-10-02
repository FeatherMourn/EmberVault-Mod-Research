"""Tests for the friendly control catalog and control -> ProfileEdit mapping."""

from __future__ import annotations

import unittest

from architect_lua_config_lab.core.control_catalog import UI_TYPES
from architect_lua_config_lab.core.profile import EVIDENCE_STATES
from architect_lua_config_lab.core.resource_catalog import CATEGORIES

from .helpers import make_lab, require_types_lua


class ControlCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_types_lua(cls)
        cls.lab = make_lab()
        cls.controls = cls.lab.controls

    def test_controls_loaded(self):
        self.assertIsNotNone(self.controls)
        self.assertGreaterEqual(len(self.controls.controls), 5)

    def test_validates_clean(self):
        errors = self.controls.validate(self.lab.schema())
        self.assertEqual(errors, [], "control catalog errors: %s" % errors)

    def test_required_fields(self):
        for control in self.controls.controls:
            self.assertTrue(control.id)
            self.assertTrue(control.name)
            self.assertTrue(control.description)
            self.assertIn(control.category, CATEGORIES)
            self.assertIn(control.ui_type, UI_TYPES)
            self.assertIn(control.status, EVIDENCE_STATES)
            self.assertTrue(control.resource_type)
            self.assertTrue(control.path)

    def test_unique_ids(self):
        ids = [c.id for c in self.controls.controls]
        self.assertEqual(len(ids), len(set(ids)))

    def test_control_to_edit_matches_advanced(self):
        """A friendly control must produce the same ProfileEdit as the
        Advanced editor's make_edit for the same resource/path/value/target."""
        control = self.controls.get("balance.player_base_stamina")
        self.assertIsNotNone(control)

        edit_from_control, err1 = self.lab.make_control_edit(control, 500)
        self.assertIsNone(err1)

        edit_from_advanced, err2 = self.lab.make_edit(
            resource_type="keen::BalancingTable",
            path="playerBaseStamina",
            value=500,
            mode="first",
            evidence_state="EXPERIMENTAL",
        )
        self.assertIsNone(err2)

        self.assertEqual(edit_from_control.to_dict(), edit_from_advanced.to_dict())

    def test_control_value_validation_rejects_bad_value(self):
        control = self.controls.get("balance.player_base_stamina")
        edit, error = self.lab.make_control_edit(control, 999999999999)
        self.assertIsNone(edit)
        self.assertIsNotNone(error)

    def test_control_value_validation_accepts_good_value(self):
        control = self.controls.get("slope.sliding_angle")
        edit, error = self.lab.make_control_edit(control, 45.0)
        self.assertIsNone(error)
        self.assertIsNotNone(edit)
        self.assertEqual(edit.schema_type, "f32")
        self.assertEqual(edit.value, 45.0)

    def test_nested_path_control(self):
        control = self.controls.get("settings.min_player_stamina_factor")
        self.assertIsNotNone(control)
        edit, error = self.lab.make_control_edit(control, 1.5)
        self.assertIsNone(error)
        self.assertEqual(edit.path, "minValues.playerStaminaFactor")

    def test_control_edit_generates_lua(self):
        from architect_lua_config_lab.core.profile import Profile

        control = self.controls.get("balance.player_base_health")
        edit, error = self.lab.make_control_edit(control, 1000)
        self.assertIsNone(error)
        profile = Profile(name="Control Test", game_build="1076226", edits=[edit])
        lua = self.lab.generate(profile)
        self.assertIn("playerBaseHealth", lua)
        self.assertIn("value = 1000", lua)


if __name__ == "__main__":
    unittest.main()
