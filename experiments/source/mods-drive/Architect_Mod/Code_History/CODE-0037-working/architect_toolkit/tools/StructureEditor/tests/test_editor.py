from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.StructureEditor.plans import PlacementPlan, load_plan, save_plan
from tools.StructureEditor.transforms import axis_quaternion, quat_inverse, quat_multiply, rotate_point


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "blueprints" / "recorded" / "recorder_test_01.architect.json"


class TransformTests(unittest.TestCase):
    def test_quarter_turn_inverse(self):
        q = axis_quaternion("z", 90); identity = quat_multiply(q, quat_inverse(q))
        self.assertAlmostEqual(identity[0], 0.0, places=6); self.assertAlmostEqual(identity[1], 0.0, places=6)
        self.assertAlmostEqual(identity[2], 0.0, places=6); self.assertAlmostEqual(abs(identity[3]), 1.0, places=6)
        self.assertEqual(tuple(round(v, 6) for v in rotate_point((1, 0, 0), (0, 0, 0), q)), (0.0, 1.0, 0.0))


class PlanTests(unittest.TestCase):
    def setUp(self): self.plan = PlacementPlan.load_source(FIXTURE)

    def test_source_is_immutable_and_reset(self):
        original = [p["localPosition"][:] for p in self.plan.placements]
        self.plan.translate(4, 0, 0); self.assertNotEqual(original, [p["localPosition"] for p in self.plan.placements]); self.plan.reset_to_source(); self.assertEqual(original, [p["localPosition"] for p in self.plan.placements])

    def test_rotate_round_trip_and_four_turns(self):
        original = [(p["localPosition"][:], p["orientationQuaternion"][:]) for p in self.plan.placements]
        for _ in range(4): self.plan.rotate("y", 90)
        for before, after in zip(original, self.plan.placements):
            for a, b in zip(before[0], after["localPosition"]): self.assertAlmostEqual(a, b, places=5)
            for a, b in zip(before[1], after["orientationQuaternion"]): self.assertAlmostEqual(abs(a), abs(b), places=5)

    def test_enable_duplicate_delete_reorder_undo_redo(self):
        first = self.plan.placements[0]["planPlacementId"]; self.plan.set_enabled(False, [first]); self.assertEqual(self.plan.statistics()["enabledPlacements"], 5)
        clone = self.plan.duplicate([first]); self.assertEqual(len(clone), 1); self.assertEqual(self.plan.statistics()["derivedPlacements"], 1)
        self.plan.undo(); self.assertEqual(self.plan.statistics()["totalPlacements"], 6); self.plan.redo(); self.assertEqual(self.plan.statistics()["totalPlacements"], 7)
        self.plan.delete(clone); self.assertEqual(self.plan.statistics()["totalPlacements"], 6)

    def test_selected_enable_disable_and_reorder_boundaries(self):
        first, second = [p["planPlacementId"] for p in self.plan.placements[:2]]
        self.plan.set_enabled(False, [first, second]); self.assertEqual(self.plan.statistics()["enabledPlacements"], 4)
        self.plan.set_enabled(True, [first]); self.assertEqual(self.plan.statistics()["enabledPlacements"], 5)
        self.plan.move_down(first); self.assertEqual(self.plan.placements[1]["planPlacementId"], first)
        self.plan.move_start(first); self.assertEqual(self.plan.placements[0]["planPlacementId"], first)
        self.plan.move_end(first); self.assertEqual(self.plan.placements[-1]["planPlacementId"], first)

    def test_material_substitution_and_source_material(self):
        material = self.plan.placements[0]["material"]; self.plan.substitute_material(99, [self.plan.placements[0]["planPlacementId"]])
        self.assertEqual(self.plan.placements[0]["originalMaterial"], material); self.assertEqual(self.plan.statistics()["plannedMaterialSubstitutions"], 1); self.plan.undo(); self.assertEqual(self.plan.placements[0]["material"], material)

    def test_mirror_is_explicitly_experimental(self):
        self.plan.mirror("x"); self.assertEqual(self.plan.to_dict()["compatibility"]["mirrorCompatibility"], "UNSOLVED")

    def test_strict_save_load(self):
        with tempfile.TemporaryDirectory() as directory:
            original = [p["localPosition"][:] for p in self.plan.placements]
            self.plan.translate(4, 0, 0)
            path = Path(directory) / "plan.architect-plan.json"; save_plan(self.plan, path); loaded = load_plan(path); self.assertEqual(loaded.to_dict()["schema"], "architect.placement_plan.v1")
            loaded.reset_to_source(); self.assertEqual(original, [p["localPosition"] for p in loaded.placements])


if __name__ == "__main__": unittest.main()
