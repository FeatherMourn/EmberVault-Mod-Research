import unittest

from core.capability_status import CapabilityStatus, audit_evidence, is_promotable, require_known


class CapabilityStatusTests(unittest.TestCase):
    def test_only_verified_is_promotable(self):
        self.assertTrue(is_promotable(CapabilityStatus.VERIFIED))
        self.assertFalse(is_promotable(CapabilityStatus.RESEARCH_ONLY))

    def test_unknown_status_is_rejected(self):
        with self.assertRaises(ValueError):
            require_known("maybe")

    def test_status_values_are_stable(self):
        self.assertEqual(CapabilityStatus.UNSUPPORTED.value, "unsupported")

    def test_audit_requires_visual_runtime_and_rollback_evidence(self):
        self.assertEqual(audit_evidence({"runtime_verified": True}), CapabilityStatus.EXPERIMENTAL)
        self.assertEqual(audit_evidence({
            "runtime_verified": True, "visual_verified": True,
            "rollback_verified": True,
        }), CapabilityStatus.VERIFIED)


if __name__ == "__main__":
    unittest.main()
