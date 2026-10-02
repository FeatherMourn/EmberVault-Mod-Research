from pathlib import Path
from tools.verify_water_displacing_evidence import verify

ROOT=Path(__file__).resolve().parents[1]
BUILD="1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"
def test_water_displacing_runtime_evidence_is_valid():
    result=verify(ROOT/"research/probe_sessions/water_displacing_runtime_evidence_20260928.json",BUILD,"1.3")
    assert result["valid"],result["errors"]
