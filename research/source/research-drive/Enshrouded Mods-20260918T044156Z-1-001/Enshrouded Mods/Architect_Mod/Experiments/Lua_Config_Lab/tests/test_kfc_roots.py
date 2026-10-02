"""Tests for KFC resource-root resolution."""

from __future__ import annotations

import unittest

from architect_lua_config_lab.config import kfc_dir
from architect_lua_config_lab.core.kfc_roots import (
    direct_field_count,
    reachable_nested_class_names,
    resolve_roots,
    roots_from_kfc_directory,
)

from .helpers import make_lab, require_types_lua


class KfcRootsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_types_lua(cls)
        cls.lab = make_lab()

    def test_131_roots_present(self):
        families = roots_from_kfc_directory(kfc_dir())
        self.assertEqual(len(families), 131)

    def test_each_root_resolves_to_one_class(self):
        families = roots_from_kfc_directory(kfc_dir())
        db = self.lab.schema()
        roots = resolve_roots(db, families)
        self.assertEqual(len(roots), 131)
        # Ensure no duplicate resource types.
        resource_types = [entry["resource_type"] for entry in roots]
        self.assertEqual(len(set(resource_types)), 131)

    def test_direct_field_count_matches_expectation(self):
        db = self.lab.schema()
        count = direct_field_count(db, self.lab.root_entries())
        self.assertEqual(count, 864)

    def test_roots_are_marked(self):
        db = self.lab.schema()
        balancing = db.get_class("keen.BalancingTable")
        self.assertTrue(balancing.is_resource_root)
        self.assertEqual(balancing.resource_family, "BalancingTable")

    def test_reachable_nested_classes_nonempty(self):
        db = self.lab.schema()
        reachable = reachable_nested_class_names(db, self.lab.root_entries())
        self.assertGreater(len(reachable), 100)


if __name__ == "__main__":
    unittest.main()
