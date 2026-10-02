"""Fail-closed verifier for a bounded FogVoxelMappingResource read."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def verify(path: Path, build: str, api: str) -> dict:
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.fog_voxel_mapping_runtime_evidence.v1": errors.append("unsupported evidence schema")
    if data.get("game_build") != build: errors.append("game build mismatch")
    if data.get("loader_api_version") != api: errors.append("loader API mismatch")
    if data.get("resource_type") != "keen::FogVoxelMappingResource" or data.get("part") != 0: errors.append("resource identity mismatch")
    if data.get("guid") != "36234b22-85f2-4001-ac56-002b379d0d88": errors.append("GUID mismatch")
    if data.get("read_only") is not True or data.get("bounded") is not True: errors.append("probe was not bounded and read-only")
    if data.get("resource_lookup") != {"ok": True, "found": True, "guid_matches": True}: errors.append("lookup mismatch")
    if data.get("payload_read") != {"ok": True, "data_type": "userdata"}: errors.append("payload read mismatch")
    if data.get("fields", {}).get("mapping_count") != 17: errors.append("mapping count mismatch")
    first = data.get("fields", {}).get("first", {})
    last = data.get("fields", {}).get("last", {})
    if first != {"type": "Gameplay", "level": 0, "min_x": 0, "max_z": 256}: errors.append("first mapping mismatch")
    if last != {"type": "Decorative", "level": 16}: errors.append("last mapping mismatch")
    if data.get("offline_runtime_parity") is not True: errors.append("offline/runtime parity missing")
    for field in ("voxel_content", "chunk_content", "created", "registered", "mutated", "attached", "world", "save"):
        if data.get("boundary", {}).get(field) is not False: errors.append(f"prohibited boundary crossed: {field}")
    if data.get("result") != "fog_voxel_mapping_payload_read_complete": errors.append("completion marker missing")
    if data.get("current_session_errors") != []: errors.append("current session contains errors")
    for field in ("game_stopped", "probe_uninstalled", "stable_profile_restored", "isolation_ready"):
        if data.get("cleanup", {}).get(field) is not True: errors.append(f"cleanup {field} is not verified")
    if data.get("promotion_ready") is not False or not data.get("limitations"): errors.append("research-only boundary missing")
    return {"schema": "control_center.fog_voxel_mapping_evidence_verification.v1", "valid": not errors, "state": "research-only", "promotion_ready": False, "errors": errors}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path); parser.add_argument("--expected-build", required=True); parser.add_argument("--expected-api", required=True)
    args = parser.parse_args(); result = verify(args.evidence, args.expected_build, args.expected_api); print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["valid"] else 1

if __name__ == "__main__": raise SystemExit(main())
