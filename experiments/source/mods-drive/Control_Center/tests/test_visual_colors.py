import unittest

from core.visual_colors import hex_to_packed_color, packed_color_plan


class VisualColorTests(unittest.TestCase):
    def test_packs_rgba_in_runtime_order(self):
        self.assertEqual(hex_to_packed_color("#B43C3C"), 0xFF3C3CB4)
        self.assertEqual(hex_to_packed_color("#2DB4DC80"), 0x80DCB42D)

    def test_rejects_invalid_hex(self):
        with self.assertRaises(ValueError):
            hex_to_packed_color("blue")

    def test_builds_three_slot_research_plan(self):
        plan = packed_color_plan({"frame": "#B43C3C", "bedding": "#2D6ED2", "trim": "#DCB42D"})
        self.assertEqual(plan["runtime_field"], "itemColorCombinationSetup")
        self.assertEqual(plan["color0"], 0xFF3C3CB4)
        self.assertTrue(plan["isSet"])


if __name__ == "__main__":
    unittest.main()
