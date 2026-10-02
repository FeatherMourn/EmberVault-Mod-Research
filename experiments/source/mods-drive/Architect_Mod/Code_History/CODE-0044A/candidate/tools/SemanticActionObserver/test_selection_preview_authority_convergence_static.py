import unittest

from tools.SemanticActionObserver.scan_selection_preview_authority_convergence_static import build, EXE, ROOT


class SelectionPreviewAuthorityConvergenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build(EXE, ROOT / "bridge")

    def test_unanchored_voxelmodel_front_is_parked(self):
        front = self.report["fronts"]["A_voxelModelGhost"]
        self.assertTrue(front["parked"])
        self.assertEqual(front["status"], "PARKED_NO_ANCHORED_GHOST_PRODUCER")
        self.assertIn("two meaningful hops", front["parkReason"])

    def test_snap_fields_require_same_owner(self):
        front = self.report["fronts"]["B_snapOwner"]
        self.assertEqual(front["sameOwnerAcrossFronts"], False)
        self.assertEqual(front["status"], "STRUCTURAL_OWNER_ONLY")
        self.assertIn("[RSI+0xF0]", front["anchors"]["ownerFields"])

    def test_commit_provenance_is_bounded(self):
        front = self.report["fronts"]["C_commitInputs"]
        self.assertEqual(front["anchors"]["callSite"], "0x280F86")
        self.assertTrue(any("R8D" in hop for hop in front["boundedHops"]))
        self.assertEqual(front["status"], "COMMIT_FRONTIER_OWNER_UNRESOLVED")

    def test_convergence_requires_real_shared_owner(self):
        graph = self.report["convergenceGraph"]
        self.assertEqual(graph["classification"], "NO_CONVERGENCE")
        self.assertTrue(any(edge["status"] == "REJECTED_COINCIDENCE" for edge in graph["edges"]))
        self.assertEqual(self.report["survivingCandidateOwners"], [])

    def test_two_hop_parking_and_parked_branches(self):
        self.assertEqual(self.report["analysisResult"], "E_PARTIAL_STATIC_FRONTIERS_PARKED")
        branches = {row["branch"]: row for row in self.report["parkedBranches"]}
        self.assertEqual(branches["CODE-0009 0x3ED1A0 slot family"]["status"], "PARKED")
        self.assertEqual(branches["CODE-0010 CreateBuildingItemAction consumer"]["status"], "PARKED")

    def test_observer_fail_closed(self):
        self.assertFalse(self.report["observerDecision"]["install"])
        self.assertFalse(self.report["observerDecision"]["installNow"])
        self.assertFalse(self.report["safety"]["runtimeHooksInstalled"])


if __name__ == "__main__":
    unittest.main()
