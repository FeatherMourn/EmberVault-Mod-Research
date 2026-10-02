import unittest
from pathlib import Path

from tools.verify_eml_build_evidence import validate


class EmlBuildEvidenceTests(unittest.TestCase):
    def test_current_build_evidence_is_valid(self):
        path = Path(__file__).resolve().parents[1] / "research" / "EML_BUILD_VERIFICATION_20260928.json"
        result = validate(path)
        self.assertTrue(result["valid"], result)


if __name__ == "__main__":
    unittest.main()
