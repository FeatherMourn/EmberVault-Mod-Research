import importlib
import unittest


class PublicExportTests(unittest.TestCase):
    def test_independent_packages_import(self):
        expected = {
            "construction_sdk": ["Blueprint", "UnavailableRuntimeAdapter"],
            "blueprint_library": ["BlueprintLibrary"],
            "worldwright": ["Selection", "paste_plan"],
            "zooping": ["wall", "floor"],
            "builders_wand": ["row", "plane"],
            "chiselcraft": ["MicroStructure"],
            "framed_architecture": ["FramedPiece", "to_blueprint"],
            "restoration": ["compare", "make_plan"],
            "kinetic_works": ["KineticNetwork"],
        }
        for module_name, symbols in expected.items():
            with self.subTest(module=module_name):
                module = importlib.import_module(module_name)
                for symbol in symbols:
                    self.assertTrue(hasattr(module, symbol), f"{module_name}.{symbol}")
                for symbol in getattr(module, "__all__", []):
                    self.assertTrue(hasattr(module, symbol), f"{module_name}.__all__.{symbol}")


if __name__ == "__main__":
    unittest.main()
