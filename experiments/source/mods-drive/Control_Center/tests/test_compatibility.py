import unittest

from core.compatibility import CompatibilityEngine, build_satisfies


class CompatibilityTests(unittest.TestCase):
    def test_build_constraints(self):
        self.assertTrue(build_satisfies("1076226", [">=1070000"]))
        self.assertFalse(build_satisfies("1060000", [">=1070000"]))
        self.assertIsNone(build_satisfies(None, [">=1070000"]))

    def test_full_eml_build_identity_can_be_pinned_exactly(self):
        build = "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"
        self.assertTrue(build_satisfies(build, [build]))
        self.assertFalse(build_satisfies(build, [build.replace("1076226", "1076227")]))
        self.assertTrue(build_satisfies(build, [">=1070000"]))

    def test_missing_capability_blocks_module(self):
        report = CompatibilityEngine().evaluate({"id": "sample", "required_loader_api": "assets.register_resource"}, "1076226", set())
        self.assertFalse(report.compatible)
        self.assertTrue(any(issue.code == "loader_capability_missing" for issue in report.issues))

    def test_research_only_is_warning_without_opt_in(self):
        report = CompatibilityEngine().evaluate({"id": "sample", "feature_state": "research-only"}, "1076226", set())
        self.assertTrue(report.compatible)
        self.assertTrue(any(issue.code == "research_only" for issue in report.issues))

    def test_incompatible_build_is_blocking(self):
        report = CompatibilityEngine().evaluate({"id": "sample", "compatible_game_builds": [">=1076226"]}, "1070000")
        self.assertFalse(report.compatible)

    def test_loader_api_version_mismatch_blocks_module(self):
        engine = CompatibilityEngine(loader_api_version="1.0")
        report = engine.evaluate({"id": "sample", "required_loader_api_version": ">=1.1"}, "1076226")
        self.assertFalse(report.compatible)
        self.assertTrue(any(issue.code == "loader_api_version_incompatible" for issue in report.issues))

    def test_unknown_loader_api_version_is_reported_as_unconfirmed(self):
        report = CompatibilityEngine().evaluate({"id": "sample", "required_loader_api_version": ">=1.1"}, "1076226")
        self.assertTrue(report.compatible)
        self.assertTrue(any(issue.code == "loader_api_version_unknown" for issue in report.issues))

    def test_matching_loader_api_version_satisfies_constraint(self):
        engine = CompatibilityEngine(loader_api_version="1.1")
        report = engine.evaluate({"id": "sample", "required_loader_api_version": ">=1.1"}, "1076226")
        self.assertTrue(report.compatible)
        self.assertFalse(any(issue.code.startswith("loader_api_version_") for issue in report.issues))


if __name__ == "__main__":
    unittest.main()
