import unittest

from architect_voxel import (
    arch,
    baseline_shapes,
    box,
    compress_occupancy,
    filled_circle,
    filled_cylinder,
    hollow_cylinder,
    hollow_cube,
    hollow_square,
    line,
    make_shape,
    transform_voxel_set,
    ring,
    sphere,
)
from chunk_planner import plan_voxels
from blueprint_recipe import BlueprintRecipe, deserialize_recipe, serialize_recipe
from f8_protocol import F8Command


class BaselineShapeTests(unittest.TestCase):
    def test_baseline_dimensions_counts_lengths_and_bytes(self):
        expected = {
            "hollow_square_4m": ((8, 1, 8), 28, "ff818181818181ff"),
            "filled_circle_4m": ((8, 1, 8), 52, "3c7effffffff7e3c"),
            "ring_4m": ((8, 1, 8), 36, "3c7ec3c3c3c37e3c"),
            "cross_4m": ((8, 1, 8), 15, "080808ff08080808"),
            "diamond_4m": ((8, 1, 8), 24, "00183c7e7e3c1800"),
            "diagonal_cross_4m": ((8, 1, 8), 16, "8142241818244281"),
            "sphere_2m": ((4, 4, 4), 32, "6006f66ff66f6006"),
            "filled_cylinder_2m": ((4, 4, 4), 48, "f66ff66ff66ff66f"),
            "hollow_cube_2m": ((4, 4, 4), 56, "ffff9ff99ff9ffff"),
            "stairs_2m": ((4, 4, 4), 40, "ffffeeeecccc8888"),
            "pyramid_2m": ((4, 4, 4), 40, "ffffffff60066006"),
            "archway_2m": ((4, 4, 4), 40, "999999999999ffff"),
        }
        actual = baseline_shapes()
        self.assertEqual(set(expected), set(actual))
        for name, (dims, count, payload_hex) in expected.items():
            shape = actual[name]
            self.assertEqual(shape.dimensions, dims)
            self.assertEqual(shape.occupied_count, count)
            self.assertEqual(len(shape.payload), (dims[0] * dims[1] * dims[2] + 7) // 8)
            self.assertEqual(shape.payload.hex(), payload_hex)
            self.assertEqual(shape.payload, actual[name].payload)  # deterministic repeat

        self.assertTrue(all(len(shape.payload) <= 8 for shape in actual.values()))

    def test_parameterized_axes_and_thickness(self):
        self.assertEqual(filled_cylinder((3, 4, 5), axis="x").dimensions, (3, 4, 5))
        self.assertEqual(filled_cylinder((3, 4, 5), axis="z").dimensions, (3, 4, 5))
        self.assertEqual(filled_cylinder((8, 8, 8), axis="y", height=3).occupied_count,
                         filled_cylinder((8, 8, 8), axis="y").occupied_count * 3 // 8)
        self.assertEqual(hollow_cylinder((8, 8, 8), axis="x", height=2).occupied_count,
                         hollow_cylinder((8, 8, 8), axis="x").occupied_count // 4)
        self.assertGreater(hollow_square((8, 1, 8), thickness=2).occupied_count, 28)
        self.assertGreater(hollow_cube((6, 6, 6), thickness=2).occupied_count, hollow_cube((6, 6, 6)).occupied_count)
        self.assertEqual(len(compress_occupancy((1, 1, 1), {(0, 0, 0)})), 1)

    def test_shape_engine_v2_primitives_and_transforms(self):
        for name in ("line", "wall", "floor", "rectangle", "box", "ellipse", "ellipsoid", "dome", "cone", "arch", "ramp", "stairs", "spiral_stairs", "tunnel", "road_strip"):
            kwargs = {"start": (0, 0, 0), "end": (7, 3, 7)} if name == "line" else {}
            shape = make_shape(name, (8, 8, 8), **kwargs)
            self.assertGreater(len(shape.occupied), 0, name)
            self.assertEqual(shape.payload, make_shape(name, (8, 8, 8), **kwargs).payload)
        source = box((3, 3, 3))
        rotated = transform_voxel_set(source, rotation=(0, 1, 0), mirror=(True, False, False), translation=(2, 1, 0))
        self.assertEqual(rotated.occupied_count, source.occupied_count)
        self.assertTrue(all(v >= 0 for p in rotated.occupied for v in p))


class ChunkPlannerTests(unittest.TestCase):
    def test_bounded_tiles_and_round_trip_counts(self):
        shape = sphere((16, 16, 16), radius=8)
        tiles = plan_voxels(shape.dimensions, shape.occupied, (8, 8, 8))
        self.assertEqual(len(tiles), 8)
        self.assertEqual(sum(len(tile.occupied) for tile in tiles), shape.occupied_count)
        self.assertTrue(all(tile.dimensions == (8, 8, 8) for tile in tiles))

    def test_empty_tiles_are_retained(self):
        tiles = plan_voxels((16, 8, 8), {(0, 0, 0)}, (8, 8, 8))
        self.assertEqual(len(tiles), 2)
        self.assertEqual(sum(not tile.is_empty for tile in tiles), 1)


class ProtocolTests(unittest.TestCase):
    def test_recipe_round_trip_and_strict_migration(self):
        recipe = BlueprintRecipe("test", "box", {"dimensions": [2, 2, 2]}, "stone", "center", {"rotation": [0, 0, 0]}, {"tileDimensions": [8, 8, 8]}, {"tags": []})
        self.assertEqual(deserialize_recipe(serialize_recipe(recipe)).to_dict(), recipe.to_dict())
        with self.assertRaises(ValueError): deserialize_recipe('{"schemaVersion": 99}')

    def test_unsupported_f8_operations_are_explicit(self):
        self.assertEqual(F8Command("preview", {}).to_dict()["protocolVersion"], 1)
        with self.assertRaises(ValueError): F8Command("rotate", {}).validate()


if __name__ == "__main__":
    unittest.main()
