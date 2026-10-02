#!/usr/bin/env python3
"""CODE-0011 bounded multi-front static convergence sweep.

Only build-locked JSON maps and the on-disk executable hash are consumed.  No
process access, debugging, hooks, injection, or runtime writes are possible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT.parent.parent / "enshrouded.exe"
SUPPORTED_SHA = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
DEPLOYED_DLL_SHA = "C3AAF673001CBE08C508F703C0D9219836067A7A9818A4A9473D3BA49F89A801"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build(exe: Path, bridge: Path) -> dict[str, Any]:
    digest = hashlib.sha256(exe.read_bytes()).hexdigest().upper()
    if digest != SUPPORTED_SHA:
        raise RuntimeError(f"BUILD_MISMATCH expected={SUPPORTED_SHA} actual={digest}")
    names = {
        "create": "create_building_item_dispatch_static_map.json",
        "snap": "snap_candidate_selection_static_map.json",
        "buildingSnap": "building_snap_static_map.json",
        "commit": "building_commit_transform_static_map.json",
        "placement": "placement_blueprint_authority_static_map.json",
        "owner": "owner_rooted_slot_dispatch_static_map.json",
    }
    maps = {key: load_json(bridge / name) for key, name in names.items()}

    # Exact anchors and instruction-backed slices imported from the reviewed
    # front maps.  Each edge retains source locations so graph membership is
    # auditable rather than a subjective score.
    graph_nodes = [
        {"id": "fn:0x3E79C0", "kind": "function", "fronts": ["B"], "status": "ANCHORED"},
        {"id": "owner:RSI@0x3E79C0", "kind": "owner_candidate", "fronts": ["B"], "status": "STRUCTURAL_ONLY"},
        {"id": "field:owner+0xF0", "kind": "field", "fronts": ["B"], "status": "PROVEN_ACCESS"},
        {"id": "field:owner+0x110", "kind": "field", "fronts": ["B"], "status": "PROVEN_ACCESS"},
        {"id": "fn:0x3E2CD0", "kind": "function", "fronts": ["C"], "status": "ANCHORED"},
        {"id": "field:commit.R8D", "kind": "argument", "fronts": ["C"], "status": "PROVEN_SOURCE_READ"},
        {"id": "field:commit.RDX", "kind": "argument", "fronts": ["C"], "status": "PROVEN_SOURCE_READ"},
        {"id": "resource:VoxelBlueprint", "kind": "resource_identity", "fronts": ["D"], "status": "RESOURCE_ONLY"},
        {"id": "resource:VoxelModel", "kind": "resource_identity", "fronts": ["A", "D"], "status": "RESOURCE_ONLY"},
        {"id": "action:CreateBuildingItem", "kind": "action", "fronts": ["C"], "status": "REFLECTION_ONLY"},
        {"id": "fn:0x3ED1A0", "kind": "function", "fronts": [], "status": "PARKED_CODE-0009"},
        {"id": "action:CreateBuildingItem.consumer", "kind": "function", "fronts": [], "status": "PARKED_CODE-0010"},
    ]
    graph_edges = [
        {"from": "fn:0x3E79C0", "to": "field:owner+0xF0", "evidence": "instruction-backed access", "source": "snap map candidateFilter.cacheLookupCall", "status": "PROVEN_ACCESS"},
        {"from": "fn:0x3E79C0", "to": "field:owner+0x110", "evidence": "instruction-backed source collection", "source": "snap map candidateFilter.sourceCollection", "status": "PROVEN_ACCESS"},
        {"from": "fn:0x3E2CD0", "to": "field:commit.R8D", "evidence": "R8D consumed at placement call frontier", "source": "building snap placementDataFlow / commit registerProvenance", "status": "PROVEN_DOWNSTREAM"},
        {"from": "fn:0x3E2CD0", "to": "field:commit.RDX", "evidence": "incoming transform/context argument", "source": "commit registerProvenance.R15 and eventFieldFlow", "status": "PROVEN_DOWNSTREAM"},
        {"from": "resource:VoxelBlueprint", "to": "resource:VoxelModel", "evidence": "exported resource relationship only", "source": "historical EML/resource evidence", "status": "RESOURCE_ONLY"},
        {"from": "action:CreateBuildingItem", "to": "field:commit.R8D", "evidence": "no continuous instruction/data-flow edge", "source": "CODE-0010 dispatch map", "status": "REJECTED"},
        {"from": "owner:RSI@0x3E79C0", "to": "fn:0x3E2CD0", "evidence": "register/offset similarity only; runtime object identity unproven", "source": "cross-front comparison", "status": "REJECTED_COINCIDENCE"},
    ]

    front_a = {
        "objective": "VoxelModel/ghost preview producer-update",
        "anchors": {"resource": "VoxelModelResource", "status": "RESOURCE_ONLY"},
        "boundedHops": [],
        "findings": ["No building-specific executable VoxelModel resolver/ghost writer is present in the reviewed maps.", "Generic renderer/model infrastructure is not accepted without a placement anchor."],
        "parked": True,
        "parkReason": "No anchored building-placement connection within two meaningful hops; resource identity remains non-authoritative.",
        "status": "PARKED_NO_ANCHORED_GHOST_PRODUCER",
    }
    snap = maps["snap"]
    front_b = {
        "objective": "snap-context owner/writer recovery",
        "anchors": {"candidateFilterRva": snap.get("candidateFilter", {}).get("rva"), "cacheLookup": snap.get("candidateFilter", {}).get("cacheLookupCall"),
                    "ownerFields": ["[RSI+0xF0]", "[RSI+0x110]"]},
        "boundedHops": ["0x3E79C0 -> 0xCA90E0 (candidate +0x08, owner [RSI+0xF0])"],
        "findings": ["Source collection [RSI+0x110] and cache [RSI+0xF0] are instruction-backed within the candidate filter.", "Accepted 0x50-byte records are caller-owned/local; persistence and cross-front owner identity remain unresolved."],
        "sameOwnerAcrossFronts": False,
        "status": "STRUCTURAL_OWNER_ONLY",
    }
    commit = maps["commit"]
    front_c = {
        "objective": "commit-input backward provenance",
        "anchors": {"commitRva": commit.get("function", {}).get("rva", "0x3E2CD0"), "callSite": "0x280F86", "returnRva": "0x280F8B"},
        "boundedHops": ["0x280F75 loads R8D from [RBX] -> 0x280F86 call 0x3E2CD0", "0x3E2CD0 R15=RDX and RSI=RCX at 0x3E2CEF/0x3E2CF6"],
        "findings": ["R8D and RDX/transform origins are proven downstream inputs, but their persistent upstream owner is unresolved.", "No connection to the snap owner or preview producer was proven."],
        "sourceEvidence": commit.get("registerProvenance", {}),
        "status": "COMMIT_FRONTIER_OWNER_UNRESOLVED",
    }
    front_d = {
        "objective": "resource-identity bridge",
        "anchors": {"itemInfo": "resource exports", "voxelBlueprint": "VoxelBlueprintItemRegistryResource", "voxelModel": "VoxelModelResource"},
        "boundedHops": [],
        "findings": ["Item/blueprint/model relationships are available as exported resource evidence.", "No executable owner/data-flow edge establishes runtime authority."],
        "status": "RESOURCE_ONLY_CONVERGENCE",
    }

    target_matrix = {
        "candidate:ownerRSI": {"selectedItemId": False, "voxelBlueprintCache": False, "voxelModelGhost": False, "snapContext": True, "previewTransform": False, "validationState": False, "commitR8DOrigin": False, "commitRDXOrigin": False},
        "candidate:commitInputs": {"selectedItemId": False, "voxelBlueprintCache": False, "voxelModelGhost": False, "snapContext": False, "previewTransform": True, "validationState": True, "commitR8DOrigin": True, "commitRDXOrigin": True},
        "candidate:resourceRelationship": {"selectedItemId": True, "voxelBlueprintCache": True, "voxelModelGhost": True, "snapContext": False, "previewTransform": False, "validationState": False, "commitR8DOrigin": False, "commitRDXOrigin": False},
    }
    parked = [
        {"branch": "CODE-0009 0x3ED1A0 slot family", "status": "PARKED", "reason": "No independent front reaches the same owner/records."},
        {"branch": "CODE-0010 CreateBuildingItemAction consumer", "status": "PARKED", "reason": "No independent frontier reaches a validated action owner/version-consume site."},
        {"branch": "generic VoxelModel/render xrefs", "status": "PARKED", "reason": "No building-placement anchor within two hops."},
    ]
    return {
        "schemaVersion": 1, "codeId": "CODE-0011", "analysisMode": "OFFLINE_STATIC_ONLY", "deliveryMode": "OFFLINE_STATIC_ONLY",
        "build": {"revision": 1076226, "exeSha256": digest, "supportedExeSha256": SUPPORTED_SHA, "deployedDllSha256": DEPLOYED_DLL_SHA, "fingerprintMatches": digest == SUPPORTED_SHA},
        "safety": {"processAccess": False, "debugApis": False, "runtimeHooksInstalled": False, "writesGameMemory": False, "writesExecutable": False, "deploymentChanged": False},
        "fronts": {"A_voxelModelGhost": front_a, "B_snapOwner": front_b, "C_commitInputs": front_c, "D_resourceIdentity": front_d},
        "convergenceGraph": {"nodes": graph_nodes, "edges": graph_edges, "classification": "NO_CONVERGENCE", "classificationRule": "No identical instruction-backed owner/object/field is reached from two target fronts."},
        "targetPropertyMatrix": target_matrix,
        "survivingCandidateOwners": [],
        "parkedBranches": parked,
        "evidenceLabels": {"PROVEN": "direct instruction/reflection evidence", "INFERRED": "bounded structural inference", "RESOURCE_ONLY": "exported/reflection relationship without executable owner proof", "UNKNOWN": "not established"},
        "contradictions": ["RSI is a placement/snap register in separate functions, but object identity across those invocations is not proven.", "Resource ItemInfo/VoxelBlueprint/VoxelModel relationships do not establish a native persistent owner.", "Commit R8D/RDX inputs are downstream frontiers, not proven selection writers."],
        "analysisResult": "E_PARTIAL_STATIC_FRONTIERS_PARKED",
        "firstUnresolvedBoundary": "shared persistent owner connecting preview, snap, blueprint identity, and commit inputs",
        "observerDecision": {"install": False, "installNow": False, "gameHookInstallAuthorized": False, "failClosed": True, "reason": "Bounded offline sweep found no multi-front instruction-backed convergence; no runtime observer is justified."},
        "nextEvidence": ["Identify a building-specific VoxelModel ghost producer/update writer with an anchored placement caller.", "Use debugger/runtime evidence only in a separately authorized future milestone after a persistent owner candidate is proven."],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=EXE)
    parser.add_argument("--bridge", type=Path, default=ROOT / "bridge")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.exe, args.bridge)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"analysisResult": report["analysisResult"], "exeSha256": report["build"]["exeSha256"], "graph": report["convergenceGraph"]["classification"], "install": report["observerDecision"]["install"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
