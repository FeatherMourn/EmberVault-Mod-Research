import json
import tempfile
import unittest
from pathlib import Path

from core.manager import ModuleManager


class ManagerFeatureGateTests(unittest.TestCase):
    def test_explicit_research_only_module_cannot_be_enabled(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); module = root / "modules" / "probe"; module.mkdir(parents=True)
            (module / "module.json").write_text(json.dumps({"id": "probe", "name": "Probe", "feature_state": "research-only", "settings": []}), encoding="utf-8")
            manager = ModuleManager(root)
            manager.set_module_enabled("probe", True)
            self.assertFalse(manager.active_config["enabled_modules"]["probe"])


if __name__ == "__main__":
    unittest.main()
