import json
from pathlib import Path
from tools.validate_world_generation_plan import validate
from tools.build_world_generation_plan import build

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "research/templates/world_generation_plan_template.json"

def test_template_is_a_valid_research_plan():
    result = validate(PLAN)
    assert result["valid"], result["errors"]

def test_validator_rejects_approved_operation(tmp_path):
    data = json.loads(PLAN.read_text(encoding="utf-8"))
    data["operations"] = [{"kind": "write-live-world", "approved": True}]
    path = tmp_path / "unsafe.json"; path.write_text(json.dumps(data), encoding="utf-8")
    result = validate(path)
    assert not result["valid"]

def test_generated_plan_is_pinned_and_safe():
    plan = build("1076226", "36234b22-85f2-4001-ac56-002b379d0d88", "Test plan")
    assert plan["game_build"] == "1076226"
    assert plan["donor_scene_guid"] == "36234b22-85f2-4001-ac56-002b379d0d88"
    assert validate_from_data(plan)["valid"]

def validate_from_data(data):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "plan.json"; path.write_text(json.dumps(data), encoding="utf-8")
        return validate(path, "1076226")
