import unittest

from src.analyzer_registry import AnalyzerRegistry
from src.analyzers import AnalyzerSpec


class AnalyzerRegistryTests(unittest.TestCase):
    def test_registry_is_deterministic_and_contract_only(self):
        registry = AnalyzerRegistry()
        spec = AnalyzerSpec("kfc-inspector", "1", ("kfc3",), ("record",))
        registry.register(spec)
        self.assertEqual(registry.get("kfc-inspector", "1"), spec)
        self.assertEqual(registry.manifest()[0]["analyzer_id"], "kfc-inspector")
        with self.assertRaises(ValueError):
            registry.register(spec)

    def test_registry_rejects_network_or_mutating_specs(self):
        registry = AnalyzerRegistry()
        with self.assertRaises(ValueError):
            registry.register(AnalyzerSpec("unsafe", "1", (), (), read_only=False))
        with self.assertRaises(ValueError):
            registry.register(AnalyzerSpec("network", "1", (), (), network_allowed=True))


if __name__ == "__main__":
    unittest.main()
