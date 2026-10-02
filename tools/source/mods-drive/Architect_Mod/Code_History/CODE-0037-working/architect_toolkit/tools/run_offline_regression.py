"""One-command offline regression for Architect Toolkit research artifacts."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOXEL = ROOT / "tools" / "ArchitectVoxel"
STAGING = ROOT / "runtime" / "native" / "staging"
DEPLOYED = ROOT / "runtime" / "native" / "ArchitectNativeRuntime.dll"
MANIFEST = ROOT / "runtime" / "native" / "SHA256.txt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(label: str, command: list[str], env: dict[str, str] | None = None) -> None:
    print(f"[RUN] {label}")
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
    if result.returncode:
        print(result.stdout, end=""); print(result.stderr, end="", file=sys.stderr)
        raise RuntimeError(f"{label} failed ({result.returncode})")
    if result.stdout.strip(): print(result.stdout.strip())


def run_shell(label: str, command: str) -> None:
    print(f"[RUN] {label}")
    result = subprocess.run(command, cwd=ROOT, shell=True, text=True, capture_output=True)
    if result.returncode:
        print(result.stdout, end=""); print(result.stderr, end="", file=sys.stderr)
        raise RuntimeError(f"{label} failed ({result.returncode})")
    if result.stdout.strip(): print(result.stdout.strip())


def main() -> int:
    deployed_hash_at_start = sha256(DEPLOYED) if DEPLOYED.is_file() else None
    try:
        # Keep repository packages importable when this script is launched by
        # absolute path from a clean Python process.
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        env = dict(__import__("os").environ)
        env["PYTHONPATH"] = str(VOXEL) + ";" + env.get("PYTHONPATH", "")
        run("Python unit tests", [sys.executable, "-m", "unittest", "discover", "-s", str(VOXEL), "-p", "test_*.py"], env)
        run("ArchitectDataIndex tests", [sys.executable, "-m", "unittest", "discover",
             "-s", str(ROOT / "tools" / "ArchitectDataIndex" / "tests"), "-p", "test_*.py"], env)
        run("Structure Recorder tests", [sys.executable, "-m", "unittest", "discover",
             "-s", str(ROOT / "tools" / "StructureRecorder" / "tests"), "-p", "test_*.py"], env)
        run("Structure Editor tests", [sys.executable, "-m", "unittest", "discover",
             "-s", str(ROOT / "tools" / "StructureEditor" / "tests"), "-p", "test_*.py"], env)
        run("SemanticCaptureAnalyzer tests", [sys.executable, "-m", "unittest", "discover",
             "-s", str(ROOT / "tools" / "SemanticCaptureAnalyzer" / "tests"), "-p", "test_*.py"], env)
        run("ArchitectCore contract tests", [sys.executable, "-m", "unittest", "discover",
             "-s", str(ROOT / "tools" / "ArchitectCore" / "tests"), "-p", "test_*.py"], env)
        run("PlayerObserver scaffold tests", [sys.executable, "-m", "unittest", "discover",
             "-s", str(ROOT / "tools" / "PlayerObserver" / "tests"), "-p", "test_*.py"], env)
        run("Admin backend framework tests", [sys.executable, "-m", "unittest", "discover",
             "-s", str(ROOT / "tools" / "AdminConsole" / "tests"), "-p", "test_*.py"], env)
        run("Camera FOV discovery tests", [sys.executable, "-m", "unittest", "discover",
             "-s", str(ROOT / "tools" / "CameraFov" / "tests"), "-p", "test_*.py"], env)
        run("First reversible cheat sprint tests", [sys.executable, "-m", "unittest", "discover",
             "-s", str(ROOT / "tools" / "CheatSprint" / "tests"), "-p", "test_*.py"], env)
        run("Movement and stamina correlation tests", [sys.executable, "-m", "unittest", "discover",
             "-s", str(ROOT / "tools" / "CheatCorrelation" / "tests"), "-p", "test_*.py"], env)
        run("EntityInspector tests", [sys.executable, "-m", "unittest", "discover",
             "-s", str(ROOT / "tools" / "EntityInspector" / "tests"), "-p", "test_*.py"], env)
        run("Generate capability recommendation", [sys.executable, "-m", "tools.ArchitectCore.recommend",
             "--capability-map", str(ROOT / "bridge" / "vanilla_capability_map.json"),
             "--graph", str(ROOT / "bridge" / "feature_dependency_graph.json"),
             "--output", str(ROOT / "bridge" / "next_capability_recommendation.json")], env)
        powershell = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
        if powershell.exists():
            run("PowerShell syntax validation", [str(powershell), "-NoProfile", "-NonInteractive", "-Command",
                 "[scriptblock]::Create((Get-Content -LiteralPath 'runtime/ArchitectRuntime.ps1' -Raw)) | Out-Null"], env)
        run("Regenerate shape/chunk audits", [sys.executable, str(VOXEL / "generate_reports.py")], env)
        run("Build semantic building catalog", [sys.executable,
             str(ROOT / "tools" / "ArchitectDataIndex" / "build_catalog.py")], env)
        run("Build catalog relationship validation", [sys.executable,
             str(ROOT / "tools" / "ArchitectDataIndex" / "build_validation.py")], env)
        run("CreateBuildingItemAction static map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_create_building_item_static.py"),
             "--output", str(ROOT / "bridge" / "create_building_item_static_map.json")], env)
        run("ClientPlayerInput static map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_client_player_input_static.py"),
             "--output", str(ROOT / "bridge" / "client_player_input_static_map.json")], env)
        run("Semantic action dispatcher static map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_semantic_action_dispatcher_static.py"),
             "--output", str(ROOT / "bridge" / "semantic_action_dispatcher_static_map.json")], env)
        run("Building snap/transform static map", [sys.executable,
             str(ROOT / "tools" / "SemanticCaptureAnalyzer" / "scan_building_snap_static.py"),
             "--output", str(ROOT / "bridge" / "building_snap_static_map.json")], env)
        run("Snap candidate selection static map", [sys.executable,
             str(ROOT / "tools" / "SemanticCaptureAnalyzer" / "scan_snap_candidate_selection_static.py"),
             "--output", str(ROOT / "bridge" / "snap_candidate_selection_static_map.json")], env)
        run("Building commit transform static map", [sys.executable,
             str(ROOT / "tools" / "SemanticCaptureAnalyzer" / "scan_building_commit_transform_static.py"),
             "--output", str(ROOT / "bridge" / "building_commit_transform_static_map.json")], env)
        run("Blueprint selection authority CFG/slice tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_blueprint_selection_authority_static"], env)
        run("Blueprint selection authority static map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_blueprint_selection_authority_static.py"),
             "--output", str(ROOT / "bridge" / "blueprint_selection_authority_static_map.json"),
             "--doc", str(ROOT / "docs" / "research" / "BlueprintSelectionAuthority-StaticMap-v1.md")], env)
        run("Placement frame-input provenance CFG/dataflow tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_placement_frame_input_provenance_static"], env)
        run("Placement frame-input provenance static map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_placement_frame_input_provenance_static.py"),
             "--output", str(ROOT / "bridge" / "placement_frame_input_provenance_static_map.json"),
             "--doc", str(ROOT / "docs" / "research" / "PlacementFrameInputProvenance-StaticMap-v1.md")], env)
        run("Placement helper-buffer field provenance tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_placement_helper_buffer_field_provenance_static"], env)
        run("Placement helper-buffer field provenance static map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_placement_helper_buffer_field_provenance_static.py"),
             "--output", str(ROOT / "bridge" / "placement_helper_buffer_field_provenance_static_map.json"),
             "--doc", str(ROOT / "docs" / "research" / "PlacementHelperBufferFieldProvenance-StaticMap-v1.md")], env)
        run("Target resolver reflection candidates", [sys.executable, "-m", "tools.ArchitectCore.target_reflection",
             "--types", str(ROOT.parents[1] / ".cache" / "types.json"),
             "--output", str(ROOT / "bridge" / "target_resolver_reflection_candidates.json")], env)
        run("Entity Inspector static map", [sys.executable,
             str(ROOT / "tools" / "EntityInspector" / "analyze_entity_targeting.py")], env)
        run("Cursor target data-flow artifact tests", [sys.executable, "-m", "unittest",
             "tools.EntityInspector.tests.test_cursor_dataflow"], env)
        run("ECS registry consumer artifact tests", [sys.executable, "-m", "unittest",
             "tools.EntityInspector.tests.test_ecs_registry_consumers"], env)

        json_files = list((ROOT / "bridge").glob("*.json")) + list((ROOT / "tools").rglob("*.json")) + list(STAGING.glob("*.json"))
        # Windows PowerShell 5.1 emits a UTF-8 BOM for several bridge research
        # files; accept it while still applying strict JSON parsing.
        for path in json_files: json.loads(path.read_text(encoding="utf-8-sig"))
        print(f"[OK] strict JSON files={len(json_files)}")
        from tools.ArchitectCore.contracts import load_capability_map, validate_feature_graph
        capability_map = load_capability_map(ROOT / "bridge" / "vanilla_capability_map.json")
        feature_graph = json.loads((ROOT / "bridge" / "feature_dependency_graph.json").read_text(encoding="utf-8"))
        validate_feature_graph(feature_graph, capability_map)
        if json.loads((ROOT / "bridge" / "architect_engineering_state.json").read_text(encoding="utf-8"))["gameBuild"] != 1076226:
            raise RuntimeError("engineering state game build mismatch")
        print(f"[OK] ArchitectCore capability adapters={len(capability_map['adapters'])} features={len(feature_graph['features'])}")
        catalog = json.loads((ROOT / "bridge" / "build_catalog.json").read_text(encoding="utf-8"))
        snap_catalog = json.loads((ROOT / "bridge" / "snap_rule_catalog.json").read_text(encoding="utf-8"))
        validation = json.loads((ROOT / "bridge" / "build_catalog_validation.json").read_text(encoding="utf-8"))
        if catalog.get("backendStatus") != "read_only_catalog" or not catalog.get("generatedAtUtc"):
            raise RuntimeError("building catalog is not read-only")
        if not any(int(row.get("itemId", 0)) == 81726253 and row.get("classification") == "Voxel Blueprint" for row in catalog.get("items", [])):
            raise RuntimeError("known Ceiling blueprint missing from catalog")
        if snap_catalog.get("status") not in {"UNAVAILABLE", "AVAILABLE_PARTIAL", "AVAILABLE"}:
            raise RuntimeError("invalid snap catalog status")
        if snap_catalog.get("itemToFamilyLink", {}).get("status") not in {"UNAVAILABLE", "AVAILABLE_PARTIAL"}:
            raise RuntimeError("snap item-to-family linkage status missing")
        if validation.get("gameBuild", {}).get("sourceBundleSha256") != "153BE9AF6875DB39594FDCAC7A08EE8B316C802BE8A426D24F0A9DFAE713C474":
            raise RuntimeError("KFC source bundle provenance missing or mismatched")
        if validation.get("gameBuild", {}).get("databaseSchemaVersion") != 2:
            raise RuntimeError("expanded KFC index schema is not active")
        if validation.get("blueprintCompressionValidation", {}).get("invalid", 0) != 0:
            raise RuntimeError("invalid compressed blueprint sizes detected")
        if snap_catalog.get("status") == "AVAILABLE" and snap_catalog.get("configurationCount", 0) == 0:
            raise RuntimeError("snap catalog claims AVAILABLE without configurations")
        print(f"[OK] semantic building catalog items={len(catalog.get('items', []))} snapStatus={snap_catalog.get('status')}")
        static_map = json.loads((ROOT / "bridge" / "create_building_item_static_map.json").read_text(encoding="utf-8"))
        if not static_map["executable"]["fingerprintMatches"]:
            raise RuntimeError("CreateBuildingItemAction static map fingerprint mismatch")
        if static_map["observerDecision"]["install"]:
            raise RuntimeError("unproven CreateBuildingItemAction observer was enabled")
        if static_map["staticConclusion"]["status"] != "UNSOLVED":
            raise RuntimeError("static action status unexpectedly promoted")
        print("[OK] CreateBuildingItemAction remains disabled/fail-closed")
        input_map = json.loads((ROOT / "bridge" / "client_player_input_static_map.json").read_text(encoding="utf-8"))
        if not input_map["build"]["fingerprintMatches"]:
            raise RuntimeError("ClientPlayerInput static map fingerprint mismatch")
        if input_map["candidateClientPlayerInput"]["observerInstall"]:
            raise RuntimeError("ClientPlayerInput observer was unexpectedly enabled")
        if input_map["statusModel"]["ClientPlayerInput_live_identity"] != "UNSOLVED":
            raise RuntimeError("ClientPlayerInput live identity unexpectedly promoted")
        print("[OK] ClientPlayerInput remains static-only/fail-closed")
        dispatcher_map = json.loads((ROOT / "bridge" / "semantic_action_dispatcher_static_map.json").read_text(encoding="utf-8"))
        if not dispatcher_map["build"]["fingerprintMatches"]:
            raise RuntimeError("dispatcher static map fingerprint mismatch")
        if dispatcher_map["observerDecision"]["install"]:
            raise RuntimeError("dispatcher action observer was unexpectedly enabled")
        if dispatcher_map["consumedVersionCluster"]["sameBaseHasAllThreeOffsets"]:
            raise RuntimeError("unproven consumed-version cluster unexpectedly promoted")
        print("[OK] dispatcher family remains static-only/fail-closed")
        snap_static = json.loads((ROOT / "bridge" / "building_snap_static_map.json").read_text(encoding="utf-8"))
        if not snap_static["executable"]["fingerprintMatches"]:
            raise RuntimeError("building snap static map fingerprint mismatch")
        if snap_static["observerDecision"]["install"] or snap_static["safety"]["hooksInstalled"]:
            raise RuntimeError("building snap observer unexpectedly enabled")
        if snap_static["observerDecision"]["status"] != "FAIL_CLOSED_STATIC_ONLY":
            raise RuntimeError("building snap observer is not fail-closed")
        print("[OK] Building snap static map remains offline/fail-closed")
        selection_static = json.loads((ROOT / "bridge" / "snap_candidate_selection_static_map.json").read_text(encoding="utf-8"))
        if not selection_static["executable"]["fingerprintMatches"]:
            raise RuntimeError("snap candidate selection map fingerprint mismatch")
        if selection_static["observerDecision"]["install"] or selection_static["safety"]["hooksInstalled"]:
            raise RuntimeError("snap candidate observer unexpectedly enabled")
        accepted = selection_static["candidateFilter"]["acceptedCollection"]
        if accepted["status"] != "PROVEN_STATIC_BUILD_1076226" or selection_static["candidateFilter"]["outputRecordStride"] != "0x50":
            raise RuntimeError("accepted candidate collection evidence missing")
        if len(selection_static.get("callers", {})) < 4:
            raise RuntimeError("candidate filter caller set incomplete")
        print("[OK] snap candidate selection remains static-only/fail-closed")
        commit_static = json.loads((ROOT / "bridge" / "building_commit_transform_static_map.json").read_text(encoding="utf-8"))
        if not commit_static["executable"]["fingerprintMatches"]:
            raise RuntimeError("building commit transform map fingerprint mismatch")
        if commit_static["observerDecision"]["install"] or commit_static["safety"]["hooksInstalled"]:
            raise RuntimeError("building commit observer unexpectedly enabled")
        required_event_fields = {"position", "orientation", "volumeMin", "volumeMax", "material", "trackingItemId", "ownerId"}
        if set(commit_static["eventFieldFlow"]) != required_event_fields | {"eventHelper"}:
            raise RuntimeError("building commit event field map incomplete")
        if commit_static["registerProvenance"]["R15"]["status"] != "PROVEN":
            raise RuntimeError("R15 provenance evidence missing")
        print("[OK] building commit transform map remains static-only/fail-closed")
        authority = json.loads((ROOT / "bridge" / "blueprint_selection_authority_static_map.json").read_text(encoding="utf-8"))
        if not authority.get("build", {}).get("fingerprintMatches") or authority.get("build", {}).get("sha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781":
            raise RuntimeError("blueprint-selection executable fingerprint mismatch")
        if authority.get("analysisMode") != "OFFLINE_STATIC_ONLY":
            raise RuntimeError("blueprint-selection map is not offline-only")
        if authority.get("safety", {}).get("runtimeHooksInstalled") or authority.get("safety", {}).get("writesGameMemory"):
            raise RuntimeError("blueprint-selection map claims runtime hook or game write")
        if authority.get("observerDecision", {}).get("install") is not False:
            raise RuntimeError("blueprint-selection observer unexpectedly enabled")
        backward = authority.get("placementBackwardSlice", {})
        if backward.get("startCallRva") != "0x280F86" or backward.get("targetFunctionRva") != "0x3E2CD0":
            raise RuntimeError("blueprint-selection placement anchors changed")
        if not any(row.get("instructionRva") == "0x280F75" and row.get("destinationExpression", "").startswith("R8D") for row in backward.get("steps", [])):
            raise RuntimeError("placement R8D load evidence missing")
        if authority.get("knownEvidenceImported", {}).get("placementLateEventGeometryAuthority") != "DISPROVEN_BUILD_1076226":
            raise RuntimeError("late BuildingPlaceEvent geometry-authority negative result was reclassified")
        if any(row.get("hookEligible") for row in authority.get("rejectedHookSites", [])):
            raise RuntimeError("a rejected hook site was marked eligible")
        convergence = authority.get("convergence", {})
        if not convergence.get("commonOwnerProven") and convergence.get("status") not in {"UNSOLVED", "PARTIAL_STATIC"}:
            raise RuntimeError("unproven convergence was silently promoted")
        if convergence.get("status") == "PROVEN_STATIC_BUILD_1076226":
            concrete = [step for step in backward.get("steps", []) if step.get("instructionRva")]
            if not concrete or any(not step.get("bytes") for step in concrete):
                raise RuntimeError("promoted convergence lacks concrete instruction evidence")
        snap_callers = authority.get("snapPreviewWriteback", {}).get("callers", {})
        if set(snap_callers) != {"0x3E377D", "0x3E4347", "0x3E6C9C", "0x3EB297"}:
            raise RuntimeError("snap caller-specific frontiers are incomplete")
        print(f"[OK] blueprint selection authority remains {convergence.get('status')}/fail-closed")
        frame_map = json.loads((ROOT / "bridge" / "placement_frame_input_provenance_static_map.json").read_text(encoding="utf-8"))
        frame_parent = frame_map.get("parentEvidence", {})
        if frame_map.get("analysisMode") != "OFFLINE_STATIC_ONLY":
            raise RuntimeError("placement frame-input map is not offline-only")
        if frame_parent.get("delivery") != "CODE-0001" or frame_parent.get("status") != "PARTIAL_STATIC" or not frame_parent.get("mapFingerprintMatches"):
            raise RuntimeError("CODE-0002 parent evidence is missing/divergent")
        if not frame_map.get("build", {}).get("fingerprintMatches") or frame_map["build"].get("sha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781":
            raise RuntimeError("placement frame-input executable fingerprint mismatch")
        frame_safety = frame_map.get("safety", {})
        if frame_safety.get("runtimeHooksInstalled") is not False or frame_safety.get("writesGameMemory") is not False or frame_safety.get("writesExecutable") is not False:
            raise RuntimeError("CODE-0002 safety gate claims a runtime hook or mutation")
        if frame_map.get("observerDecision", {}).get("install") is not False:
            raise RuntimeError("CODE-0002 observer install gate was enabled")
        expected_anchors = {
            "resolverCallRva": "0x28089E", "resolverTargetRva": "0xCB4B50",
            "itemLoadRva": "0x280F75", "placementCallRva": "0x280F86",
            "placementTargetRva": "0x3E2CD0",
        }
        if frame_map.get("anchor") != expected_anchors:
            raise RuntimeError("CODE-0002 required static anchors changed")
        for slot_name in ("rbp08Provenance", "rbp48Provenance"):
            slot = frame_map.get(slot_name, {})
            candidates = slot.get("reachingDefinitions", [])
            if len(candidates) > 1 and slot.get("status") == "PROVEN_STATIC":
                raise RuntimeError(f"ambiguous {slot_name} definitions were promoted to PROVEN_STATIC")
            if slot.get("status") == "PROVEN_STATIC" and (
                len(candidates) != 1 or candidates[0].get("evidenceStatus") != "PROVEN_STATIC"
            ):
                raise RuntimeError(f"{slot_name} claims PROVEN_STATIC without one concrete field definition")
            for event in slot.get("reachingDefinitions", []):
                if not event.get("instructionRva") or not event.get("bytes") or not event.get("basicBlock"):
                    raise RuntimeError(f"{slot_name} reaching definition lacks instruction/CFG evidence")
        for name, claim in frame_map.get("crossSystemCorrelation", {}).items():
            status = str(claim.get("status", ""))
            pointer_identity = str(claim.get("pointerIdentity", ""))
            nested_proof = any(isinstance(value, str) and value.startswith("PROVEN_STATIC")
                               for value in claim.values())
            if status.startswith("PROVEN_STATIC") or pointer_identity.startswith("PROVEN_STATIC") or nested_proof:
                evidence = claim.get("connectingInstructions", [])
                if not evidence or any(not row.get("instructionRva") or not row.get("instruction") or not row.get("bytes") for row in evidence):
                    raise RuntimeError(f"cross-system claim {name} lacks concrete instruction-level connection evidence")
        if frame_map.get("convergenceDelta", {}).get("status") == "PROVEN_STATIC_BUILD_1076226":
            delta = frame_map["convergenceDelta"]
            if not all(delta.get(key) is True for key in ("rbp08OwnerProven", "rbp48OwnerProven", "commonOwnerProven")):
                raise RuntimeError("CODE-0002 convergence promotion lacks both owner chains")
            if not frame_map["convergenceDelta"].get("evidence"):
                raise RuntimeError("CODE-0002 convergence promotion lacks evidence rows")
        if any(row.get("hookEligible") for row in authority.get("rejectedHookSites", [])):
            raise RuntimeError("CODE-0002 reclassified a rejected hook site as eligible")
        print(f"[OK] placement frame-input map remains {frame_map['convergenceDelta']['status']}/offline/fail-closed")
        helper_map = json.loads((ROOT / "bridge" / "placement_helper_buffer_field_provenance_static_map.json").read_text(encoding="utf-8"))
        if helper_map.get("analysisMode") != "OFFLINE_STATIC_ONLY" or helper_map.get("parentEvidence", {}).get("status") != "PARTIAL_STATIC":
            raise RuntimeError("CODE-0003 helper map parent/mode gate failed")
        if helper_map.get("build", {}).get("sha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781" or not helper_map.get("build", {}).get("fingerprintMatches"):
            raise RuntimeError("CODE-0003 executable fingerprint mismatch")
        safety = helper_map.get("safety", {})
        if safety.get("runtimeHooksInstalled") is not False or safety.get("writesGameMemory") is not False or safety.get("writesExecutable") is not False:
            raise RuntimeError("CODE-0003 safety claims a hook or write")
        if helper_map.get("observerDecision", {}).get("install") is not False:
            raise RuntimeError("CODE-0003 observer install gate was enabled")
        anchors = helper_map.get("parentAnchors", {})
        expected = {"logicalFunctionStartRva": "0x280790", "logicalFunctionEndRva": "0x2810E8",
                    "resolverCallRva": "0x28089E", "resolverTargetRva": "0xCB4B50",
                    "itemLoadRva": "0x280F75", "placementCallRva": "0x280F86",
                    "placementTargetRva": "0x3E2CD0", "localBufferField38": "0x38", "localBufferField78": "0x78"}
        if anchors != expected:
            raise RuntimeError("CODE-0003 anchors changed")
        callsites = helper_map.get("helperCallsites", [])
        decoded = {(row.get("callsiteRva"), row.get("targetRva")) for row in callsites}
        if decoded != {("0x2807B6", "0x8DA7C0"), ("0x2807C8", "0x8D5CA0"), ("0x2810A3", "0x8D5CA0")}:
            raise RuntimeError("CODE-0003 helper callsite mapping incomplete")
        for helper_rva, helper in helper_map.get("helpers", {}).items():
            if helper.get("outputBufferArgument", {}).get("status") != "PROVEN_STATIC":
                raise RuntimeError(f"CODE-0003 output alias not proven for {helper_rva}")
            for write in helper.get("writes", []):
                if write.get("evidenceStatus") == "PROVEN_STATIC":
                    if not write.get("instructionRva") or not write.get("bytes") or not write.get("destinationRange") or not write.get("writeWidth"):
                        raise RuntimeError(f"CODE-0003 fixed writer evidence incomplete for {helper_rva}")
                if write.get("evidenceStatus") == "UNSOLVED_DYNAMIC_DESTINATION" and write.get("overlapsTarget38") is True:
                    raise RuntimeError("CODE-0003 dynamic write was promoted as exact field overlap")
            for nested in helper.get("nestedDirectCallees", []):
                if nested.get("fieldWriterFollowed"):
                    if not nested.get("directCallEvidence") or not nested.get("outputPointerArguments"):
                        raise RuntimeError(f"CODE-0003 nested writer lacks call/argument evidence for {helper_rva}")
        for field in ("field38", "field78"):
            data = helper_map.get(field, {})
            if data.get("lastProvenWriter") is not None and len(data.get("reachingWrites", [])) != 1:
                raise RuntimeError(f"CODE-0003 non-unique {field} last writer")
            if data.get("status") == "PROVEN_STATIC_BUILD_1076226" and not data.get("sourceProvenance"):
                raise RuntimeError(f"CODE-0003 {field} source proof missing")
        if helper_map.get("convergenceDelta", {}).get("status") == "PROVEN_STATIC_BUILD_1076226":
            raise RuntimeError("CODE-0003 unexpectedly promoted common-owner convergence")
        if any(row.get("hookEligible") for row in authority.get("rejectedHookSites", [])):
            raise RuntimeError("CODE-0003 marked a rejected hook eligible")
        print(f"[OK] placement helper-buffer map remains {helper_map['convergenceDelta']['status']}/offline/fail-closed")
        run("Placement computed-destination arithmetic tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_placement_computed_destination_arithmetic_static"], env)
        run("Placement computed-destination arithmetic static map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_placement_computed_destination_arithmetic_static.py"),
             "--output", str(ROOT / "bridge" / "placement_computed_destination_arithmetic_static_map.json"),
             "--doc", str(ROOT / "docs" / "research" / "PlacementComputedDestinationArithmetic-StaticMap-v1.md")], env)
        computed_map = json.loads((ROOT / "bridge" / "placement_computed_destination_arithmetic_static_map.json").read_text(encoding="utf-8"))
        if computed_map.get("analysisMode") != "OFFLINE_STATIC_ONLY":
            raise RuntimeError("CODE-0004 map is not offline-only")
        if computed_map.get("build", {}).get("sha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781" or not computed_map.get("build", {}).get("fingerprintMatches"):
            raise RuntimeError("CODE-0004 executable fingerprint mismatch")
        csafety = computed_map.get("safety", {})
        if any(csafety.get(k) for k in ("processAccess", "debugApis", "writesExecutable", "writesGameMemory", "runtimeHooksInstalled")):
            raise RuntimeError("CODE-0004 safety gate claims process/debug/write/hook access")
        if computed_map.get("observerDecision", {}).get("install") is not False:
            raise RuntimeError("CODE-0004 observer install gate was enabled")
        if computed_map.get("parentEvidence", {}).get("status") != "PARTIAL_STATIC":
            raise RuntimeError("CODE-0004 parent status changed")
        expected_writes = {"0x8D5D35", "0x8D5D77", "0x8D5DA3", "0x8D5DCC", "0x8D5DF7", "0x8D5E25", "0x8D5E46"}
        writes = computed_map.get("helper8D5CA0", {}).get("writes", [])
        if {row.get("rva") for row in writes} != expected_writes:
            raise RuntimeError("CODE-0004 seven primary write anchors changed")
        if computed_map.get("helper8DA7C0", {}).get("computedDestination8DA992", {}).get("rva") != "0x8DA992":
            raise RuntimeError("CODE-0004 0x8DA992 anchor missing")
        for field in ("field38", "field78"):
            target = computed_map.get("targets", {}).get(field, {})
            if target.get("readWidth") != 8 or target.get("byteRange") not in ([56, 64], [120, 128]):
                raise RuntimeError(f"CODE-0004 {field} target byte range not decoded")
        for row in writes:
            for field in ("target38", "target78"):
                claim = row.get(field, {})
                if claim.get("classification") == "CANNOT_HIT_TARGET" and not claim.get("proof"):
                    raise RuntimeError(f"CODE-0004 {row.get('rva')} missing cannot-hit proof")
                if claim.get("classification") == "CAN_HIT_TARGET" and not claim.get("witnesses"):
                    raise RuntimeError(f"CODE-0004 {row.get('rva')} missing hit witness")
                if claim.get("classification") == "UNRESOLVED" and not claim.get("proof"):
                    raise RuntimeError(f"CODE-0004 {row.get('rva')} unresolved without boundary")
        if computed_map.get("field38Delta", {}).get("lastProvenWriter") is not None or computed_map.get("field78Delta", {}).get("lastProvenWriter") is not None:
            raise RuntimeError("CODE-0004 promoted a last writer from reachability alone")
        if computed_map.get("convergenceDelta", {}).get("status") not in {"UNSOLVED", "PARTIAL_STATIC"}:
            raise RuntimeError("CODE-0004 convergence was silently promoted")
        print(f"[OK] placement computed-destination map remains {computed_map['convergenceDelta']['status']}/offline/fail-closed")
        run("CODE-0005 observer-site qualification tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_placement_helper_observer_site_qualification_static"], env)
        run("CODE-0005 observer-site qualification map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_placement_helper_observer_site_qualification_static.py"),
             "--output", str(ROOT / "bridge" / "placement_helper_observer_site_qualification_static_map.json"),
             "--doc", str(ROOT / "docs" / "research" / "PlacementHelperObserverSiteQualification-StaticMap-v1.md")], env)
        site_map = json.loads((ROOT / "bridge" / "placement_helper_observer_site_qualification_static_map.json").read_text(encoding="utf-8"))
        if site_map.get("analysisMode") != "OFFLINE_STATIC_ONLY" or not site_map.get("build", {}).get("fingerprintMatches"):
            raise RuntimeError("CODE-0005 site qualifier fingerprint/mode gate failed")
        if site_map.get("selectedDesign", {}).get("status") not in {"NO_SAFE_OBSERVER_SITE", "PARTIAL_STATIC", "QUALIFIED_SAFE_OBSERVER_SITE"}:
            raise RuntimeError("CODE-0005 invalid site qualification status")
        if site_map.get("observerDecision", {}).get("installNow") is not False:
            raise RuntimeError("CODE-0005 observer installNow was enabled")
        eligible = site_map.get("selectedDesign", {}).get("status") == "QUALIFIED_SAFE_OBSERVER_SITE"
        if site_map.get("observerDecision", {}).get("stagingBuildEligible") != eligible:
            raise RuntimeError("CODE-0005 staging eligibility does not follow qualification")
        if any(row.get("hookEligible") for row in site_map.get("knownRejectedSites", [])):
            raise RuntimeError("CODE-0005 historical rejected site became eligible")
        if site_map.get("selectedDesign", {}).get("status") == "NO_SAFE_OBSERVER_SITE" and site_map.get("candidateSites", []) and not all(row.get("status") == "NOT_QUALIFIED" for row in site_map["candidateSites"]):
            raise RuntimeError("CODE-0005 no-safe result contains an unqualified candidate")
        ssafety = site_map.get("safety", {})
        if any(ssafety.get(k) for k in ("gameStateWrites", "argumentSubstitution", "returnValueSubstitution", "controlFlowMutation", "fileIoInHook", "heapAllocationInHook", "blockingInHook")):
            raise RuntimeError("CODE-0005 safety map claims an unsafe operation")
        print(f"[OK] CODE-0005 site qualification={site_map['selectedDesign']['status']}; no runtime observer installed")
        run("CODE-0005A relocation planner tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_observer_relocation_plan"], env)
        run("CODE-0005A capability/requalification artifacts", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "generate_observer_trampoline_capability.py"),
             "--output", str(ROOT / "bridge" / "observer_trampoline_capability_map.json"),
             "--delta", str(ROOT / "bridge" / "placement_helper_observer_site_requalification_code0005a.json")], env)
        capability = json.loads((ROOT / "bridge" / "observer_trampoline_capability_map.json").read_text(encoding="utf-8"))
        requal = json.loads((ROOT / "bridge" / "placement_helper_observer_site_requalification_code0005a.json").read_text(encoding="utf-8"))
        if capability.get("codeId") != "CODE-0005A" or capability.get("analysisMode") != "OFFLINE_AND_NATIVE_HARNESS":
            raise RuntimeError("CODE-0005A capability identity/mode invalid")
        if capability.get("parentEvidence", {}).get("result") != "NO_SAFE_OBSERVER_SITE":
            raise RuntimeError("CODE-0005A parent gate changed")
        if capability.get("runtimeEligibility", {}).get("gameHookInstallAuthorized") is not False:
            raise RuntimeError("CODE-0005A game hook authorization was enabled")
        if capability.get("runtimeEligibility", {}).get("infrastructureReadyForSiteRequalification") is not False:
            raise RuntimeError("CODE-0005A infrastructure was promoted without ABI/drain proof")
        if requal.get("result") != "NO_SAFE_OBSERVER_SITE" or requal.get("observerDecision", {}).get("installNow") is not False:
            raise RuntimeError("CODE-0005A requalification promoted a site")
        for cls in ("RIP_RELATIVE", "RELATIVE_CALL", "RELATIVE_JMP", "RELATIVE_JCC"):
            if not any(x.get("class") == cls and x.get("status") == "UNSUPPORTED_FAIL_CLOSED" for x in capability.get("trampoline", {}).get("unsupportedRelocations", [])):
                raise RuntimeError(f"CODE-0005A missing fail-closed relocation class {cls}")
        print("[OK] CODE-0005A capability remains partial/offline/fail-closed")
        run("CODE-0005B helper contract tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_helper_8d5ca0_site_contract_static"], env)
        run("CODE-0005B helper contract static map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_helper_8d5ca0_site_contract_static.py"),
             "--output", str(ROOT / "bridge" / "helper_8d5ca0_site_contract_static_map.json"),
             "--delta", str(ROOT / "bridge" / "placement_helper_observer_site_requalification_code0005b.json")], env)
        helper_b = json.loads((ROOT / "bridge" / "helper_8d5ca0_site_contract_static_map.json").read_text(encoding="utf-8"))
        helper_delta = json.loads((ROOT / "bridge" / "placement_helper_observer_site_requalification_code0005b.json").read_text(encoding="utf-8"))
        if helper_b.get("build", {}).get("exeSha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781":
            raise RuntimeError("CODE-0005B executable fingerprint mismatch")
        if helper_b.get("site", {}).get("rva") != "0x8D5CA0" or helper_b.get("siteEligibility", {}).get("installNow") is not False or helper_b.get("siteEligibility", {}).get("gameHookInstallAuthorized") is not False:
            raise RuntimeError("CODE-0005B site gate invalid")
        if helper_b.get("siteEligibility", {}).get("status") not in {"PARTIAL_STATIC", "NOT_QUALIFIED"}:
            raise RuntimeError("CODE-0005B unexpectedly promoted site")
        if helper_delta.get("observerDecision", {}).get("installNow") is not False:
            raise RuntimeError("CODE-0005B delta authorized installation")
        print(f"[OK] CODE-0005B site contract={helper_b['siteEligibility']['status']}; install disabled")
        run("CODE-0005C parent relay static tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_parent_call_relay_correlation_static"], env)
        run("CODE-0005C parent relay static map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_parent_call_relay_correlation_static.py"),
             "--output", str(ROOT / "bridge" / "parent_call_relay_correlation_static_map.json")], env)
        relay_map = json.loads((ROOT / "bridge" / "parent_call_relay_correlation_static_map.json").read_text(encoding="utf-8"))
        if relay_map.get("site", {}).get("originalBytes") != "E8 D3 54 65 00" or not relay_map.get("site", {}).get("targetMatchesExpected"):
            raise RuntimeError("CODE-0005C parent CALL/target verification failed")
        if relay_map.get("relay", {}).get("callsFromRelay") is not False or relay_map.get("relay", {}).get("modifiesReturnAddress") is not False:
            raise RuntimeError("CODE-0005C relay contract permits CALL/return rewrite")
        if relay_map.get("correlation", {}).get("status") != "CORRELATION_UNPROVEN" or relay_map.get("runtimeEligibility", {}).get("gameHookInstallAuthorized") is not False:
            raise RuntimeError("CODE-0005C correlation/authorization gate invalid")
        relay_asm = STAGING / "ArchitectParentCallRelay.asm"
        relay_harness = STAGING / "ArchitectParentCallRelayHarness.c"
        for source in (relay_asm, relay_harness):
            if not source.is_file(): raise RuntimeError(f"CODE-0005C staging source missing: {source.name}")
            if re.search(r"\b(OpenProcess|ReadProcessMemory|WriteProcessMemory|CreateRemoteThread|DebugActiveProcess)\b", source.read_text(encoding="utf-8")):
                raise RuntimeError(f"CODE-0005C staging source contains forbidden process API: {source.name}")
        asm_hot = relay_asm.read_text(encoding="utf-8").split("synthetic_call_entry PROC", 1)[0]
        asm_hot = "\n".join(line.split(";", 1)[0] for line in asm_hot.splitlines())
        if re.search(r"\b(call|push|pop)\b", asm_hot, flags=re.IGNORECASE):
            raise RuntimeError("CODE-0005C relay hot path contains CALL or stack instruction")
        print("[OK] CODE-0005C relay source is synthetic-only and stack/call-free")
        run("CODE-0005D parent-frame correlation tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_parent_frame_lifetime_correlation_static"], env)
        run("CODE-0005D parent-frame correlation map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_parent_frame_lifetime_correlation_static.py"),
             "--output", str(ROOT / "bridge" / "parent_frame_lifetime_correlation_static_map.json")], env)
        frame_map = json.loads((ROOT / "bridge" / "parent_frame_lifetime_correlation_static_map.json").read_text(encoding="utf-8"))
        if frame_map.get("build", {}).get("exeSha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781":
            raise RuntimeError("CODE-0005D executable fingerprint mismatch")
        if frame_map.get("siteEligibility", {}).get("status") not in {"PARTIAL_STATIC", "NOT_QUALIFIED"}:
            raise RuntimeError("CODE-0005D unexpectedly promoted site")
        if frame_map.get("siteEligibility", {}).get("installNow") is not False or frame_map.get("siteEligibility", {}).get("gameHookInstallAuthorized") is not False:
            raise RuntimeError("CODE-0005D installation gate invalid")
        if frame_map.get("producerModel", {}).get("spscCompatibility") != "UNPROVEN":
            raise RuntimeError("CODE-0005D promoted SPSC compatibility")
        print(f"[OK] CODE-0005D frame correlation={frame_map['correlationGate']['status']}; install disabled")
        run("CODE-0005E relay safety tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_relay_safety_closure"], env)
        run("CODE-0005E relay safety map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_parent_relay_safety_closure_static.py"),
             "--output", str(ROOT / "bridge" / "parent_relay_safety_closure_static_map.json")], env)
        safety_map = json.loads((ROOT / "bridge" / "parent_relay_safety_closure_static_map.json").read_text(encoding="utf-8"))
        if safety_map.get("build", {}).get("exeSha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781":
            raise RuntimeError("CODE-0005E executable fingerprint mismatch")
        if safety_map.get("publication", {}).get("slotCount") not in (8, 16):
            raise RuntimeError("CODE-0005E slot bound invalid")
        if safety_map.get("runtimeEligibility", {}).get("installNow") is not False or safety_map.get("runtimeEligibility", {}).get("gameHookInstallAuthorized") is not False:
            raise RuntimeError("CODE-0005E authorization gate invalid")
        if safety_map.get("runtimeEligibility", {}).get("status") != "PARTIAL_STATIC_OR_HARNESS":
            raise RuntimeError("CODE-0005E unexpectedly promoted")
        print("[OK] CODE-0005E publication/matcher remain bounded and fail-closed")
        run("CODE-0006 snap winner static tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_snap_winner_preview_writeback_static"], env)
        run("CODE-0006 snap winner static map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_snap_winner_preview_writeback_static.py"),
             "--output", str(ROOT / "bridge" / "snap_winner_preview_writeback_static_map.json")], env)
        snap_winner = json.loads((ROOT / "bridge" / "snap_winner_preview_writeback_static_map.json").read_text(encoding="utf-8"))
        if snap_winner.get("build", {}).get("exeSha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781":
            raise RuntimeError("CODE-0006 executable fingerprint mismatch")
        if snap_winner.get("winnerSelection", {}).get("status") != "NO_WINNER_SELECTION_IN_BOUNDED_PATH":
            raise RuntimeError("CODE-0006 promoted an unsupported winner claim")
        if snap_winner.get("observerEligibility", {}).get("installNow") is not False or snap_winner.get("observerEligibility", {}).get("gameHookInstallAuthorized") is not False:
            raise RuntimeError("CODE-0006 observer authorization gate invalid")
        if snap_winner.get("installNow") is not False or snap_winner.get("gameHookInstallAuthorized") is not False or snap_winner.get("currentSourceDesignationAuthorized") is not False:
            raise RuntimeError("CODE-0006 top-level authorization gate invalid")
        if snap_winner.get("analysisResult") not in ("PARTIAL_STATIC", "NOT_PREVIEW_PATH", "PREVIEW_WRITEBACK_PROVEN_STATIC"):
            raise RuntimeError("CODE-0006 result classification missing")
        print("[OK] CODE-0006 winner/preview authority remains unresolved and static-only")
        run("CODE-0007 returned-pointer ownership tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_preview_write_destination_owner_static"], env)
        run("CODE-0007 returned-pointer ownership map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_preview_write_destination_owner_static.py"),
             "--output", str(ROOT / "bridge" / "preview_write_destination_owner_static_map.json")], env)
        owner_map = json.loads((ROOT / "bridge" / "preview_write_destination_owner_static_map.json").read_text(encoding="utf-8"))
        if owner_map.get("build", {}).get("exeSha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781":
            raise RuntimeError("CODE-0007 executable fingerprint mismatch")
        if not any(x.get("callRva") == "0x3E5578" and x.get("targetRva") == "0x3ED1A0" for x in owner_map.get("functions", {}).get("0x3ED1A0", {}).get("directCallers", [])):
            raise RuntimeError("CODE-0007 expected 0x3ED1A0 call contract missing")
        if owner_map.get("returnedPointerSource", {}).get("classification") != "OWNER_ROOTED_CONTAINER_SLOT":
            raise RuntimeError("CODE-0007 returned-pointer classification changed")
        if owner_map.get("lifetime", {}).get("classification") != "PERSISTENCE_UNRESOLVED":
            raise RuntimeError("CODE-0007 unresolved lifetime was promoted")
        if owner_map.get("anchoredReadersWriters", {}).get("connectedReaders"):
            raise RuntimeError("CODE-0007 claimed an unreviewed connected reader")
        if owner_map.get("observerEligibility", {}).get("installNow") is not False or owner_map.get("observerEligibility", {}).get("gameHookInstallAuthorized") is not False:
            raise RuntimeError("CODE-0007 observer authorization gate invalid")
        print("[OK] CODE-0007 owner/lifetime remains static-only and unresolved")
        run("CODE-0008 owner-rooted container tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_owner_rooted_container_family_static"], env)
        run("CODE-0008 owner-rooted container map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_owner_rooted_container_family_static.py"),
             "--output", str(ROOT / "bridge" / "owner_rooted_container_family_static_map.json")], env)
        container_map = json.loads((ROOT / "bridge" / "owner_rooted_container_family_static_map.json").read_text(encoding="utf-8"))
        if container_map.get("build", {}).get("exeSha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781":
            raise RuntimeError("CODE-0008 executable fingerprint mismatch")
        if [x.get("callRva") for x in container_map.get("argumentContracts", [])] != ["0x3E262B", "0x3E2919", "0x3E52BD", "0x3E5578"]:
            raise RuntimeError("CODE-0008 direct resolver call set changed")
        if container_map.get("allocator7AEDA0", {}).get("classification") != "FREE_LIST_REUSE_OR_BOUNDED_APPEND":
            raise RuntimeError("CODE-0008 allocator classification changed")
        if container_map.get("lifetime", {}).get("classification") != "PERSISTENCE_UNRESOLVED":
            raise RuntimeError("CODE-0008 unresolved lifetime was promoted")
        if container_map.get("anchoredReadersWriters", {}).get("previewOrCommitReaders"):
            raise RuntimeError("CODE-0008 claimed an unreviewed preview/commit reader")
        if container_map.get("observerDecision", {}).get("installNow") is not False or container_map.get("observerDecision", {}).get("gameHookInstallAuthorized") is not False:
            raise RuntimeError("CODE-0008 observer authorization gate invalid")
        if container_map.get("analysisResult") not in ("PARTIAL_STATIC", "GENERIC_CONTAINER_FAMILY_PROVEN_STATIC", "PLACEMENT_CONTAINER_FAMILY_PROVEN_STATIC", "PREVIEW_OWNER_CONVERGENCE_PROVEN_STATIC"):
            raise RuntimeError("CODE-0008 result classification missing")
        print("[OK] CODE-0008 owner-rooted container remains static-only and unresolved")
        run("CODE-0009 owner-rooted slot dispatch tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_owner_rooted_slot_dispatch_static"], env)
        run("CODE-0009 owner-rooted slot dispatch map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_owner_rooted_slot_dispatch_static.py"),
             "--output", str(ROOT / "bridge" / "owner_rooted_slot_dispatch_static_map.json")], env)
        slot_map = json.loads((ROOT / "bridge" / "owner_rooted_slot_dispatch_static_map.json").read_text(encoding="utf-8"))
        if slot_map.get("build", {}).get("exeSha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781":
            raise RuntimeError("CODE-0009 executable fingerprint mismatch")
        if [x.get("callRva") for x in slot_map.get("directCallSites", {}).get("slotAllocation", [])] != ["0x3E262B", "0x3E2919", "0x3E52BD", "0x3E5578"]:
            raise RuntimeError("CODE-0009 allocator caller set changed")
        contract = slot_map.get("slotInitializationContract", {})
        if contract.get("status") != "PROVEN_STATIC" or contract.get("fields", {}).get("+0x48", {}).get("status") != "PROVEN" or contract.get("fields", {}).get("+0x4C", {}).get("status") != "PROVEN":
            raise RuntimeError("CODE-0009 slot initialization evidence missing")
        dispatcher = slot_map.get("dispatcher", {})
        if dispatcher.get("functionRva") != "0x3E5A60" or dispatcher.get("discriminator", {}).get("field") != "+0x4C":
            raise RuntimeError("CODE-0009 anchored dispatcher evidence missing")
        if dispatcher.get("discriminator", {}).get("handlers", {}).get("5", {}).get("targetRva") != "0x3E5B39":
            raise RuntimeError("CODE-0009 discriminator-5 handler mapping changed")
        if slot_map.get("value5Handler", {}).get("targetRva") != "0x3E27B0" or slot_map.get("value5Handler", {}).get("classification") != "SEMANTICS_UNRESOLVED":
            raise RuntimeError("CODE-0009 value-5 semantics were over-promoted")
        if slot_map.get("lifecycle", {}).get("releasePath", {}).get("status") != "NOT_PROVEN":
            raise RuntimeError("CODE-0009 release path unexpectedly promoted")
        if slot_map.get("analysisResult") != "PARTIAL_STATIC":
            raise RuntimeError("CODE-0009 result classification changed")
        if slot_map.get("observerDecision", {}).get("installNow") is not False or slot_map.get("observerDecision", {}).get("gameHookInstallAuthorized") is not False:
            raise RuntimeError("CODE-0009 installation gate invalid")
        print("[OK] CODE-0009 anchored slot dispatcher remains static-only and unresolved")
        run("CODE-0010 CreateBuildingItemAction dispatch tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_create_building_item_dispatch_static"], env)
        run("CODE-0010 CreateBuildingItemAction dispatch map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_create_building_item_dispatch_static.py"),
             "--output", str(ROOT / "bridge" / "create_building_item_dispatch_static_map.json")], env)
        action_map = json.loads((ROOT / "bridge" / "create_building_item_dispatch_static_map.json").read_text(encoding="utf-8"))
        if action_map.get("build", {}).get("exeSha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781":
            raise RuntimeError("CODE-0010 executable fingerprint mismatch")
        offsets = action_map.get("memberOffsets", {})
        if offsets.get("ClientPlayerInput.createBuildingItemAction", {}).get("offset") != "0x1B0":
            raise RuntimeError("CODE-0010 client action offset missing")
        if offsets.get("ServerConsumedPlayerInput.consumedCreateBuildingItemAction", {}).get("offset") != "0x30":
            raise RuntimeError("CODE-0010 consumed action offset missing")
        if action_map.get("versionConsumeCandidates", {}).get("search", {}).get("actionQualifiedCandidateCount") != 0:
            raise RuntimeError("CODE-0010 promoted an unvalidated action consumer")
        if action_map.get("firstActionConsumer", {}).get("status") != "NOT_FOUND":
            raise RuntimeError("CODE-0010 action consumer unexpectedly promoted")
        if action_map.get("analysisResult") != "PARTIAL_STATIC" or action_map.get("observerDecision", {}).get("install") is not False:
            raise RuntimeError("CODE-0010 fail-closed classification invalid")
        print("[OK] CODE-0010 action dispatch remains PARTIAL_STATIC/fail-closed")
        run("CODE-0011 selection/preview convergence tests", [sys.executable, "-m", "unittest",
             "tools.SemanticActionObserver.test_selection_preview_authority_convergence_static"], env)
        convergence_path = ROOT / "bridge" / "selection_preview_authority_convergence_static_map.json"
        run("CODE-0011 selection/preview convergence map", [sys.executable,
             str(ROOT / "tools" / "SemanticActionObserver" / "scan_selection_preview_authority_convergence_static.py"),
             "--output", str(convergence_path)], env)
        convergence_map = json.loads(convergence_path.read_text(encoding="utf-8"))
        if convergence_map.get("build", {}).get("exeSha256") != "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781":
            raise RuntimeError("CODE-0011 executable fingerprint mismatch")
        if convergence_map.get("analysisResult") != "E_PARTIAL_STATIC_FRONTIERS_PARKED":
            raise RuntimeError("CODE-0011 partial-frontier classification changed")
        graph = convergence_map.get("convergenceGraph", {})
        if graph.get("classification") != "NO_CONVERGENCE":
            raise RuntimeError("CODE-0011 convergence graph was over-promoted")
        decision = convergence_map.get("observerDecision", {})
        if decision.get("install") is not False or decision.get("installNow") is not False:
            raise RuntimeError("CODE-0011 observer authorization gate invalid")
        if graph.get("survivingCandidateOwners"):
            raise RuntimeError("CODE-0011 reported an unsupported shared owner")
        fronts = convergence_map.get("fronts", {})
        if fronts.get("A_voxelModelGhost", {}).get("status") != "PARKED_NO_ANCHORED_GHOST_PRODUCER":
            raise RuntimeError("CODE-0011 VoxelModel front was not parked")
        if fronts.get("B_snapOwner", {}).get("status") != "STRUCTURAL_OWNER_ONLY":
            raise RuntimeError("CODE-0011 snap front classification changed")
        if fronts.get("D_resourceIdentity", {}).get("status") != "RESOURCE_ONLY_CONVERGENCE":
            raise RuntimeError("CODE-0011 resource front classification changed")
        parked = {row.get("branch"): row for row in convergence_map.get("parkedBranches", [])}
        if parked.get("CODE-0009 0x3ED1A0 slot family", {}).get("status") != "PARKED" or parked.get("CODE-0010 CreateBuildingItemAction consumer", {}).get("status") != "PARKED":
            raise RuntimeError("CODE-0011 parked branch guard missing")
        print("[OK] CODE-0011 convergence sweep remains offline/static and fail-closed")
        run("CODE-0014 preview activation package tests", [sys.executable, "-m", "unittest",
             "tools.ArchitectProductPath.test_preview_activation_package"], env)
        activation_target = ROOT.parent / "architect_product_path_preview_test"
        if not (activation_target / "mod.json").is_file() or not (activation_target / "src" / "mod.lua").is_file():
            raise RuntimeError("CODE-0014 sibling test package missing")
        print("[OK] CODE-0014 preview activation package is distinct, opt-in, and placement-free")
        run("CODE-0012 product-path staging tests", [sys.executable, "-m", "unittest",
             "tools.ArchitectProductPath.test_product_path_staging"], env)
        product_manifest_path = ROOT / "bridge" / "blueprint_ghost_identity_perturbation_manifest.json"
        product_lua_path = ROOT / "runtime" / "staging" / "ArchitectProductPathPreview.lua"
        run("CODE-0012 product-path staging manifest/package", [sys.executable, "-m",
             "tools.ArchitectProductPath.product_path_staging", "--output", str(product_manifest_path),
             "--lua-output", str(product_lua_path)], env)
        product_manifest = json.loads(product_manifest_path.read_text(encoding="utf-8"))
        if product_manifest.get("status") != "PRODUCT_PATH_STAGING_READY":
            raise RuntimeError("CODE-0012 product path did not remain source-anchored")
        if product_manifest.get("gameMutation") is not False or product_manifest.get("deployedRuntimeChanged") is not False:
            raise RuntimeError("CODE-0012 mutation/deployment boundary invalid")
        if product_manifest.get("observerDecision", {}).get("deploy") is not False:
            raise RuntimeError("CODE-0012 deployment gate invalid")
        if product_manifest.get("adapter", {}).get("runtimePackage", {}).get("module") != "runtime/staging/ArchitectProductPathPreview.lua":
            raise RuntimeError("CODE-0012 runtime package mapping missing")
        if not product_lua_path.is_file():
            raise RuntimeError("CODE-0012 preview package missing")
        product_lua = product_lua_path.read_text(encoding="utf-8")
        if "enabled = false" not in product_lua or "BuildingPlaceEvent" in product_lua or "place(" in product_lua.lower():
            raise RuntimeError("CODE-0012 preview package activation/placement boundary invalid")
        if any(str(row.get("privateItemIdCandidate")) not in product_lua for row in product_manifest.get("variants", [])):
            raise RuntimeError("CODE-0012 manifest/package identity mapping incomplete")
        policy = product_manifest.get("safeCanaryPolicy", {})
        if policy.get("dimensions") != [4, 4, 4] or policy.get("maxCompressedPayloadBytes") != 8 or policy.get("dynamicArrayResize") is not False or policy.get("allocation") is not False:
            raise RuntimeError("CODE-0012 canary safety policy changed")
        variants = product_manifest.get("variants", [])
        if {row.get("variant") for row in variants} != {"CONTROL", "GHOST_VARIANT", "FINAL_VARIANT", "CROSS_WIRED"}:
            raise RuntimeError("CODE-0012 canary matrix incomplete")
        if not all(row.get("validationPassed") and row.get("placement", {}).get("compressedLength") == 8 for row in variants):
            raise RuntimeError("CODE-0012 canary validation/payload bound failed")
        if not product_manifest.get("identityChecks", {}).get("candidateIdsUnique") or not product_manifest.get("identityChecks", {}).get("symbolicGuidsOnly"):
            raise RuntimeError("CODE-0012 private identity checks failed")
        if product_manifest.get("manualTestStatus") != "NOT_RUN_USER_PREVIEW_REQUIRED":
            raise RuntimeError("CODE-0012 incorrectly claimed live preview evidence")
        print("[OK] CODE-0012 product-path staging is source-anchored, bounded, and offline-only")
        staging_diag = STAGING / "ArchitectObserverDiagnostics.c"
        staging_tramp = STAGING / "ArchitectObserverTrampoline.c"
        staging_harness = STAGING / "ArchitectObserverInfrastructureHarness.c"
        for source in (staging_diag, staging_tramp, staging_harness):
            if not source.is_file(): raise RuntimeError(f"CODE-0005A staging source missing: {source.name}")
            if re.search(r"\b(OpenProcess|ReadProcessMemory|WriteProcessMemory|CreateRemoteThread|DebugActiveProcess)\b", source.read_text(encoding="utf-8")):
                raise RuntimeError(f"CODE-0005A staging source contains forbidden process API: {source.name}")
        hot = staging_diag.read_text(encoding="utf-8")
        publish = hot[hot.index("int architect_observer_ring_publish"):hot.index("int architect_observer_ring_drain")]
        if re.search(r"\b(malloc|calloc|realloc|free|CreateFile|WriteFile|Sleep|WaitFor|printf|fopen|VirtualAlloc|OpenProcess|ReadProcessMemory|WriteProcessMemory)\b", publish):
            raise RuntimeError("CODE-0005A producer contains forbidden hot-path operation")
        print("[OK] CODE-0005A producer static no-I/O/no-heap/no-blocking gate")
        target_map = json.loads((ROOT / "bridge" / "target_resolver_static_map.json").read_text(encoding="utf-8"))
        target_candidates = json.loads((ROOT / "bridge" / "target_resolver_reflection_candidates.json").read_text(encoding="utf-8"))
        if target_map.get("analysisMode") != "offline_static_only" or target_map.get("runtimeMutation"):
            raise RuntimeError("target resolver map is not offline/read-only")
        if any(row.get("install") for row in target_map.get("observerCandidates", [])):
            raise RuntimeError("target resolver observer unexpectedly enabled")
        control_names = {row.get("type") for row in target_map.get("reflection", {}).get("highValueControls", [])}
        if "keen::ecs::ClientCursor" not in control_names or not target_candidates.get("controlCandidates"):
            raise RuntimeError("target reflection controls missing")
        if target_map.get("firstUnresolvedBoundary") != "live target acquisition and publication of a stable semantic target before placement":
            raise RuntimeError("target resolver boundary changed unexpectedly")
        print("[OK] target resolver remains reflection-only/fail-closed")

        sys.path.insert(0, str(VOXEL))
        sys.path.insert(0, str(ROOT))
        from architect_voxel import baseline_shapes
        expected = {"hollow_square_4m": "ff818181818181ff", "filled_circle_4m": "3c7effffffff7e3c", "ring_4m": "3c7ec3c3c3c37e3c", "sphere_2m": "6006f66ff66f6006", "filled_cylinder_2m": "f66ff66ff66ff66f", "hollow_cube_2m": "ffff9ff99ff9ffff"}
        for name, payload in expected.items():
            actual = baseline_shapes()[name].payload.hex()
            if actual != payload: raise RuntimeError(f"baseline payload mismatch: {name}")
        print("[OK] six baseline payloads")

        # Recorded-structure regression fixture: verify lossless Q32.32
        # migration, translated bounds, and explicit provenance counters.
        from tools.StructureRecorder.recorder import load_blueprint
        recorded_fixture = ROOT / "blueprints" / "recorded" / "recorder_test_01.architect.json"
        recorded = load_blueprint(recorded_fixture)
        recorded_stats = recorded.statistics()
        if recorded_stats["bounds"]["min"] != [-4.0, 0.0, 0.0] or recorded_stats["bounds"]["max"] != [12.0, 6.0, 4.0]:
            raise RuntimeError("recorded-structure translated bounds mismatch")
        if recorded_stats["bounds"]["size"] != [16.0, 6.0, 4.0]:
            raise RuntimeError("recorded-structure bounds size mismatch")
        if not all(isinstance(v, int) for v in recorded.placements[0]["raw"]["position"]):
            raise RuntimeError("recorded-structure raw coordinates were not migrated losslessly")
        if recorded_stats["buildingRawEventsInRecordingWindow"] != 12 or recorded_stats["pairedBuildingRawEvents"] != 12:
            raise RuntimeError("recorded-structure provenance counters mismatch")
        print("[OK] recorded structure coordinates/bounds/provenance")

        manifest_match = re.search(r"^([0-9a-fA-F]{64})\s+ArchitectNativeRuntime\.dll", MANIFEST.read_text(encoding="utf-8"), re.MULTILINE)
        if not manifest_match: raise RuntimeError("DLL SHA manifest entry missing")
        deployed_hash_before = sha256(DEPLOYED)
        if deployed_hash_at_start is None or deployed_hash_before != deployed_hash_at_start:
            raise RuntimeError("deployed DLL changed during offline regression")
        if deployed_hash_before.lower() != manifest_match.group(1).lower(): raise RuntimeError("deployed DLL does not match SHA manifest")
        native_source = (ROOT / "runtime/native/source/ArchitectNativeRuntime.c").read_text(encoding="utf-8")
        if not re.search(r'#define ARCHITECT_RUNTIME_BUILD_ID\s+"[^"]+"', native_source): raise RuntimeError("native build ID missing")
        staging_source = (STAGING / "ArchitectBlueprintCacheDiagnostic.c").read_text(encoding="utf-8")
        if "architect-v013-blueprintcache-readonly-staging" not in staging_source: raise RuntimeError("staging identity missing")
        print(f"[OK] deployed SHA={deployed_hash_before}")

        vcvars = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat")
        if not vcvars.exists(): raise RuntimeError("MSVC vcvars64.bat not found")
        obj = STAGING / "ArchitectBlueprintCacheDiagnostic.obj"
        staging_c = STAGING / "ArchitectBlueprintCacheDiagnostic.c"
        cmdline = f'call "{vcvars}" && cl /nologo /c /O2 /W4 /EHsc /Fo"{obj}" "{staging_c}"'
        run_shell("MSVC x64 staging compile", cmdline)
        harness_exe = STAGING / "ArchitectObserverInfrastructureHarness.exe"
        harness_cmd = f'call "{vcvars}" && cl /nologo /O2 /W4 /EHsc /Fe:"{harness_exe}" "{staging_harness}" "{staging_diag}" "{staging_tramp}"'
        run_shell("MSVC x64 observer infrastructure harness", harness_cmd)
        run("CODE-0005A native harness", [str(harness_exe)], env)
        print(f"[OK] CODE-0005A harness SHA={sha256(harness_exe)}")
        relay_obj = STAGING / "ArchitectParentCallRelay.obj"
        relay_exe = STAGING / "ArchitectParentCallRelayHarness.exe"
        relay_cmd = f'call "{vcvars}" && ml64 /nologo /c /Fo"{relay_obj}" "{relay_asm}" && cl /nologo /O2 /W4 /Fe:"{relay_exe}" "{relay_harness}" "{relay_obj}"'
        run_shell("MSVC x64 parent relay harness", relay_cmd)
        run("CODE-0005C native relay harness", [str(relay_exe)], env)
        print(f"[OK] CODE-0005C relay harness SHA={sha256(relay_exe)}")
        deployed_hash_after = sha256(DEPLOYED)
        if deployed_hash_after != deployed_hash_at_start: raise RuntimeError("deployed DLL changed during regression")
        print(f"[OK] deployed DLL unchanged before={deployed_hash_at_start} after={deployed_hash_after}")
        print("OFFLINE REGRESSION: PASS")
        return 0
    except Exception as exc:
        print(f"OFFLINE REGRESSION: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
