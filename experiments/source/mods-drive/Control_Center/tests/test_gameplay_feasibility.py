import unittest
import json
import subprocess
import sys
from pathlib import Path

from core.gameplay_feasibility import GameplayArea, GameplayFeasibilityPlanner


class GameplayFeasibilityTests(unittest.TestCase):
    def test_multiplayer_is_not_overclaimed(self):
        result = GameplayFeasibilityPlanner().assess(GameplayArea.MULTIPLAYER_AUTHORITY)
        self.assertEqual(result.state, "unsupported")

    def test_interaction_remains_research_only_until_custom_graph_is_verified(self):
        result = GameplayFeasibilityPlanner().assess("interaction")
        self.assertEqual(result.state, "research-only")
        self.assertIn("custom interaction graph construction is unverified", result.blockers)
        self.assertEqual(result.next_probe, "inventory an asset-backed donor and verify single-player readback")

    def test_ai_remains_research_only(self):
        result = GameplayFeasibilityPlanner().assess(GameplayArea.AI)
        self.assertEqual(result.state, "research-only")

    def test_interaction_probe_is_explicitly_read_only(self):
        spec = GameplayFeasibilityPlanner.interaction_probe_spec("donor-guid", "Open", "opens donor")
        self.assertEqual(spec["schema"], "control_center.interaction_probe.v1")
        self.assertFalse(spec["runtime_mutation"])
        self.assertEqual(spec["authority"], "unknown")
        self.assertEqual(spec["execution_scope"], "single-player-read-only")
        self.assertIn("identify owning resource or ECS component", spec["authority_checks"])

    def test_interaction_probe_requires_identity(self):
        with self.assertRaises(ValueError):
            GameplayFeasibilityPlanner.interaction_probe_spec("", "Open")

    def test_builder_placement_probe_is_read_only(self):
        spec = GameplayFeasibilityPlanner.builder_placement_spec(2940001508, "castle beds")
        self.assertEqual(spec["schema"], "control_center.builder_placement_probe.v1")
        self.assertFalse(spec["runtime_mutation"])
        self.assertEqual(spec["authority"], "unknown")

    def test_builder_placement_probe_requires_positive_item(self):
        with self.assertRaises(ValueError):
            GameplayFeasibilityPlanner.builder_placement_spec(0)

    def test_validate_report_enforces_interaction_probe_safety(self):
        report = {
            "schema": "control_center.gameplay_feasibility.v1",
            "runtime_mutation": False,
            "assessments": [{"area": "interaction"}],
            "interaction_probe": GameplayFeasibilityPlanner.interaction_probe_spec("guid", "Open"),
        }
        self.assertEqual(GameplayFeasibilityPlanner.validate_report(report), ())
        report["interaction_probe"]["runtime_mutation"] = True
        self.assertIn("interaction probe must be read-only", GameplayFeasibilityPlanner.validate_report(report))

    def test_validate_report_rejects_placeholder_interaction_donor(self):
        report = {
            "schema": "control_center.gameplay_feasibility.v1",
            "runtime_mutation": False,
            "assessments": [{"area": "interaction"}],
            "interaction_probe": GameplayFeasibilityPlanner.interaction_probe_spec("donor-guid", "Open"),
        }
        self.assertIn("placeholder", " ".join(GameplayFeasibilityPlanner.validate_report(report)))

    def test_saved_report_validation_is_conservative(self):
        report = {"schema": "control_center.gameplay_feasibility.v1", "assessments": [], "runtime_mutation": False}
        self.assertTrue(GameplayFeasibilityPlanner.validate_report(report))
        report["assessments"] = [{"area": "ai", "state": "research-only"}]
        self.assertEqual(GameplayFeasibilityPlanner.validate_report(report), ())

    def test_matrix_covers_all_areas_and_cli_is_read_only(self):
        matrix = GameplayFeasibilityPlanner().all_assessments()
        self.assertEqual({item.area for item in matrix}, set(GameplayArea))
        result = subprocess.run([sys.executable, "tools/report_gameplay_feasibility.py"], cwd=Path(__file__).parents[1], capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        self.assertEqual(report["schema"], "control_center.gameplay_feasibility.v1")
        self.assertFalse(report["runtime_mutation"])

    def test_cli_can_emit_interaction_probe_contract(self):
        result = subprocess.run([
            sys.executable, "tools/report_gameplay_feasibility.py",
            "--interaction-guid", "donor-guid", "--interaction-key", "Open",
        ], cwd=Path(__file__).parents[1], capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        self.assertEqual(report["interaction_probe"]["schema"], "control_center.interaction_probe.v1")

    def test_cli_can_emit_builder_placement_contract(self):
        result = subprocess.run([
            sys.executable, "tools/report_gameplay_feasibility.py",
            "--builder-item-id", "2940001508", "--builder-plan", "castle beds",
        ], cwd=Path(__file__).parents[1], capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        self.assertEqual(report["builder_placement_probe"]["schema"], "control_center.builder_placement_probe.v1")
        self.assertFalse(report["builder_placement_probe"]["runtime_mutation"])

    def test_cli_can_save_feasibility_report(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "feasibility.json"
            subprocess.run([
                sys.executable, "tools/report_gameplay_feasibility.py", "--builder-item-id", "1", "--output", str(output),
            ], cwd=Path(__file__).parents[1], capture_output=True, text=True, check=True)
            saved = json.loads(output.read_text())
            self.assertEqual(saved["schema"], "control_center.gameplay_feasibility.v1")


if __name__ == "__main__":
    unittest.main()
