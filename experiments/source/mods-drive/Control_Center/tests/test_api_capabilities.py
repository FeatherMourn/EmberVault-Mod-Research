import unittest

from core.api_capabilities import CapabilityRegistry


class CapabilityTests(unittest.TestCase):
    def test_old_create_resource_alias_satisfies_canonical_api(self):
        registry = CapabilityRegistry()
        result = registry.resolve("assets.register_resource", {"assets.create_resource"})
        self.assertTrue(result.supported)
        self.assertEqual(result.matched, "assets.create_resource")

    def test_missing_capability_is_reported(self):
        self.assertEqual(CapabilityRegistry().missing(["assets.get_all_resources"], set()), ["assets.get_all_resources"])

    def test_normalize_adds_canonical_names(self):
        self.assertIn("assets.register_resource", CapabilityRegistry().normalize({"assets.create_resource"}))


if __name__ == "__main__":
    unittest.main()
