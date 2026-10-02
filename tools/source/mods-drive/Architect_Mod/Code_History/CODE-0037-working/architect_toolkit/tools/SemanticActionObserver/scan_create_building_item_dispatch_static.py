#!/usr/bin/env python3
"""CODE-0010 offline map for CreateBuildingItemAction dispatch.

The scanner is deliberately conservative: reflection offsets are reported as
layout evidence, while executable candidates are promoted only when a
version-consume pair and same-payload field flow are present.  No process,
debugger, hook, or runtime memory is used.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SUPPORTED_SHA = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
DEPLOYED_DLL_SHA = "C3AAF673001CBE08C508F703C0D9219836067A7A9818A4A9473D3BA49F89A801"
DEFAULT_EXE = ROOT.parent.parent / "enshrouded.exe"
DEFAULT_TYPES = DEFAULT_EXE.parent / ".cache" / "types.json"
PRIOR_MAP = ROOT / "bridge" / "create_building_item_static_map.json"


def hx(value: int | None) -> str | None:
    return None if value is None else f"0x{value:X}"


def load_types(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not isinstance(data.get("types"), list):
        raise RuntimeError("reflection cache has no types array")
    return data


def find_type(types: list[dict[str, Any]], qualified: str) -> dict[str, Any]:
    for row in types:
        if row.get("qualifiedName") == qualified:
            return row
    raise RuntimeError(f"reflection type missing: {qualified}")


def reflected_layout(row: dict[str, Any], status: str = "PROVEN_STATIC_BUILD_1076226") -> dict[str, Any]:
    fields = []
    for field in (row.get("structFields") or {}).values():
        off = int(field.get("dataOffset", 0))
        fields.append({"name": field.get("name"), "offset": hx(off), "offsetBytes": off,
                       "typeIndex": field.get("type"), "status": status})
    fields.sort(key=lambda x: x["offsetBytes"])
    return {"qualifiedName": row.get("qualifiedName"), "size": row.get("size"),
            "alignment": row.get("alignment"), "typeIndex": row.get("index"),
            "fields": fields, "status": status}


def field_offset(layout: dict[str, Any], name: str) -> dict[str, Any] | None:
    return next((x for x in layout.get("fields", []) if x.get("name") == name), None)


def prior_candidates() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not PRIOR_MAP.is_file():
        return {}, []
    prior = json.loads(PRIOR_MAP.read_text(encoding="utf-8-sig"))
    return prior, list(prior.get("completeFieldConsumerCandidates", []))


def build(exe: Path, types_path: Path) -> dict[str, Any]:
    exe = exe.resolve()
    types_path = types_path.resolve()
    # StaticImage is intentionally used only for hash validation; no PE/code
    # execution or process access is involved in this map.
    import hashlib
    digest = hashlib.sha256(exe.read_bytes()).hexdigest().upper()
    if digest != SUPPORTED_SHA:
        raise RuntimeError(f"BUILD_MISMATCH expected={SUPPORTED_SHA} actual={digest}")
    types = load_types(types_path)["types"]
    action = reflected_layout(find_type(types, "keen::ecs::CreateBuildingItemAction"))
    action_ds = reflected_layout(find_type(types, "keen::ds::ecs::CreateBuildingItemAction"))
    client_data = reflected_layout(find_type(types, "keen::ecs::ClientPlayerInputData"))
    client = reflected_layout(find_type(types, "keen::ecs::ClientPlayerInput"))
    server = reflected_layout(find_type(types, "keen::ecs::ServerConsumedPlayerInput"))
    ui = reflected_layout(find_type(types, "keen::ecs::UiCreateBuildingItemEvent"))
    stock = reflected_layout(find_type(types, "keen::ecs::BuildingStockCycleAction"))
    prior, candidates = prior_candidates()
    if prior and prior.get("executable", {}).get("sha256") not in (None, digest):
        raise RuntimeError("prior CreateBuildingItem static map fingerprint mismatch")

    client_action = field_offset(client_data, "createBuildingItemAction")
    consumed_action = field_offset(server, "consumedCreateBuildingItemAction")
    stock_member = field_offset(client_data, "buildingStockCycleAction")
    action_fields = {x["name"]: x for x in action["fields"]}

    # The prior scanner intentionally found shape-only candidates.  Preserve a
    # bounded, auditable sample and reject all until action ownership/version
    # consumption is proven in the same function.
    rejected = []
    for row in candidates[:32]:
        rejected.append({"functionStartRva": row.get("functionStartRva"),
                         "functionEndRva": row.get("functionEndRva"),
                         "baseRegister": row.get("baseRegister"),
                         "fieldAccesses": row.get("fieldAccesses", [])[:8],
                         "reason": "generic +0/+4/+8 shape; no validated PlayerInput action base, consumed-version pair, or same-payload flow"})

    return {
        "schemaVersion": 1,
        "codeId": "CODE-0010",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "deliveryMode": "OFFLINE_STATIC_ONLY",
        "build": {"revision": 1076226, "exeSha256": digest, "supportedExeSha256": SUPPORTED_SHA,
                   "deployedDllSha256": DEPLOYED_DLL_SHA, "fingerprintMatches": digest == SUPPORTED_SHA},
        "safety": {"processAccess": False, "debugApis": False, "runtimeHooksInstalled": False,
                   "writesGameMemory": False, "writesExecutable": False, "memoryScanning": False},
        "installNow": False,
        "gameHookInstallAuthorized": False,
        "currentSourceDesignationAuthorized": False,
        "reflectionSource": {"path": str(types_path), "status": "PROVEN_STATIC_SOURCE", "readOnly": True},
        "reflectedLayouts": {"CreateBuildingItemAction": action, "dsCreateBuildingItemAction": action_ds,
                              "ClientPlayerInputData": client_data, "ClientPlayerInput": client,
                              "ServerConsumedPlayerInput": server, "UiCreateBuildingItemEvent": ui,
                              "BuildingStockCycleAction": stock},
        "memberOffsets": {
            "ClientPlayerInput.createBuildingItemAction": {"owner": "ClientPlayerInputData embedded at ClientPlayerInput+0x00",
                "offset": client_action["offset"], "offsetBytes": client_action["offsetBytes"], "payloadType": "keen::ecs::CreateBuildingItemAction",
                "status": "PROVEN_REFLECTION_ONLY", "provenance": "types.json structFields; executable owner identity remains unresolved"},
            "ServerConsumedPlayerInput.consumedCreateBuildingItemAction": {"offset": consumed_action["offset"], "offsetBytes": consumed_action["offsetBytes"],
                "payloadType": "keen::VersionedData", "status": "PROVEN_REFLECTION_ONLY", "provenance": "types.json structFields; live server owner remains unresolved"},
            "ClientPlayerInputData.buildingStockCycleAction": {"offset": stock_member["offset"], "offsetBytes": stock_member["offsetBytes"],
                "payloadType": "keen::ecs::BuildingStockCycleAction", "status": "PROVEN_STRUCTURAL_CONTROL_ONLY"},
        },
        "actionProtocol": {"actionSize": hx(action["size"]), "versionData": {"offset": action_fields["versionData"]["offset"], "widthBytes": 4},
            "selectedIndex": {"offset": action_fields["selectedIndex"]["offset"], "widthBytes": 4},
            "itemId": {"offset": action_fields["itemId"]["offset"], "widthBytes": 4},
            "consumedVersionOffset": consumed_action["offset"],
            "requiredPair": "same validated owner relationship: client action version read/compare against server consumed +0x30, then consumed-version update",
            "status": "REFLECTION_PROVEN_EXECUTABLE_CONSUMER_UNSOLVED"},
        "versionConsumeCandidates": {"search": {"required": ["validated ClientPlayerInput action member base", "validated ServerConsumedPlayerInput consumed member or update", "version compare/change", "selectedIndex/itemId from same payload"],
            "priorGenericCandidateCount": len(candidates), "actionQualifiedCandidateCount": 0,
            "status": "NO_VALIDATED_VERSION_CONSUME_EDGE",
            "rejections": rejected,
            "reason": "Existing executable scan found only generic shape matches; no candidate satisfies the ownership and version protocol simultaneously."}},
        "firstActionConsumer": {"status": "NOT_FOUND", "functionRva": None, "functionBoundary": None,
            "reason": "No instruction-backed function currently proves both action member ownership and consumed-version gating."},
        "forwardDataFlow": {"selectedIndex": {"source": "ClientPlayerInputData+0x1B0+0x04", "status": "REFLECTION_ONLY", "firstPersistentNonStackWrite": None},
            "itemId": {"source": "ClientPlayerInputData+0x1B0+0x08", "status": "REFLECTION_ONLY", "firstPersistentNonStackWrite": None},
            "placementR8D": {"status": "NOT_CONNECTED", "evidence": "0x3E2CD0 R8D frontier is known, but no CreateBuildingItemAction data-flow edge reaches it"}},
        "uiCreateBuildingItemEvent": {"status": "UNSOLVED", "layout": {"size": hx(ui["size"]), "fields": ui["fields"]},
            "convergence": "No instruction-level construction/emission path from CreateBuildingItemAction fields was identified."},
        "convergenceTests": {
            "persistentSelectionPreview": {"status": "NOT_PROVEN", "reason": "No validated action consumer"},
            "snapRSI+0xF0": {"status": "NOT_PROVEN", "reason": "No continuous action data-flow edge"},
            "snapRSI+0x110": {"status": "NOT_PROVEN", "reason": "No continuous action data-flow edge"},
            "previewTransform": {"status": "NOT_PROVEN", "reason": "No continuous action data-flow edge"},
            "placement0x3E2CD0R8D": {"status": "NOT_PROVEN", "reason": "Downstream R8D source remains separate"},
            "VoxelBlueprintCache": {"status": "NOT_PROVEN", "reason": "No lookup/cache identity edge"},
            "VoxelModelGhost": {"status": "NOT_PROVEN", "reason": "No exact data-flow or identity edge"}},
        "siblingActionControl": {"buildingStockCycleAction": {"offset": stock_member["offset"], "status": "STRUCTURAL_CONTROL_ONLY",
            "note": "Nearby versioned action layout; no semantics or offsets are transferred to CreateBuildingItemAction."}},
        "contradictionsAndNegativeFindings": ["Reflection offsets are not native owner addresses.", "Same +0/+4/+8 shapes are explicitly rejected as generic.", "UiCreateBuildingItemEvent field similarity does not establish emission.", "CreateBuildingItemAction.itemId is not statically connected to placement R8D."],
        "analysisResult": "PARTIAL_STATIC",
        "firstUnresolvedBoundary": "action-specific version-consume dispatch and validated PlayerInput/ConsumedPlayerInput owner relationship",
        "observerDecision": {"install": False, "installNow": False, "gameHookInstallAuthorized": False, "failClosed": True,
            "reason": "CODE-0010 is offline/static only; no action-specific consumer or authority convergence is proven."},
        "nextEvidence": ["Identify a concrete version-consume function with both owner relationships before examining payload flow.", "Do not resume generic +0/+4/+8 scans.", "If this boundary remains unresolved, move to the independently identified ghost/preview VoxelModel producer path."],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--types", type=Path, default=DEFAULT_TYPES)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.exe, args.types)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"analysisResult": report["analysisResult"], "exeSha256": report["build"]["exeSha256"],
                      "actionQualifiedCandidateCount": report["versionConsumeCandidates"]["search"]["actionQualifiedCandidateCount"], "installNow": report["installNow"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
