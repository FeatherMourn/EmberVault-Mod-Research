import tempfile
import unittest
from pathlib import Path

from core.content_identity import ContentIdentityService


class ContentIdentityTests(unittest.TestCase):
    def test_identity_is_deterministic_and_persisted(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "content-identities.json"
            first = ContentIdentityService(path).identity("example_mod", "Palm Wood Bed")
            second = ContentIdentityService(path).identity("example_mod", "Palm Wood Bed")
            self.assertEqual(first, second)
            self.assertGreaterEqual(first.numeric_id, 3_800_000_000)
            self.assertEqual(len(second.guid), 36)

    def test_namespace_ownership_is_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            service = ContentIdentityService(Path(td) / "ids.json")
            identity = service.identity("example_mod", "test")
            service.claim(identity, "author-a")
            with self.assertRaises(ValueError):
                service.claim(identity, "author-b")

    def test_invalid_namespace_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                ContentIdentityService(Path(td) / "ids.json").identity("Bad Namespace", "item")

    def test_identity_skips_known_runtime_ids(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ids.json"
            service = ContentIdentityService(path)
            first = service.identity("example_mod", "first")
            second = service.identity("example_mod", "second", {first.numeric_id})
            self.assertNotEqual(second.numeric_id, first.numeric_id)

    def test_existing_identity_fails_closed_if_runtime_claims_it(self):
        with tempfile.TemporaryDirectory() as td:
            service = ContentIdentityService(Path(td) / "ids.json")
            identity = service.identity("example_mod", "stable")
            with self.assertRaises(ValueError):
                service.identity("example_mod", "stable", {identity.numeric_id})


if __name__ == "__main__":
    unittest.main()
