import tempfile
import unittest
from pathlib import Path

from tools.ArchitectProductPath.product_path_staging import (
    CANARIES,
    SAFE_PAYLOAD_BYTES,
    SAFE_DIMENSIONS,
    build_manifest,
    private_item_id,
    write_preview_module,
)


class ProductPathStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build_manifest()

    def test_private_ids_are_deterministic_unique_and_nonvanilla(self):
        ids = [private_item_id(canary.name) for canary in CANARIES]
        self.assertEqual(ids, [private_item_id(canary.name) for canary in CANARIES])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(isinstance(value, int) and 0 <= value <= 0xFFFFFFFF for value in ids))
        self.assertTrue(all(row["identityMaterialization"]["itemId"]["status"] == "PROVEN_SOURCE_METHOD" for row in self.report["variants"]))

    def test_safe_payload_policy_is_strict(self):
        self.assertEqual(tuple(self.report["safeCanaryPolicy"]["dimensions"]), SAFE_DIMENSIONS)
        self.assertEqual(self.report["safeCanaryPolicy"]["maxCompressedPayloadBytes"], SAFE_PAYLOAD_BYTES)
        self.assertFalse(self.report["safeCanaryPolicy"]["dynamicArrayResize"])
        for pattern in self.report["patterns"].values():
            self.assertEqual(pattern["compressedLength"], SAFE_PAYLOAD_BYTES)

    def test_no_shared_vanilla_resource_mutation(self):
        self.assertFalse(self.report["gameMutation"])
        self.assertFalse(self.report["adapter"]["sharedVanillaMutation"])
        for row in self.report["variants"]:
            self.assertEqual(row["resourceWrites"], "NOT_EXECUTED_OFFLINE")
            self.assertTrue(row["crossWiredPrivateOnly"] or row["variant"] != "CROSS_WIRED")

    def test_manifest_completeness_and_matrix(self):
        self.assertEqual({row["variant"] for row in self.report["variants"]}, {"CONTROL", "GHOST_VARIANT", "FINAL_VARIANT", "CROSS_WIRED"})
        for row in self.report["variants"]:
            for key in ("variant", "createdPrivateItemId", "privateItemIdCandidate", "identityMaterialization", "resourceIdentities", "sourceTemplateResources", "placement", "ghost", "validationPassed", "evidenceStatus"):
                self.assertIn(key, row)
            self.assertEqual(row["placement"]["compressedLength"], 8)
        control = next(row for row in self.report["variants"] if row["variant"] == "CONTROL")
        ghost = next(row for row in self.report["variants"] if row["variant"] == "GHOST_VARIANT")
        final = next(row for row in self.report["variants"] if row["variant"] == "FINAL_VARIANT")
        self.assertEqual(control["placement"]["payloadSha256"], ghost["placement"]["payloadSha256"])
        self.assertNotEqual(control["ghost"]["previewSha256"], ghost["ghost"]["previewSha256"])
        self.assertNotEqual(control["placement"]["payloadSha256"], final["placement"]["payloadSha256"])

    def test_missing_source_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            report = build_manifest(Path(directory) / "missing_mod.lua")
        self.assertEqual(report["status"], "BLOCKED_MISSING_PROVEN_SOURCE")
        self.assertTrue(all(not row["validationPassed"] for row in report["variants"]))
        self.assertTrue(report["observerDecision"]["failClosed"])

    def test_preview_module_is_disabled_and_has_no_placement_automation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ArchitectProductPathPreview.lua"
            write_preview_module(self.report, path)
            text = path.read_text(encoding="utf-8")
        self.assertIn("enabled = false", text)
        self.assertIn("function M.activate()", text)
        self.assertIn("placementEnabled = false", text)
        self.assertNotIn("BuildingPlaceEvent", text)
        self.assertNotIn("place(", text.lower())
        for row in self.report["variants"]:
            self.assertIn(f"itemId={row['privateItemIdCandidate']}", text)


if __name__ == "__main__":
    unittest.main()
