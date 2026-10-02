import unittest

from construction_sdk.models import Coordinate
from framed_architecture import AppearanceProfile, CompatibilityRegistry, FramedPiece, ShapeCatalog, to_blueprint


class FramedArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.catalog = ShapeCatalog()
        self.registry = CompatibilityRegistry()
        self.registry.register("stone_wall", {"framed_cube", "framed_slope"})

    def test_compatible_piece_converts_to_sdk_piece(self):
        framed = FramedPiece(Coordinate(1, 2, 3), "framed_slope", AppearanceProfile("stone_wall", "stone"), 90)
        piece = framed.to_piece(self.catalog, self.registry)
        self.assertEqual(piece.resource_id, "framed:framed_slope")
        self.assertEqual(piece.material_id, "stone")
        self.assertEqual(piece.orientation, 90)

    def test_incompatible_shape_rejected(self):
        framed = FramedPiece(Coordinate(0, 0, 0), "framed_stairs", AppearanceProfile("stone_wall", "stone"))
        with self.assertRaises(ValueError):
            framed.to_piece(self.catalog, self.registry)

    def test_unknown_shape_rejected(self):
        framed = FramedPiece(Coordinate(0, 0, 0), "unknown", AppearanceProfile("stone_wall", "stone"))
        with self.assertRaises(ValueError):
            framed.to_piece(self.catalog, self.registry)

    def test_assembly_exports_shared_blueprint(self):
        pieces = [
            FramedPiece(Coordinate(5, 0, 5), "framed_cube", AppearanceProfile("stone_wall", "stone")),
            FramedPiece(Coordinate(6, 0, 5), "framed_slope", AppearanceProfile("stone_wall", "stone")),
        ]
        blueprint = to_blueprint("window", pieces, self.catalog, self.registry)
        self.assertEqual(blueprint.source_type, "framed_architecture")
        self.assertEqual(len(blueprint.pieces), 2)
        self.assertEqual(blueprint.metadata["shapes"], ["framed_cube", "framed_slope"])


if __name__ == "__main__":
    unittest.main()
