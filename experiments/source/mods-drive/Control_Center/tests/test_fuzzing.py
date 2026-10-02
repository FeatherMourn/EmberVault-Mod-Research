import unittest

from core.fuzzing import OfflineFuzzService


class FuzzingTests(unittest.TestCase):
    def test_bounded_malformed_cases_are_rejected(self):
        results = OfflineFuzzService().assert_safe()
        self.assertEqual(len(results), 5)
        self.assertTrue(all(result.rejected for result in results))


if __name__ == "__main__":
    unittest.main()
