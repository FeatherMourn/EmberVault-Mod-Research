import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "research" / "probes" / "fog_voxel_mapping_single_donor_probe_36234b22_1076226"

def test_fog_mapping_probe_is_bounded_research_only():
    manifest = json.loads((PROBE / "mod.json").read_text(encoding="utf-8"))
    lua = (PROBE / "src" / "mod.lua").read_text(encoding="utf-8")
    assert manifest["feature_state"] == "research-only"
    assert manifest["research_only"] is True
    assert manifest["required_loader_api_version"] == "1.3"
    assert "keen::FogVoxelMappingResource" in lua
    assert "36234b22-85f2-4001-ac56-002b379d0d88" in lua
    assert "fog_voxel_mapping_payload_read_complete" in lua
    assert "resource.data" in lua
    assert "created=false" in lua
    assert "mutated=false" in lua
    assert "save=false" in lua
