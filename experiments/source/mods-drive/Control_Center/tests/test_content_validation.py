import json
import tempfile
import unittest
from pathlib import Path

from core.content_validation import ContentProjectValidator


class ContentValidationTests(unittest.TestCase):
    def test_bed_staging_fixture_is_valid(self):
        project = Path(r"I:\My Drive\Enshrouded Mods\Control_Center\research\staging\bed_clone_kfc_subset_1076226")
        report = ContentProjectValidator().validate(project)
        self.assertTrue(report.valid, [issue.message for issue in report.issues])

    def test_duplicate_content_ids_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "content.json").write_text(json.dumps({
                "id": "sample", "name": "Sample", "version": "1.0.0",
                "namespace": "sample_mod",
                "content": [{"id": "one"}, {"id": "one"}],
            }), encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any(issue.code == "content.id_duplicate" for issue in report.issues))

    def test_invalid_json_resource_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mod.json").write_text(json.dumps({"id": "sample", "name": "Sample", "version": "1.0.0"}), encoding="utf-8")
            (root / "ItemInfo").mkdir()
            (root / "ItemInfo" / "bad.json").write_text("{not json", encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any(issue.code == "resource.json_invalid" for issue in report.issues))

    def test_tampered_asset_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "mod.json").write_text(json.dumps({"id": "sample", "name": "Sample", "version": "1.0.0"}), encoding="utf-8")
            assets = root / "assets" / "icons"; assets.mkdir(parents=True); icon = assets / "icon.png"; icon.write_bytes(b"one")
            from core.asset_service import AssetService
            AssetService().import_file(icon, root, "icons", "copy.png")
            (root / "assets" / "icons" / "copy.png").write_bytes(b"tampered")
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any(issue.code == "assets.integrity" for issue in report.issues))

    def test_tampered_package_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mod.json").write_text(json.dumps({"id": "sample", "name": "Sample", "version": "1.0.0"}), encoding="utf-8")
            payload = root / "src.lua"; payload.write_text("return {}", encoding="utf-8")
            from core.package_service import PackageService
            PackageService().create_manifest(root, "sample", "1.0.0")
            payload.write_text("return {tampered=true}", encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any(issue.code == "package.integrity" for issue in report.issues))

    def test_unlisted_package_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mod.json").write_text(json.dumps({"id": "sample", "name": "Sample", "version": "1.0.0"}), encoding="utf-8")
            (root / "src.lua").write_text("return {}", encoding="utf-8")
            from core.package_service import PackageService
            PackageService().create_manifest(root, "sample", "1.0.0")
            (root / "unexpected.lua").write_text("return {}", encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any("Unlisted packaged file" in issue.message for issue in report.issues))

    def test_template_graph_candidate_hash_is_checked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); candidate = root / "candidate.json"
            candidate.write_text('{"components":[]}', encoding="utf-8")
            (root / "mod.json").write_text(json.dumps({
                "id": "sample", "name": "Sample", "version": "1.0.0",
                "template_graph_plan": {
                    "candidate_path": "candidate.json", "candidate_sha256": "0" * 64
                },
            }), encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any(issue.code == "template_graph.hash_mismatch" for issue in report.issues))

    def test_template_graph_source_hash_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); candidate = root / "candidate.json"; source = root / "donor.json"
            candidate.write_text('{"components":[]}', encoding="utf-8")
            source.write_text('{"version":1}', encoding="utf-8")
            import hashlib
            candidate_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
            (root / "mod.json").write_text(json.dumps({
                "id": "sample", "name": "Sample", "version": "1.0.0",
                "template_graph_plan": {
                    "candidate_path": "candidate.json", "candidate_sha256": candidate_hash,
                    "source": str(source), "source_sha256": "0" * 64
                },
            }), encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any(issue.code == "template_graph.source_changed" for issue in report.issues))

    def test_visual_variant_transform_and_policy_are_validated(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mod.json").write_text(json.dumps({"id": "sample", "name": "Sample", "version": "1.0.0"}), encoding="utf-8")
            (root / "content").mkdir()
            (root / "content" / "visual_variant.json").write_text(json.dumps({
                "scale": [1.0, 1.2, 0.8], "offset": [0.0, 0.1, 0.0],
                "catalog_preview": "custom-research", "placement_preview": "donor-fallback",
                "color_adjustments": [{"target": "frame", "color": "#442233"}],
            }), encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertTrue(report.valid, [issue.message for issue in report.issues])

    def test_visual_variant_invalid_transform_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mod.json").write_text(json.dumps({"id": "sample", "name": "Sample", "version": "1.0.0"}), encoding="utf-8")
            (root / "content").mkdir()
            (root / "content" / "visual_variant.json").write_text(json.dumps({
                "scale": [1.0, 0.0], "catalog_preview": "unsafe-preview",
            }), encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any(issue.code == "visual_variant.transform_invalid" for issue in report.issues))
            self.assertTrue(any(issue.code == "visual_variant.preview_policy_invalid" for issue in report.issues))

    def test_visual_variant_invalid_color_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mod.json").write_text(json.dumps({"id": "sample", "name": "Sample", "version": "1.0.0"}), encoding="utf-8")
            (root / "content").mkdir()
            (root / "content" / "visual_variant.json").write_text(json.dumps({
                "color_adjustments": [{"target": "frame", "color": "not-a-color"}],
            }), encoding="utf-8")
            report = ContentProjectValidator().validate(root)
            self.assertFalse(report.valid)
            self.assertTrue(any(issue.code == "visual_variant.color_invalid" for issue in report.issues))


if __name__ == "__main__":
    unittest.main()
