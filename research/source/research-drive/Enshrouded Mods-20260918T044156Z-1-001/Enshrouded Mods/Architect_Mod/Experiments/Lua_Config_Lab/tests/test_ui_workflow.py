"""Tests for the MyChangesView and UI wiring."""

import unittest
from architect_lua_config_lab.core.lab import Lab
from architect_lua_config_lab.core.profile import Profile
from architect_lua_config_lab.config import (
    types_lua_path,
    base_lua_path,
    kfc_dir,
    cache_dir,
)
from architect_lua_config_lab.ui.main_window import MainWindow


class TestUIWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class DummyArgs:
            types_lua = types_lua_path()
            base_lua = base_lua_path()
            kfc_dir = kfc_dir()
            no_cache = False

        cls.args = DummyArgs()
        cls.window = MainWindow(cls.args)
        cls.window.withdraw()  # keep offscreen during tests

    @classmethod
    def tearDownClass(cls):
        cls.window.destroy()

    def test_navigation_views(self):
        w = self.window
        w.show_home()
        self.assertIsNotNone(w.home_view)

        w.show_category('Player & Game Balance')
        self.assertEqual(w.category_view.category, 'Player & Game Balance')

        w.show_resource('keen::BalancingTable')
        self.assertEqual(w.resource_view.resource_type, 'keen::BalancingTable')

        w.show_search('health')
        self.assertTrue(len(w.search_view._results) > 0)

        w.show_all_resources()
        self.assertEqual(len(w.all_resources_view._rows), 131)

        w.show_my_changes()
        self.assertIsNotNone(w.my_changes_view)

        w.show_advanced('keen::BalancingTable')
        self.assertEqual(w.advanced_view.current_resource_type, 'keen::BalancingTable')

    def test_control_addition_and_my_changes_view(self):
        w = self.window
        w.profile = Profile(name="TestPreset", game_build="1076226")
        self.assertEqual(len(w.profile.edits), 0)

        # Get a control from catalog
        control = next(c for c in w.controls.controls if c.id == 'balance.player_base_health')
        edit, err = w.lab.make_control_edit(control, 150.0)
        self.assertIsNone(err)
        self.assertIsNotNone(edit)

        w.profile.edits.append(edit)
        w.refresh_changes_badge()
        self.assertIn("(1)", w.changes_btn_var.get())

        w.show_my_changes()
        self.assertEqual(len(w.my_changes_view._edit_rows), 1)

        # Toggle edit
        children = w.my_changes_view.tree.get_children()
        w.my_changes_view.tree.selection_set(children[0])
        w.my_changes_view._toggle()
        self.assertFalse(edit.enabled)


if __name__ == '__main__':
    unittest.main()
