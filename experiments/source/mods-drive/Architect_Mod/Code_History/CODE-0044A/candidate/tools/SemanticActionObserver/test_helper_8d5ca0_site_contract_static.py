import json
import unittest
from pathlib import Path

from tools.SemanticActionObserver.scan_helper_8d5ca0_site_contract_static import build_map, EXE, SITE


class Helper8D5CA0ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = build_map(EXE)

    def test_exact_entry_plan_and_boundary(self):
        plan = self.result["site"]["overwritePlan"]
        self.assertEqual(plan["originalBytes"], "40574883ec104c8b09488bfa")
        self.assertEqual(plan["spanBytes"], 12)
        self.assertEqual(plan["continuationRva"], "0x8D5CAC")
        self.assertEqual(len(plan["instructions"]), 4)
        self.assertEqual(sum(i["length"] for i in plan["instructions"]), plan["spanBytes"])

    def test_only_harness_proven_relocation_class(self):
        self.assertEqual(self.result["site"]["relocationCoverage"]["status"], "FULLY_COVERED_ORDINARY_COPY")
        self.assertEqual(self.result["site"]["relocationCoverage"]["unsupported"], [])

    def test_separate_parent_call_contracts(self):
        calls = self.result["callerContracts"]
        self.assertEqual([c["callsiteRva"] for c in calls], ["0x2807C8", "0x2810A3"])
        for c in calls:
            self.assertEqual(c["rdx"]["expression"], "rbp-0x30")
            self.assertEqual(c["r8"]["expression"], "0x100")
            self.assertEqual(c["r9"]["status"], "UNSOLVED_CALLER_SOURCE")

    def test_sources_are_explicit_and_not_promoted(self):
        self.assertEqual(self.result["dataReads"]["A"]["rva"], "0x8D5CC3")
        self.assertEqual(self.result["dataReads"]["R"]["rva"], "0x8D5D00")
        self.assertEqual(self.result["dataReads"]["B"]["rva"], "0x8D5CE2")
        self.assertEqual(self.result["dataReads"]["R"]["status"], "UNSAFE_OR_UNPROVEN_READ")
        self.assertFalse(self.result["semanticClaims"]["lastReachingWriterProven"])

    def test_eligibility_is_fail_closed(self):
        gate = self.result["siteEligibility"]
        self.assertEqual(gate["status"], "PARTIAL_STATIC")
        self.assertFalse(gate["installNow"])
        self.assertFalse(gate["gameHookInstallAuthorized"])
        self.assertGreaterEqual(len(gate["blockers"]), 4)

    def test_producer_and_drain_are_not_overclaimed(self):
        self.assertEqual(self.result["producerModel"]["spscCompatibility"], "UNPROVEN")
        self.assertEqual(self.result["drainHost"]["status"], "DRAIN_HOST_CANDIDATE_PARTIAL")
        self.assertIsNone(self.result["drainHost"]["selected"])


if __name__ == "__main__":
    unittest.main()
