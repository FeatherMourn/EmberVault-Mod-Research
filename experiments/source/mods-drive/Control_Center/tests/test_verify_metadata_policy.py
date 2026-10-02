import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_metadata_policy import verify


class MetadataPolicyVerifierTests(unittest.TestCase):
    def test_rejects_verified_quarantined_overlap(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "research").mkdir()
            evidence = root / "evidence.json"
            evidence.write_text("{}", encoding="utf-8")
            policy = root / "research" / "policy.json"
            policy.write_text(json.dumps({
                "schema": "control_center.safe_metadata_resource_types.v1",
                "verified_types": [{"type": "keen::ItemInfo", "evidence": "evidence.json"}],
                "quarantined_types": [{"type": "keen::ItemInfo", "evidence": "evidence.json"}],
            }), encoding="utf-8")
            result = verify(policy)
            self.assertFalse(result["valid"])
            self.assertTrue(any("both verified and quarantined" in error for error in result["errors"]))

    def test_accepts_valid_policy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "research").mkdir()
            (root / "evidence.json").write_text("{}", encoding="utf-8")
            policy = root / "research" / "policy.json"
            policy.write_text(json.dumps({
                "schema": "control_center.safe_metadata_resource_types.v1",
                "verified_types": [{"type": "keen::ItemInfo", "evidence": "evidence.json"}],
                "quarantined_types": [{"type": "keen::TemplateResource", "evidence": "evidence.json"}],
            }), encoding="utf-8")
            self.assertTrue(verify(policy)["valid"])


if __name__ == "__main__":
    unittest.main()
