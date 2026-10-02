"""Tests for provenance and local result recording."""

from __future__ import annotations

import os
import tempfile
import unittest

from architect_lua_config_lab.core.profile import Profile
from architect_lua_config_lab.core.provenance import (
    build_provenance,
    sha256_file,
    sha256_text,
)
from architect_lua_config_lab.core.results import RESULT_VALUES, ResultStore


class ProvenanceTests(unittest.TestCase):
    def test_sha256_text_deterministic(self):
        self.assertEqual(sha256_text("abc"), sha256_text("abc"))
        self.assertEqual(len(sha256_text("abc")), 64)

    def test_sha256_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as handle:
            handle.write("hello")
            path = handle.name
        try:
            self.assertEqual(sha256_file(path), sha256_text("hello"))
            self.assertIsNone(sha256_file("/nonexistent/file.txt"))
        finally:
            os.remove(path)

    def test_provenance_record(self):
        profile = Profile(name="Test", game_build="1076226")
        lua = "-- test lua"
        record = build_provenance(profile, lua)
        self.assertEqual(record["profile_name"], "Test")
        self.assertEqual(record["game_build"], "1076226")
        self.assertEqual(record["generated_lua_sha256"], sha256_text(lua))
        self.assertIn("tool_version", record)
        self.assertIn("generated_at", record)


class ResultStoreTests(unittest.TestCase):
    def test_add_and_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "results.json")
            store = ResultStore(path)
            store.add(
                profile="Baseline", field="playerBaseStamina",
                requested_value=500, result="PASS", notes="stamina increased",
                game_build="1076226",
            )
            self.assertEqual(len(store.records()), 1)
            # Reload from disk.
            store2 = ResultStore(path)
            self.assertEqual(len(store2.records()), 1)
            self.assertEqual(store2.records()[0]["result"], "PASS")

    def test_rejects_unknown_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ResultStore(os.path.join(tmp, "results.json"))
            with self.assertRaises(ValueError):
                store.add(profile="x", field="y", requested_value=1, result="BOGUS")

    def test_result_values(self):
        for value in ("PASS", "NO_EFFECT", "CRASH", "LOAD_FAILURE",
                      "BEHAVIOR_UNCLEAR", "NOT_TESTED"):
            self.assertIn(value, RESULT_VALUES)


if __name__ == "__main__":
    unittest.main()
