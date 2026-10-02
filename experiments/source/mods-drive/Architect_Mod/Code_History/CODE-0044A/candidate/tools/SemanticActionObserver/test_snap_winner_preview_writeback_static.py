import unittest
from tools.SemanticActionObserver.scan_snap_winner_preview_writeback_static import build, EXE

class SnapWinnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.m = build(EXE)
    def test_families_and_stride(self):
        fs = self.m["consumerFamilies"]
        self.assertEqual([x["functionRva"] for x in fs], ["0x3EB810", "0x99F970"])
        self.assertEqual(fs[0]["acceptedCollection"]["stride"], "0x50")
    def test_no_winner(self):
        self.assertEqual(self.m["winnerSelection"]["status"], "NO_WINNER_SELECTION_IN_BOUNDED_PATH")
        self.assertTrue(all(x["selection"]["status"] == "NO_WINNER_SELECTION_IN_BOUNDED_PATH" for x in self.m["consumerFamilies"]))
    def test_writeback_unresolved(self):
        self.assertEqual(self.m["persistentWriteback"]["status"], "UNSOLVED_NOT_PERSISTENCE_PROOF")
        self.assertEqual(self.m["convergence"]["previewOwnerIdentity"], "UNSOLVED")
    def test_safety(self):
        self.assertFalse(self.m["installNow"])
        self.assertFalse(self.m["gameHookInstallAuthorized"])
        self.assertFalse(self.m["currentSourceDesignationAuthorized"])
        self.assertFalse(self.m["safety"]["processAccess"])
        self.assertFalse(self.m["safety"]["writesGameMemory"])
        self.assertFalse(self.m["safety"]["runtimeHooksInstalled"])
        self.assertFalse(self.m["safety"]["currentSourceDesignationAuthorized"])
        self.assertFalse(self.m["observerEligibility"]["installNow"])
        self.assertFalse(self.m["observerEligibility"]["gameHookInstallAuthorized"])
        self.assertFalse(self.m["observerEligibility"]["currentSourceDesignationAuthorized"])
        self.assertEqual(self.m["analysisResult"], "PARTIAL_STATIC")

if __name__ == "__main__": unittest.main()
