import unittest

from core.loader_adapter import EmlCompatibilityAdapter, LoaderIdentity


class LoaderAdapterTests(unittest.TestCase):
    def test_normalizes_legacy_capability_and_checks_requirements(self):
        adapter = EmlCompatibilityAdapter(LoaderIdentity("EML", "local", "abc123", "control-center-fork"))
        result = adapter.inspect(["assets.create_resource", "assets.get_all_resources"], ["assets.register_resource", "assets.get_all_resources"])
        self.assertTrue(result.compatible)
        self.assertIn("assets.register_resource", result.capabilities)
        self.assertTrue(any("legacy" in warning for warning in result.warnings))

    def test_reports_missing_capabilities_and_incomplete_provenance(self):
        adapter = EmlCompatibilityAdapter(LoaderIdentity("EML", "local", None, "local-fork"))
        result = adapter.inspect([], ["assets.register_resource"])
        self.assertFalse(result.compatible)
        self.assertEqual(result.missing, ("assets.register_resource",))
        self.assertTrue(any("upstream commit" in warning for warning in result.warnings))

    def test_manifest_is_stable_and_explicit(self):
        identity = LoaderIdentity("EML", "local", "abc123", "fork")
        manifest = EmlCompatibilityAdapter.manifest(identity, ["assets.get_all_resources", "assets.register_resource"])
        self.assertEqual(manifest["schema"], "control_center.loader_provenance.v1")
        self.assertEqual(manifest["capabilities"], ["assets.get_all_resources", "assets.register_resource"])


if __name__ == "__main__":
    unittest.main()
