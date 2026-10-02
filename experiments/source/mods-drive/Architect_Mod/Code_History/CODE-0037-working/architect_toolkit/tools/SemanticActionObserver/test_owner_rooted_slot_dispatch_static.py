import unittest

from tools.SemanticActionObserver.scan_owner_rooted_slot_dispatch_static import build, EXE


class OwnerRootedSlotDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build(EXE)

    def test_slot_header_contract(self):
        contract = self.report["slotInitializationContract"]
        self.assertEqual(contract["status"], "PROVEN_STATIC")
        self.assertEqual(contract["fields"]["+0x48"]["instructionRva"], "0x3ED266")
        self.assertEqual(contract["fields"]["+0x4C"]["instructionRva"], "0x3ED260")
        self.assertEqual(contract["fields"]["secondaryIndexSlot"]["instructionRva"], "0x3ED27E")
        self.assertEqual(len(contract["slotZeroing"]["instructions"]), 5)

    def test_exact_allocator_callers_and_no_generic_only_anchor(self):
        calls = self.report["directCallSites"]["slotAllocation"]
        self.assertEqual([row["callRva"] for row in calls],
                         ["0x3E262B", "0x3E2919", "0x3E52BD", "0x3E5578"])
        self.assertEqual(self.report["containerFamily"]["status"], "ANCHORED_OWNER_ROOTED_FAMILY")
        self.assertIn("0x3EE0C0", self.report["containerFamily"]["directFamilyEdge"])

    def test_dispatcher_and_handlers(self):
        dispatch = self.report["dispatcher"]
        self.assertEqual(dispatch["functionRva"], "0x3E5A60")
        self.assertEqual(dispatch["slotResolution"]["callRva"], "0x3E5AC2")
        self.assertEqual(dispatch["discriminator"]["field"], "+0x4C")
        self.assertEqual(dispatch["discriminator"]["handlers"]["5"]["targetRva"], "0x3E5B39")
        self.assertEqual(dispatch["discriminator"]["handlers"]["6"]["targetRva"], "0x3E5B4A")
        self.assertEqual(self.report["value5Handler"]["targetRva"], "0x3E27B0")
        self.assertEqual(self.report["value5Handler"]["familyContinuation"]["targetRva"], "0x3ED1A0")

    def test_lifecycle_and_convergence_remain_unresolved(self):
        lifecycle = self.report["lifecycle"]
        self.assertEqual(lifecycle["allocator"]["classification"], "FREE_LIST_REUSE_OR_BOUNDED_APPEND")
        self.assertEqual(lifecycle["releasePath"]["status"], "NOT_PROVEN")
        self.assertEqual(lifecycle["classification"], "MIXED_LIFETIME_UNRESOLVED")
        self.assertEqual(self.report["analysisResult"], "PARTIAL_STATIC")
        self.assertEqual(self.report["convergenceTests"]["previewOrGhost"]["status"], "NOT_PROVEN")
        self.assertEqual(self.report["convergenceTests"]["commit0x3E2CD0"]["status"], "NOT_PROVEN")
        self.assertFalse(self.report["observerDecision"]["installNow"])
        self.assertFalse(self.report["observerDecision"]["gameHookInstallAuthorized"])

    def test_value5_reads_all_produced_fields(self):
        offsets = {row["fieldOffset"] for row in self.report["value5Handler"]["slotFieldsRead"]}
        self.assertEqual(offsets, {"0x0", "0x8", "0x10", "0x14", "0x18", "0x1C", "0x20", "0x28", "0x2C", "0x34", "0x38", "0x3C"})


if __name__ == "__main__":
    unittest.main()
