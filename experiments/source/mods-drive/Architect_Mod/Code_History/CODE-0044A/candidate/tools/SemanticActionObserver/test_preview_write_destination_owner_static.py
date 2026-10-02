import json
import unittest
from pathlib import Path

from tools.SemanticActionObserver.scan_preview_write_destination_owner_static import build, EXE


class PreviewWriteDestinationOwnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.map = build(EXE)

    def test_supported_build_and_safety_gate(self):
        self.assertEqual(self.map["build"]["exeSha256"],
                         "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781")
        self.assertFalse(self.map["installNow"])
        self.assertFalse(self.map["gameHookInstallAuthorized"])
        self.assertFalse(self.map["currentSourceDesignationAuthorized"])
        self.assertFalse(self.map["safety"]["processAccess"])
        self.assertFalse(self.map["safety"]["writesGameMemory"])

    def test_three_e5480_calls_three_ed1a0(self):
        contract = self.map["callContract"]
        self.assertEqual(contract["callRva"], "0x3E5578")
        self.assertEqual(contract["targetRva"], "0x3ED1A0")
        self.assertTrue(any(x["callRva"] == "0x3E5578" and x["targetRva"] == "0x3ED1A0"
                            for x in self.map["functions"]["0x3ED1A0"]["directCallers"]))

    def test_split_pdata_chain_is_retained(self):
        chunks = self.map["functions"]["0x3ED1A0"]["pdataChunks"]
        self.assertEqual([(x["startRva"], x["endRva"]) for x in chunks], [
            ("0x3ED1A0", "0x3ED1DB"),
            ("0x3ED1DB", "0x3ED296"),
            ("0x3ED296", "0x3ED2B8"),
        ])

    def test_returned_pointer_and_writes(self):
        source = self.map["returnedPointerSource"]
        self.assertEqual(source["classification"], "OWNER_ROOTED_CONTAINER_SLOT")
        self.assertIn("ownerRoot+0xA10", source["storageExpression"])
        writes = self.map["functions"]["0x3E5480"]["returnedPointerWrites"]
        self.assertEqual(len(writes), 11)
        self.assertEqual({x["destination"] for x in writes}, {
            "returnedRAX+0x0", "returnedRAX+0x8", "returnedRAX+0x10",
            "returnedRAX+0x14", "returnedRAX+0x1C", "returnedRAX+0x20",
            "returnedRAX+0x28", "returnedRAX+0x2C", "returnedRAX+0x34",
            "returnedRAX+0x38", "returnedRAX+0x3C",
        })

    def test_no_unproven_promotion(self):
        self.assertEqual(self.map["analysisResult"], "PARTIAL_STATIC")
        self.assertEqual(self.map["lifetime"]["classification"], "PERSISTENCE_UNRESOLVED")
        self.assertEqual(self.map["convergence"]["previewOwner"], "UNSOLVED")
        self.assertEqual(self.map["convergence"]["placementCommit0x3E2CD0"], "NO_CONNECTED_READER_PROVEN")
        self.assertEqual(self.map["anchoredReadersWriters"]["connectedReaders"], [])


if __name__ == "__main__":
    unittest.main()
