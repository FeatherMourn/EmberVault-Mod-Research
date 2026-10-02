#!/usr/bin/env python3
"""Build-locked, offline ClientPlayerInput reflection/data-flow map.

This scanner deliberately does not attach to a process or search process
memory.  It combines the installed, read-only reflection cache with the
already reviewed InventoryTransferAction PE evidence.  A reflected type is
not promoted to a live object merely because one native register happens to
contain an action-shaped payload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_SHA256 = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
REVISION = 1076226


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def hx(value: int | None) -> str | None:
    return None if value is None else f"0x{value:X}"


def find_type(types: list[dict[str, Any]], qualified: str) -> dict[str, Any] | None:
    for t in types:
        if t.get("qualifiedName") == qualified:
            return t
    return None


def field_rows(t: dict[str, Any] | None, types: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if not t:
        return []
    types = types or []
    return [{"name": name, "typeIndex": field.get("type"),
             "typeName": (types[field.get("type")].get("qualifiedName")
                          if isinstance(field.get("type"), int) and field.get("type") < len(types)
                          and isinstance(types[field.get("type")], dict) else None),
             "offset": hx(field.get("dataOffset")),
             "offsetBytes": field.get("dataOffset"),
             "attributes": field.get("attributes") or {}}
            for name, field in (t.get("structFields") or {}).items()]


def type_snapshot(t: dict[str, Any] | None, status: str, types: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if not t:
        return {"status": "UNKNOWN", "reason": "qualified type not present in reflection cache"}
    return {"status": status, "index": t.get("index"), "name": t.get("name"),
            "qualifiedName": t.get("qualifiedName"), "size": t.get("size"),
            "alignment": t.get("alignment"), "innerType": t.get("innerType"),
            "fieldCount": t.get("fieldCount"), "flags": t.get("flags"),
            "attributes": t.get("attributes") or {}, "fields": field_rows(t, types)}


def action_layout(types: list[dict[str, Any]], qualified: str, status: str) -> dict[str, Any]:
    return type_snapshot(find_type(types, qualified), status, types)


def build_report(exe: Path, types_path: Path, inventory_path: Path) -> dict[str, Any]:
    actual = sha256(exe)
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"BUILD_MISMATCH expected={EXPECTED_SHA256} actual={actual}")
    reflection = json.loads(types_path.read_text(encoding="utf-8-sig"))
    types = reflection.get("types") if isinstance(reflection, dict) else None
    if not isinstance(types, list):
        raise SystemExit("REFLECTION_INVALID types array missing")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8-sig"))

    runtime_input = find_type(types, "keen::ecs::ClientPlayerInput")
    runtime_data = find_type(types, "keen::ecs::ClientPlayerInputData")
    ds_input = find_type(types, "keen::ds::ecs::ClientPlayerInput")
    ds_data = find_type(types, "keen::ds::ecs::ClientPlayerInputData")
    server = find_type(types, "keen::ecs::ServerConsumedPlayerInput")
    ds_server = find_type(types, "keen::ds::ecs::ServerConsumedPlayerInput")

    relevant = {}
    for name in ("inventoryTransferAction", "createBuildingItemAction", "buildingStockCycleAction"):
        fld = (runtime_data or {}).get("structFields", {}).get(name)
        relevant[name] = {"offset": hx(fld.get("dataOffset")) if fld else None,
                          "offsetBytes": fld.get("dataOffset") if fld else None,
                          "typeIndex": fld.get("type") if fld else None,
                          "status": "PROVEN_STATIC_BUILD_1076226" if fld else "UNKNOWN"}

    # The known anchor is copied from the independently generated map, not
    # inferred by this report.  Keep all concrete register/field evidence and
    # explicitly mark the first missing owner transition.
    anchor = {
        "consumerFunction": {"beginRva": "0x371810", "endRva": "0x37229F", "status": "PROVEN_BUILD_1076226"},
        "entryInstructions": [
            {"rva": "0x37182C", "bytes": "48 8B 72 10", "text": "mov rsi,[rdx+0x10]", "effect": "action/envelope pointer candidate"},
            {"rva": "0x371830", "bytes": "4C 8B E1", "text": "mov r12,rcx", "effect": "preserves dispatch/service context"},
            {"rva": "0x37184D", "bytes": "48 8B 4A 38", "text": "mov rcx,[rdx+0x38]", "effect": "consumed-record-like context"},
            {"rva": "0x371842", "bytes": "8B 46 08", "text": "mov eax,[rsi+0x08]", "effect": "reads action version"},
            {"rva": "0x371869", "bytes": "89 41 20", "text": "mov [rcx+0x20],eax", "effect": "copies version to downstream record"},
        ],
        "payload": {"baseExpression": "RSI+0x08", "size": "0x20", "identity": "InventoryTransferAction", "status": "PROVEN_BUILD_1076226"},
        "pointerDataFlow": [
            "RDX is the consumer's dispatch context argument.",
            "[RDX+0x10] is loaded into RSI at 0x37182C; fields at RSI+0x08..0x26 form the proven action payload.",
            "[RDX+0x38] is loaded into RCX and receives a version copy at +0x20.",
            "The static interval does not establish that RDX, [RDX+0x10], or their owners are a reflected ClientPlayerInput instance.",
        ],
        "firstUnresolvedPointerTransition": {
            "locationRva": "0x37182C",
            "expression": "dispatchContext + 0x10 -> RSI -> RSI + 0x08 action payload",
            "status": "UNSOLVED",
            "reason": "No action-specific producer/copy edge ties the dispatch context to ClientPlayerInput.data at reflected offset 0x00."
        },
    }

    return {
        "schemaVersion": 1,
        "tool": "scan_client_player_input_static.py",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "safety": {"processAccess": False, "debugApis": False, "writesExecutable": False,
                   "memoryScanning": False, "runtimeHooksInstalled": False},
        "build": {"revision": REVISION, "sha256": actual, "supportedSha256": EXPECTED_SHA256,
                  "fingerprintMatches": actual == EXPECTED_SHA256},
        "reflectionSource": {
            "path": str(types_path), "status": "PROVEN_STATIC_SOURCE",
            "repositoryReflectionDataPresent": (Path(__file__).resolve().parents[2] / "reflection_data.json").is_file(),
            "note": "The installed .cache/types.json is read-only local reflection evidence; no process/runtime lookup was attempted."
        },
        "reflectedLayouts": {
            "VersionedData": action_layout(types, "keen::VersionedData", "PROVEN_STATIC_BUILD_1076226"),
            "InventoryTransferAction": action_layout(types, "keen::ecs::InventoryTransferAction", "PROVEN_STATIC_BUILD_1076226"),
            "CreateBuildingItemAction": action_layout(types, "keen::ecs::CreateBuildingItemAction", "PROVEN_STATIC_BUILD_1076226"),
            "BuildingStockCycleAction": action_layout(types, "keen::ecs::BuildingStockCycleAction", "PROVEN_STATIC_BUILD_1076226"),
            "ClientPlayerInputData": type_snapshot(runtime_data, "PROVEN_STATIC_BUILD_1076226", types),
            "ClientPlayerInput": type_snapshot(runtime_input, "PROVEN_STATIC_BUILD_1076226", types),
            "ds::ClientPlayerInputData": type_snapshot(ds_data, "PROVEN_STATIC_BUILD_1076226", types),
            "ds::ClientPlayerInput": type_snapshot(ds_input, "PROVEN_STATIC_BUILD_1076226", types),
            "ServerConsumedPlayerInput": type_snapshot(server, "PROVEN_STATIC_BUILD_1076226", types),
            "ds::ServerConsumedPlayerInput": type_snapshot(ds_server, "PROVEN_STATIC_BUILD_1076226", types),
        },
        "clientPlayerInputRelevantOffsets": relevant,
        "knownInventoryTransferAnchor": anchor,
        "candidateClientPlayerInput": {
            "status": "UNSOLVED",
            "candidateBase": None,
            "reason": "The proven RSI+0x08 action payload is not enough to identify a ClientPlayerInput base. Reflected validation requires candidateBase+0x00 inventoryTransferAction plus independent fields (for example +0x1B0 and +0xA4), which static evidence does not provide.",
            "requiredMultiFieldValidation": ["candidateBase+0x00 == exact observed InventoryTransferAction", "candidateBase+0x1B0 is coherent CreateBuildingItemAction", "candidateBase+0xA4 is coherent BuildingStockCycleAction"],
            "observerInstall": False,
            "failClosed": True,
        },
        "parentObservation": {"status": "NOT_INSTALLED", "reason": "No safe parent pointer or producer boundary was proven; no new detour or runtime probe is justified."},
        "createBuildingItemThroughParent": {"status": "EXPERIMENTAL_NOT_AVAILABLE", "offset": relevant["createBuildingItemAction"], "readOnly": True},
        "buildingStockCycleFutureAnchor": {"status": "PROVEN_STATIC_ONLY", "offset": relevant["buildingStockCycleAction"], "actionSize": "0x14"},
        "serverConsumedInput": {"status": "PROVEN_STATIC_LAYOUT_UNSOLVED_OWNER", "consumedCreateBuildingItemActionOffset": "0x30", "consumedBuildingStockCycleActionOffset": "0x40", "note": "These are VersionedData fields in the reflected server record; no live owner identity is claimed."},
        "uiCreateBuildingItemEvent": {"status": "UNSOLVED", "reason": "No action-specific edge from UiCreateBuildingItemEvent to the parent input chain was found in the existing evidence."},
        "placementCorrelation": {"status": "UNSOLVED", "reason": "No live CreateBuildingItemAction observer exists; itemId ↔ BuildingPlaceEvent.trackingItemId remains unvalidated."},
        "priorStaticMap": {"path": str(inventory_path), "status": "PROVEN_ANCHOR_IMPORTED", "staticMapStatus": inventory.get("strongestConclusion", {}).get("status"), "consumerFound": inventory.get("staticConclusion", {}).get("consumerFound")},
        "statusModel": {"InventoryTransferAction": "PROVEN_BUILD_1076226", "ClientPlayerInput_reflection": "PROVEN_STATIC_BUILD_1076226", "ClientPlayerInput_live_identity": "UNSOLVED", "CreateBuildingItemAction_reflection": "PROVEN_STATIC_BUILD_1076226", "CreateBuildingItemAction_consumer": "UNSOLVED", "buildingStockCycleAction": "STATIC_REFLECTION_ONLY"},
        "unresolved": ["producer/copy site that forms dispatchContext+0x10", "concrete owner of RSI action payload", "runtime resource/ecs lookup path", "safe static correlation to UiCreateBuildingItemEvent", "live multi-field ClientPlayerInput validation"],
    }


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=root / "enshrouded.exe")
    parser.add_argument("--types", type=Path, default=root / ".cache" / "types.json")
    parser.add_argument("--inventory-map", type=Path, default=Path(__file__).resolve().parents[2] / "bridge" / "inventory_transfer_static_map.json")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[2] / "bridge" / "client_player_input_static_map.json")
    args = parser.parse_args()
    report = build_report(args.exe.resolve(), args.types.resolve(), args.inventory_map.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"clientPlayerInput=PROVEN_STATIC; liveIdentity=UNSOLVED; output={args.output.resolve()}")


if __name__ == "__main__":
    main()
