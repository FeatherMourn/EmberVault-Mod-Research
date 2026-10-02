import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from tools.validate_external_content_route import _discover_recipe_guid, run


class ExternalContentRouteValidatorTests(unittest.TestCase):
    def test_recipe_guid_auto_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "RecipeRegistryResource"
            root.mkdir()
            (root / "recipes.json").write_text(json.dumps({
                "recipes": [{"recipeId": {"value": 123}, "recipeGuid": "generated-guid"}]
            }), encoding="utf-8")
            self.assertEqual(_discover_recipe_guid(root.parent, 123), "generated-guid")

    def test_live_installation_is_refused_before_external_tools_run(self):
        args = Namespace(
            game_dir=r"H:\SteamLibrary\steamapps\common\Enshrouded",
            emm="missing",
            parser="missing",
            item_id=1,
            recipe_id=2,
            debug_name="x",
            recipe_guid="auto",
            probe=None,
            expected_build="build",
            output=None,
        )
        with self.assertRaises(SystemExit) as raised:
            run(args)
        self.assertIn("live Enshrouded", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
