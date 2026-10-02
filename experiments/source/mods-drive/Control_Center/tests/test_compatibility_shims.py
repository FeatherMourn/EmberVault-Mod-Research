import unittest

from core.compatibility import CompatibilityEngine
from core.compatibility_shims import CompatibilityShimService


class CompatibilityShimTests(unittest.TestCase):
    def test_legacy_manifest_is_adapted_without_mutation(self):
        source = {"id": "old", "required_api": "assets.create_resource"}
        adapted, shims = CompatibilityShimService().adapt_manifest(source)
        self.assertEqual(adapted["required_loader_api"], "assets.register_resource")
        self.assertNotIn("required_loader_api", source)
        self.assertTrue(shims)

    def test_engine_reports_applied_shim(self):
        report = CompatibilityEngine().evaluate({"id": "old", "required_api": "assets.create_resource"}, "1076226", {"assets.register_resource"})
        self.assertTrue(report.compatible)
        self.assertTrue(any(issue.code == "compatibility_shim" for issue in report.issues))


if __name__ == "__main__":
    unittest.main()
