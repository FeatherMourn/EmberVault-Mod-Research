import unittest

from src.identity import duplicate_groups, identity_key


class IdentityTests(unittest.TestCase):
    def test_identity_normalizes_case_and_whitespace(self):
        left = {"id": "a", "kind": "donor", "identity": {"name": " Bed  "}, "build_scope": ["1"]}
        right = {"id": "b", "kind": "DONOR", "identity": {"name": "bed"}, "build_scope": ["1"]}
        self.assertEqual(identity_key(left), identity_key(right))
        self.assertEqual(duplicate_groups([left, right]), [["a", "b"]])

    def test_build_scope_can_remain_distinct(self):
        left = {"id": "a", "kind": "donor", "identity": {"name": "bed"}, "build_scope": ["1"]}
        right = {"id": "b", "kind": "donor", "identity": {"name": "bed"}, "build_scope": ["2"]}
        self.assertEqual(duplicate_groups([left, right]), [])
        self.assertEqual(duplicate_groups([left, right], include_build=False), [["a", "b"]])


if __name__ == "__main__":
    unittest.main()
