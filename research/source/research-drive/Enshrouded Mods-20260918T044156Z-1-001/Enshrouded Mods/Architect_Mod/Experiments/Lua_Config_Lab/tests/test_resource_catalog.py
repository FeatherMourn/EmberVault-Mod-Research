"""Tests for the resource catalog (completeness, uniqueness, search, lookups)."""

from __future__ import annotations

import unittest

from architect_lua_config_lab.core.kfc_roots import load_known_roots
from architect_lua_config_lab.core.resource_catalog import (
    CATEGORIES,
    ResourceCatalog,
)

from .helpers import make_lab, require_types_lua


class ResourceCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_types_lua(cls)
        cls.lab = make_lab()
        cls.catalog = cls.lab.catalog
        cls.known = load_known_roots()["roots"]

    def test_catalog_loaded(self):
        self.assertIsNotNone(self.catalog)

    def test_exactly_131_entries(self):
        self.assertEqual(len(self.catalog.entries), 131)

    def test_validates_clean(self):
        errors = self.catalog.validate(self.known, self.lab.schema())
        self.assertEqual(errors, [], "catalog validation errors: %s" % errors)

    def test_every_known_root_present_exactly_once(self):
        known_types = {r["resource_type"] for r in self.known}
        catalog_types = [e.resource_type for e in self.catalog.entries]
        self.assertEqual(set(catalog_types), known_types)
        self.assertEqual(len(catalog_types), len(set(catalog_types)))

    def test_no_unknown_resource_types(self):
        known_types = {r["resource_type"] for r in self.known}
        for entry in self.catalog.entries:
            self.assertIn(entry.resource_type, known_types)

    def test_required_fields_present(self):
        for entry in self.catalog.entries:
            self.assertTrue(entry.friendly_name, entry.resource_type)
            self.assertTrue(entry.primary_category, entry.resource_type)
            self.assertTrue(entry.description, entry.resource_type)
            self.assertIsInstance(entry.tags, list)

    def test_categories_approved(self):
        for entry in self.catalog.entries:
            self.assertIn(entry.primary_category, CATEGORIES)

    def test_mapped_lua_class_exists(self):
        db = self.lab.schema()
        family_to_class = {r["family"]: r["lua_class"] for r in self.known}
        for entry in self.catalog.entries:
            lua_class = family_to_class.get(entry.family)
            self.assertIsNotNone(lua_class, entry.family)
            self.assertTrue(db.has_class(lua_class), lua_class)

    # -- search --------------------------------------------------------------

    def test_search_stamina(self):
        results = self.catalog.search("stamina")
        families = {r["entry"].family for r in results}
        self.assertIn("BalancingTable", families)

    def test_search_weather(self):
        results = self.catalog.search("weather")
        families = {r["entry"].family for r in results}
        self.assertIn("WeatherSystemResource", families)

    def test_search_blueprint(self):
        results = self.catalog.search("blueprint")
        families = {r["entry"].family for r in results}
        self.assertIn("VoxelBlueprintConfig", families)

    def test_search_case_insensitive(self):
        self.assertTrue(self.catalog.search("BALANCING"))
        self.assertTrue(self.catalog.search("balancing"))

    def test_search_empty_returns_nothing(self):
        self.assertEqual(self.catalog.search(""), [])

    # -- lookups -------------------------------------------------------------

    def test_lookup_by_resource_type(self):
        entry = self.catalog.get("keen::BalancingTable")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.friendly_name, "Game Balance")

    def test_lookup_by_family(self):
        entry = self.catalog.get_by_family("BalancingTable")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.resource_type, "keen::BalancingTable")

    def test_entries_in_category(self):
        entries = self.catalog.entries_in_category("Building & Blueprints")
        self.assertGreater(len(entries), 0)
        for entry in entries:
            self.assertEqual(entry.primary_category, "Building & Blueprints")

    def test_all_categories_used_are_known(self):
        for category in self.catalog.categories_present():
            self.assertIn(category, CATEGORIES)

    def test_friendly_controls_marked(self):
        # The seeded controls touch BalancingTable, so it should be flagged.
        entry = self.catalog.get("keen::BalancingTable")
        self.assertTrue(entry.friendly_controls_available)


if __name__ == "__main__":
    unittest.main()
