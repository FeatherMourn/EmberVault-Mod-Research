import unittest
from tools.SemanticActionObserver.scan_parent_frame_lifetime_correlation_static import build, EXE

class ParentFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.m = build(EXE)
    def test_rsp_interval(self): self.assertEqual(self.m["frameAnalysis"]["effectiveRspStatus"], "PROVEN_STATIC_BUILD_1076226"); self.assertEqual(self.m["frameAnalysis"]["rspWrites"], [])
    def test_rbp_interval(self): self.assertEqual(self.m["frameAnalysis"]["rbpRelationStatus"], "PROVEN_STATIC_BUILD_1076226")
    def test_equations_hypothesis(self): self.assertFalse(self.m["frameAnalysis"]["equationsValidated"]); self.assertEqual(self.m["outputRange"]["bufferInFrame"], "UNPROVEN")
    def test_alias_hazards_conservative(self): self.assertTrue(self.m["postConsumerHazards"]["field38"]["status"].startswith("ALIAS/")); self.assertTrue(self.m["postConsumerHazards"]["field78"]["status"].startswith("ALIAS/"))
    def test_race_unwind_block(self): self.assertEqual(self.m["producerModel"]["spscCompatibility"], "UNPROVEN"); self.assertEqual(self.m["unwind"]["status"], "UNWIND_SUPPORT_UNSOLVED")
    def test_gate_fail_closed(self): self.assertEqual(self.m["correlationGate"]["status"], "CORRELATION_UNPROVEN"); self.assertFalse(self.m["siteEligibility"]["gameHookInstallAuthorized"])

if __name__ == "__main__": unittest.main()
