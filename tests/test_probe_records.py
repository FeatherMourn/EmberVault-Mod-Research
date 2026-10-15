import unittest

from src.probe_records import validate_probe_collection, validate_probe_record


def record(**overrides):
    value = {
        "probe_id": "platform-inventory",
        "probe_version": "1",
        "game_build": "25936191",
        "eml_version": "0.1.2-kfc4",
        "started_at": "2026-10-15T00:00:00Z",
        "completed_at": "2026-10-15T00:01:00Z",
        "input_hashes": ["sha256:input"],
        "output_hashes": ["sha256:output"],
        "evidence_state": "observed",
        "limitations": ["Read-only export; no runtime mutation."],
        "errors": [],
        "read_only": True,
        "runtime_approval": False,
    }
    value.update(overrides)
    return value


class ProbeRecordTests(unittest.TestCase):
    def test_validates_read_only_record(self):
        self.assertTrue(validate_probe_record(record())["valid"])

    def test_rejects_missing_hashes(self):
        with self.assertRaises(ValueError):
            validate_probe_record(record(output_hashes=[]))

    def test_rejects_runtime_approval(self):
        with self.assertRaises(ValueError):
            validate_probe_record(record(runtime_approval=True))

    def test_summarizes_collection_states(self):
        result = validate_probe_collection({"schema_version": 1, "read_only": True, "records": [record(), record(evidence_state="partial")]})
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["by_state"]["partial"], 1)


if __name__ == "__main__":
    unittest.main()
