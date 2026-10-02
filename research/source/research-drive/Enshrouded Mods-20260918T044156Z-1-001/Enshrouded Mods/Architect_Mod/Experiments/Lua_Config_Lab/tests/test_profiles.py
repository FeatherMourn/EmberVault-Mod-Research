"""Tests for profile serialization and semantic equality."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from architect_lua_config_lab.core.profile import (
    Edit,
    Profile,
    Target,
    load_profile,
    profile_hash,
    save_profile,
    semantic_equal,
)


def _profile() -> Profile:
    return Profile(
        name="Baseline Test",
        description="startup experiment",
        game_build="1076226",
        types_lua_sha256="deadbeef",
        edits=[
            Edit(
                enabled=True,
                resource_type="keen::BalancingTable",
                target=Target(mode="first"),
                path="playerBaseStamina",
                schema_type="u32",
                value=500,
                evidence_state="EXPERIMENTAL",
            ),
            Edit(
                enabled=False,
                resource_type="keen::BalancingTable",
                target=Target(mode="match", selector={
                    "field": "itemId.value", "operator": "eq", "value": 123,
                }),
                path="playerBaseHealth",
                schema_type="u32",
                value=1000,
                evidence_state="SCHEMA_VALIDATED",
                expected_original=500,
            ),
        ],
    )


class ProfileTests(unittest.TestCase):
    def test_round_trip_semantic_equality(self):
        profile = _profile()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "profile.json")
            save_profile(profile, path)
            loaded = load_profile(path)
        self.assertTrue(semantic_equal(profile, loaded))

    def test_version_preserved(self):
        profile = _profile()
        data = profile.to_dict()
        self.assertEqual(data["profile_version"], 1)
        self.assertEqual(Profile.from_dict(data).profile_version, 1)

    def test_hash_stable(self):
        self.assertEqual(profile_hash(_profile()), profile_hash(_profile()))

    def test_hash_changes_with_value(self):
        a = _profile()
        b = _profile()
        b.edits[0].value = 999
        self.assertNotEqual(profile_hash(a), profile_hash(b))

    def test_validation_accepts_valid(self):
        self.assertIsNone(_profile().validate())

    def test_validation_rejects_unknown_mode(self):
        profile = _profile()
        profile.edits[0].target.mode = "bogus"
        self.assertIsNotNone(profile.validate())


if __name__ == "__main__":
    unittest.main()
