import unittest

from src.identity import duplicate_groups, identity_key, near_duplicate_pairs


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

    def test_near_duplicates_are_review_flags_not_merges(self):
        left = {"id": "a", "kind": "recipe", "identity": {"name": "wooden bed"}, "build_scope": ["1"]}
        right = {"id": "b", "kind": "recipe", "identity": {"name": "wooden beds"}, "build_scope": ["2"]}
        pairs = near_duplicate_pairs([left, right], threshold=0.8)
        self.assertEqual([pair["left"] for pair in pairs], ["a"])
        self.assertEqual(pairs[0]["builds"], ["1", "2"])


if __name__ == "__main__":
    unittest.main()
