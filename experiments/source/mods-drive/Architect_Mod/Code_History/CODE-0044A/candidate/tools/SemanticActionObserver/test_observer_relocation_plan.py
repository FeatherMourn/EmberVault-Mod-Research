import unittest

from tools.SemanticActionObserver.build_observer_relocation_plan import plan_from_bytes


class RelocationPlannerTests(unittest.TestCase):
    def test_whole_instruction_growth_and_ordinary_copy(self):
        # push rbp; mov rbp,rsp; sub rsp,20h; nop => 9 bytes, no split.
        p = plan_from_bytes(bytes.fromhex("55 48 89 e5 48 83 ec 20 90"), minimum_patch_bytes=8)
        self.assertEqual(p["status"], "PLANNED")
        self.assertEqual(p["spanBytes"], 8)
        self.assertEqual(p["continuationRva"], 8)
        self.assertTrue(all(i["relocation"] == "ORDINARY_COPY" for i in p["instructions"]))

    def test_rip_relative_fails_closed(self):
        p = plan_from_bytes(bytes.fromhex("48 8b 05 00 00 00 00 90 90 90 90 90"), minimum_patch_bytes=8)
        self.assertEqual(p["status"], "REJECTED")
        self.assertEqual(p["reason"], "relocationRequiresReviewedRewrite")

    def test_relative_call_jumps_and_jcc_fail_closed(self):
        for blob in ("e8 00 00 00 00 90 90 90 90 90 90 90", "eb 02 90 90 90 90 90 90 90 90 90 90", "75 02 90 90 90 90 90 90 90 90 90 90"):
            self.assertEqual(plan_from_bytes(bytes.fromhex(blob), minimum_patch_bytes=5)["status"], "REJECTED")

    def test_external_branch_into_middle_rejected(self):
        p = plan_from_bytes(bytes.fromhex("48 89 c8 48 89 d0 90 90"), minimum_patch_bytes=6,
                            external_targets=[3])
        self.assertEqual(p["reason"], "externalBranchIntoDisplacedSpan")

    def test_plan_hash_deterministic(self):
        blob = bytes.fromhex("48 89 c8 48 89 d0 90 90")
        self.assertEqual(plan_from_bytes(blob, minimum_patch_bytes=6)["planHash"],
                         plan_from_bytes(blob, minimum_patch_bytes=6)["planHash"])


if __name__ == "__main__":
    unittest.main()
