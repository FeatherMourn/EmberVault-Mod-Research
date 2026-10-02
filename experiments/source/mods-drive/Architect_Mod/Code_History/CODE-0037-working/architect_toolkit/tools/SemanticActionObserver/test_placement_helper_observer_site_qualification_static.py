"""Synthetic safety-gate tests for CODE-0005 Gate 1."""
import unittest

from tools.SemanticActionObserver.scan_placement_helper_observer_site_qualification_static import qualify_synthetic


class ObserverSiteQualificationTests(unittest.TestCase):
    def base(self):
        return {"outputLifetimeProven": True}

    def test_contiguous_relocatable_site_eligible(self):
        result = qualify_synthetic(self.base())
        self.assertEqual(result["status"], "QUALIFIED_SAFE_OBSERVER_SITE")

    def test_rip_relative_rejected(self):
        c = self.base(); c["ripRelative"] = True
        self.assertEqual(qualify_synthetic(c)["status"], "NOT_QUALIFIED")

    def test_branch_target_inside_span_rejected(self):
        c = self.base(); c["branchIntoSpan"] = True
        self.assertEqual(qualify_synthetic(c)["status"], "NOT_QUALIFIED")

    def test_live_flags_rejected(self):
        c = self.base(); c["flagsNotPreserved"] = True
        self.assertEqual(qualify_synthetic(c)["status"], "NOT_QUALIFIED")

    def test_stack_alignment_rejected(self):
        c = self.base(); c["stackMisaligned"] = True
        self.assertEqual(qualify_synthetic(c)["status"], "NOT_QUALIFIED")

    def test_existing_hook_overlap_rejected(self):
        c = self.base(); c["hookOverlap"] = True
        self.assertEqual(qualify_synthetic(c)["status"], "NOT_QUALIFIED")

    def test_expected_bytes_mismatch_fail_closed(self):
        c = self.base(); c["expectedBytesMismatch"] = True
        self.assertEqual(qualify_synthetic(c)["status"], "NOT_QUALIFIED")

    def test_unproven_output_lifetime_rejected(self):
        self.assertEqual(qualify_synthetic({})["status"], "NOT_QUALIFIED")

    def test_proven_local_reads_acceptable(self):
        c = self.base(); c["fieldReadsProven"] = True
        self.assertEqual(qualify_synthetic(c)["status"], "QUALIFIED_SAFE_OBSERVER_SITE")

    def test_historical_sites_noneligible(self):
        c = self.base(); c["reasons"] = ["historical rejected RVA"]
        self.assertEqual(qualify_synthetic(c)["status"], "NOT_QUALIFIED")

    def test_relative_branch_rejected(self):
        c = self.base(); c["relativeBranch"] = True
        self.assertEqual(qualify_synthetic(c)["status"], "NOT_QUALIFIED")

    def test_split_instruction_rejected(self):
        c = self.base(); c["splitInstruction"] = True
        self.assertEqual(qualify_synthetic(c)["status"], "NOT_QUALIFIED")


if __name__ == "__main__":
    unittest.main()
