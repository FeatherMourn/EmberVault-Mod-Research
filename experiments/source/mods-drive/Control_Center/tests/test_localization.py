import tempfile
import unittest
from pathlib import Path

from core.localization import LocalizationService


class LocalizationTests(unittest.TestCase):
    def test_catalog_has_deterministic_keys_and_fallback(self):
        catalog = LocalizationService().build("sample_mod", {"Palm Bed": {"en": "Palm Bed", "de": "Palmenbett"}})
        self.assertTrue(catalog.valid)
        self.assertEqual(catalog.resolve("sample_mod.palm_bed", "fr"), "Palm Bed")
        self.assertEqual(catalog.resolve("sample_mod.palm_bed", "de"), "Palmenbett")

    def test_region_language_falls_back_to_base_language(self):
        catalog = LocalizationService().build("sample_mod", {"bed": {"en": "Bed", "de-DE": "Bett"}})
        self.assertEqual(catalog.resolve("sample_mod.bed", "de-DE"), "Bett")
        self.assertEqual(catalog.resolve("sample_mod.bed", "de-AT"), "Bett")
        self.assertEqual(catalog.resolve("sample_mod.bed", "EN-us"), "Bed")

    def test_slug_collisions_are_rejected(self):
        catalog = LocalizationService().build("sample_mod", {"Palm Bed": {"en": "One"}, "palm-bed": {"en": "Two"}})
        self.assertFalse(catalog.valid)
        self.assertTrue(any("collides" in issue.message for issue in catalog.issues))

    def test_saved_payload_validation_rejects_bad_language_and_empty_text(self):
        issues = LocalizationService.validate_payload({
            "schema": "control_center.localization.v1",
            "namespace": "sample_mod",
            "default_language": "en",
            "entries": {"sample_mod.bed": {"english": "Bad", "en": ""}},
        })
        self.assertTrue(any("Invalid language" in issue.message for issue in issues))
        self.assertTrue(any("Empty translation" in issue.message for issue in issues))

    def test_missing_default_language_is_warning_not_silent(self):
        catalog = LocalizationService().build("sample_mod", {"bed": {"de": "Bett"}})
        self.assertTrue(catalog.valid)
        self.assertTrue(any(issue.severity == "warning" for issue in catalog.issues))

    def test_saved_payload_rejects_foreign_namespace_keys(self):
        issues = LocalizationService.validate_payload({
            "schema": "control_center.localization.v1",
            "namespace": "sample_mod",
            "default_language": "en",
            "entries": {"other_mod.bed": {"en": "Bed"}},
        })
        self.assertTrue(any("must belong to namespace" in issue.message for issue in issues))

    def test_empty_translation_fails(self):
        catalog = LocalizationService().build("sample_mod", {"bed": {"en": ""}})
        self.assertFalse(catalog.valid)

    def test_catalog_writes_research_only_payload(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "localization.json"
            catalog = LocalizationService().build("sample_mod", {"bed": {"en": "Bed"}})
            LocalizationService().save(catalog, path)
            self.assertIn('"feature_state": "research-only"', path.read_text(encoding="utf-8"))

    def test_saved_catalog_loads_with_validation_and_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "localization.json"
            service = LocalizationService()
            service.save(service.build("sample_mod", {"bed": {"en": "Bed", "de": "Bett"}}), path)
            loaded = service.load(path)
            self.assertEqual(loaded.resolve("sample_mod.bed", "de-DE"), "Bett")

    def test_saved_catalog_load_rejects_invalid_payload(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "localization.json"
            path.write_text('{"schema":"control_center.localization.v1","namespace":"sample_mod"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                LocalizationService.load(path)

    def test_lua_payload_is_deterministic_and_explicitly_payload_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            catalog = LocalizationService().build("sample_mod", {"Palm Bed": {"en": "Palm Bed", "de": "Palmenbett"}})
            path = root / "src" / "localization_payload.lua"
            LocalizationService().save_lua_payload(catalog, path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("Payload only", text)
            self.assertIn("sample_mod.palm_bed", text)
            self.assertLess(text.index('["de"]'), text.index('["en"]'))

    def test_runtime_evidence_cannot_promote_without_ui_proof(self):
        issues = LocalizationService.validate_runtime_evidence({
            "schema": "control_center.localization_probe_result.v1",
            "build": "1076226", "status": "runtime_registration_verified",
            "ui_consumption_verified": False, "promotion_ready": True,
        })
        joined = " ".join(issues)
        self.assertIn("ui_consumption_verified=true", joined)
        self.assertIn("visual_evidence", joined)
        self.assertEqual(LocalizationService.validate_runtime_evidence({
            "schema": "control_center.localization_probe_result.v1",
            "build": "1076226", "status": "runtime_registration_verified",
            "promotion_ready": False, "ui_consumption_verified": False,
        }), ())


if __name__ == "__main__":
    unittest.main()
