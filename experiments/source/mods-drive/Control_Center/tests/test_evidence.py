import unittest

from core.evidence import EvidenceLevel, classify_evidence


class EvidenceTests(unittest.TestCase):
    def test_requires_package_integrity(self):
        state = classify_evidence({"runtime_verified": True})
        self.assertEqual(state.level, EvidenceLevel.REVIEW_REQUIRED)

    def test_runtime_requires_explicit_flag(self):
        state = classify_evidence({"package_valid": True})
        self.assertEqual(state.level, EvidenceLevel.PACKAGED)
        state = classify_evidence({"package_valid": True, "runtime_verified": True})
        self.assertEqual(state.level, EvidenceLevel.RUNTIME_VERIFIED)

    def test_visual_requires_evidence_path(self):
        state = classify_evidence({"package_valid": True, "runtime_verified": True, "visual_verified": True})
        self.assertEqual(state.level, EvidenceLevel.RUNTIME_VERIFIED)
        state = classify_evidence({"package_valid": True, "runtime_verified": True,
                                   "visual_verified": True, "visual_evidence": "capture.png"})
        self.assertEqual(state.level, EvidenceLevel.VISUAL_VERIFIED)


if __name__ == "__main__":
    unittest.main()
