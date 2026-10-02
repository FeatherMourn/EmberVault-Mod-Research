import unittest

from tools.SemanticActionObserver.scan_owner_rooted_container_family_static import build, EXE


class OwnerRootedContainerFamilyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.map = build(EXE)

    def test_exact_resolver_callers(self):
        calls = self.map["argumentContracts"]
        self.assertEqual([x["callRva"] for x in calls], ["0x3E262B", "0x3E2919", "0x3E52BD", "0x3E5578"])
        self.assertEqual(self.map["containerFamily"]["r8bValues"], {"0x3E262B": 1, "0x3E2919": 6, "0x3E52BD": 0, "0x3E5578": 5})

    def test_owner_root_anchor(self):
        c = self.map["containerFamily"]
        self.assertEqual(c["ownerRootEquation"], "incoming RCX to 0x3ED1A0 -> RDI (ownerRoot)")
        self.assertIn("+0xA10", c["ownerStorage"]["baseField"])
        self.assertEqual(self.map["returnedPointerSource"]["classification"], "OWNER_ROOTED_CONTAINER_SLOT")

    def test_allocator_classification(self):
        a = self.map["allocator7AEDA0"]
        self.assertEqual(a["classification"], "FREE_LIST_REUSE_OR_BOUNDED_APPEND")
        self.assertIn("reusePath", a)
        self.assertIn("appendPath", a)
        self.assertIn("returns RAX=0", a["notFoundOrExhausted"])

    def test_negative_convergence(self):
        self.assertEqual(self.map["analysisResult"], "PARTIAL_STATIC")
        self.assertEqual(self.map["lifetime"]["classification"], "PERSISTENCE_UNRESOLVED")
        self.assertEqual(self.map["anchoredReadersWriters"]["previewOrCommitReaders"], [])
        self.assertFalse(self.map["observerDecision"]["installNow"])
        self.assertFalse(self.map["observerDecision"]["gameHookInstallAuthorized"])


if __name__ == "__main__":
    unittest.main()
