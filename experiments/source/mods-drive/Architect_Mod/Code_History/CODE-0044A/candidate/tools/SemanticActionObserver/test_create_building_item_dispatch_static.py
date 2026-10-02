import unittest

from tools.SemanticActionObserver.scan_create_building_item_dispatch_static import build, DEFAULT_EXE, DEFAULT_TYPES


class CreateBuildingItemDispatchStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build(DEFAULT_EXE, DEFAULT_TYPES)

    def test_reflected_member_offsets(self):
        offsets = self.report["memberOffsets"]
        self.assertEqual(offsets["ClientPlayerInput.createBuildingItemAction"]["offset"], "0x1B0")
        self.assertEqual(offsets["ServerConsumedPlayerInput.consumedCreateBuildingItemAction"]["offset"], "0x30")
        action = self.report["actionProtocol"]
        self.assertEqual(action["versionData"]["offset"], "0x0")
        self.assertEqual(action["selectedIndex"]["offset"], "0x4")
        self.assertEqual(action["itemId"]["offset"], "0x8")

    def test_generic_shape_candidates_rejected(self):
        candidates = self.report["versionConsumeCandidates"]
        self.assertEqual(candidates["search"]["actionQualifiedCandidateCount"], 0)
        self.assertEqual(candidates["search"]["status"], "NO_VALIDATED_VERSION_CONSUME_EDGE")
        self.assertTrue(candidates["search"]["rejections"])
        self.assertTrue(all("generic +0/+4/+8" in row["reason"] for row in candidates["search"]["rejections"]))

    def test_no_action_consumer_or_forward_authority_claim(self):
        self.assertEqual(self.report["firstActionConsumer"]["status"], "NOT_FOUND")
        self.assertEqual(self.report["forwardDataFlow"]["itemId"]["status"], "REFLECTION_ONLY")
        self.assertEqual(self.report["forwardDataFlow"]["placementR8D"]["status"], "NOT_CONNECTED")
        self.assertEqual(self.report["analysisResult"], "PARTIAL_STATIC")
        self.assertFalse(self.report["observerDecision"]["install"])
        self.assertFalse(self.report["observerDecision"]["installNow"])

    def test_convergence_rejected(self):
        convergence = self.report["convergenceTests"]
        self.assertEqual(convergence["persistentSelectionPreview"]["status"], "NOT_PROVEN")
        self.assertEqual(convergence["placement0x3E2CD0R8D"]["status"], "NOT_PROVEN")
        self.assertEqual(self.report["uiCreateBuildingItemEvent"]["status"], "UNSOLVED")

    def test_sibling_is_structural_control_only(self):
        control = self.report["siblingActionControl"]["buildingStockCycleAction"]
        self.assertEqual(control["offset"], "0xA4")
        self.assertEqual(control["status"], "STRUCTURAL_CONTROL_ONLY")


if __name__ == "__main__":
    unittest.main()
