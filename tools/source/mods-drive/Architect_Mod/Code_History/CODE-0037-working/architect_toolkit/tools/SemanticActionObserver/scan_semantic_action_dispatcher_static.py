#!/usr/bin/env python3
"""Offline map of the proven action-dispatch family.

This is intentionally conservative: it only disassembles the build-locked
InventoryTransferAction consumer and the bounded set of handler ranges already
recorded in inventory_transfer_static_map.json.  It does not perform process
access, a broad numeric memory search, or a runtime hook.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import capstone
import pefile

EXPECTED_SHA256 = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
CONSUMER = (0x371810, 0x37229F)


def hx(v: int) -> str:
    return f"0x{v:X}"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


class Image:
    def __init__(self, path: Path):
        self.path, self.data = path, path.read_bytes()
        self.digest = sha(self.data)
        if self.digest != EXPECTED_SHA256:
            raise SystemExit(f"BUILD_MISMATCH expected={EXPECTED_SHA256} actual={self.digest}")
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = [(s.VirtualAddress, s.PointerToRawData, s.SizeOfRawData,
                          s.Misc_VirtualSize) for s in self.pe.sections]
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        self.md.detail = True

    def offset(self, rva: int) -> int:
        for va, raw, raw_size, virtual_size in self.sections:
            if va <= rva < va + max(raw_size, virtual_size):
                return raw + rva - va
        raise ValueError(f"RVA outside image: {hx(rva)}")

    def disasm(self, begin: int, end: int):
        off = self.offset(begin)
        return list(self.md.disasm(self.data[off:off + end - begin], self.base + begin))


def memory_accesses(image: Image, ranges: list[tuple[int, int]]) -> list[dict[str, Any]]:
    rows = []
    wanted = {0x20, 0x30, 0x40}
    for begin, end in ranges:
        for ins in image.disasm(begin, end):
            if not ins.operands:
                continue
            for op in ins.operands:
                if op.type != capstone.x86.X86_OP_MEM or op.mem.disp not in wanted:
                    continue
                base = ins.reg_name(op.mem.base) if op.mem.base else None
                rows.append({"rva": hx(ins.address - image.base), "rangeBeginRva": hx(begin), "instruction": f"{ins.mnemonic} {ins.op_str}",
                             "baseRegister": base, "displacement": hx(op.mem.disp),
                             "write": ins.mnemonic.startswith(("mov", "stos", "xchg", "lock")) and
                                     len(ins.operands) > 0 and op is ins.operands[0]})
    return rows


def build_report(image: Image, inventory: dict[str, Any], client: dict[str, Any], create: dict[str, Any]) -> dict[str, Any]:
    direct = inventory.get("directCallerInventory") or {}
    ranges = [CONSUMER, (0x385D80, 0x386166), (0x386180, 0x3863B0), (0x3883C0, 0x3885BC)]
    for rows in direct.values():
        for row in rows:
            b, e = int(row["functionBeginRva"], 16), int(row["functionEndRva"], 16)
            if e - b <= 0x20000:
                ranges.append((b, e))
    # deduplicate and cap the connected set to avoid turning this into a broad scan
    ranges = list(dict.fromkeys(ranges))[:64]
    accesses = memory_accesses(image, ranges)
    # Only the RCX base at 0x371869 is known to be a consumed-record-like
    # destination.  Do not treat stack/local bases or unrelated registers with
    # the same numeric displacement as the reflected ServerConsumed object.
    # No aggregate match is promoted: the bounded caller set contains helper
    # functions that reuse registers for unrelated locals. Establishing the
    # cluster requires data-flow identity, not merely equal displacements.
    same_base_cluster = []

    anchor = inventory.get("actionCandidate", {})
    return {
        "schemaVersion": 1,
        "tool": "scan_semantic_action_dispatcher_static.py",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "safety": {"processAccess": False, "debugApis": False, "writesExecutable": False,
                   "broadNumericScan": False, "runtimeHooksInstalled": False},
        "build": {"revision": 1076226, "sha256": image.digest, "supportedSha256": EXPECTED_SHA256,
                  "fingerprintMatches": image.digest == EXPECTED_SHA256},
        "inventoryWrapperArchitecture": {
            "status": "INFERRED",
            "consumerRange": {"beginRva": hx(CONSUMER[0]), "endRva": hx(CONSUMER[1])},
            "dispatchContextRegister": "RDX",
            "actionEnvelopeExpression": "[RDX+0x10] -> RSI",
            "actionPayloadExpression": "RSI+0x08",
            "payloadSize": "0x20",
            "headerBeforePayload": {"bytesBeforeAction": "0x08", "status": "UNKNOWN",
                                     "reason": "No static producer/copy routine proves whether these bytes are a generic header or envelope state."},
            "metadataOrTypeField": {"status": "UNKNOWN", "reason": "The consumer reads action fields but no wrapper type/length field is established."},
            "producerCopyRvas": [],
            "enqueueDispatchRvas": [],
            "unresolvedPointerTransition": "0x37182C: dispatchContext+0x10 becomes RSI; producer/owner is not statically connected.",
        },
        "dispatchGraph": {
            "consumer": "0x371810..0x37229F",
            "branches": [
                {"at": "0x37200D", "target": "0x386180", "condition": "action type == 3"},
                {"at": "0x372020", "target": "0x385D80", "condition": "accepted non-3 path"},
            ],
            "downstream": ["0x385D80 -> 0x3883C0", "0x386180 -> 0x3883C0"],
            "status": "PROVEN_STATIC_BUILD_1076226",
        },
        "consumedVersionCluster": {
            "reflectedOffsets": {"inventory": "0x20", "createBuilding": "0x30", "buildingStockCycle": "0x40"},
            "connectedAccesses": accesses,
            "sameBaseHasAllThreeOffsets": bool(same_base_cluster),
            "sameBaseRegisters": same_base_cluster,
            "status": "UNSOLVED",
            "reason": "Connected code has a proven +0x20 version copy at 0x371869, but no single statically identified base accesses +0x20/+0x30/+0x40 as the reflected ServerConsumedPlayerInput cluster.",
        },
        "siblingActionCandidates": {
            "CreateBuildingItemAction": {"status": "UNSOLVED", "payloadSize": "0x0C", "consumerRvas": [], "versionFlow": "UNKNOWN", "selectedIndexUse": "UNKNOWN", "itemIdUse": "UNKNOWN"},
            "BuildingStockCycleAction": {"status": "UNSOLVED", "payloadSize": "0x14", "consumerRvas": [], "versionFlow": "UNKNOWN"},
            "structuralRequirement": "A payload-size coincidence is rejected; a sibling requires wrapper, VersionedData, and downstream/consumed-field evidence.",
        },
        "clientInputConnectedSearch": {
            "reflectedOffsets": {"inventory": "0x000", "buildingStockCycle": "0x0A4", "createBuildingItem": "0x1B0"},
            "multiFieldBaseFound": False,
            "status": "UNSOLVED",
            "reason": "No connected function establishes one base register with multiple reflected ClientPlayerInput offsets.",
        },
        "createBuildingEvidence": {"reflected": create.get("reflectedLayout"), "staticConclusion": create.get("staticConclusion"), "observerInstalled": False},
        "stockCycleEvidence": {"reflectedType": (client.get("reflectedLayouts") or {}).get("BuildingStockCycleAction"), "runtimeObserverInstalled": False},
        "rejectedCandidates": [
            {"candidate": "generic +0x00/+0x04/+0x08 structures", "status": "DISPROVEN", "reason": "Offset shape alone does not identify CreateBuildingItemAction."},
            {"candidate": "single +0x20 consumed-version write", "status": "INFERRED_ONLY", "reason": "No same-object +0x30/+0x40 validation."},
        ],
        "unresolved": ["dispatch wrapper producer/copy site", "wrapper allocation/lifetime", "generic versus inventory-specific wrapper", "CreateBuildingItemAction consumer", "BuildingStockCycleAction sibling consumer", "UiCreateBuildingItemEvent connection"],
        "observerDecision": {"install": False, "status": "FAIL_CLOSED", "reason": "Create-building consumer and owner transition are not strongly established; no runtime observer is justified."},
    }


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=root / "enshrouded.exe")
    parser.add_argument("--inventory-map", type=Path, default=Path(__file__).resolve().parents[2] / "bridge" / "inventory_transfer_static_map.json")
    parser.add_argument("--client-map", type=Path, default=Path(__file__).resolve().parents[2] / "bridge" / "client_player_input_static_map.json")
    parser.add_argument("--create-map", type=Path, default=Path(__file__).resolve().parents[2] / "bridge" / "create_building_item_static_map.json")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[2] / "bridge" / "semantic_action_dispatcher_static_map.json")
    args = parser.parse_args()
    image = Image(args.exe.resolve())
    inventory = json.loads(args.inventory_map.read_text(encoding="utf-8-sig"))
    client = json.loads(args.client_map.read_text(encoding="utf-8-sig"))
    create = json.loads(args.create_map.read_text(encoding="utf-8-sig"))
    report = build_report(image, inventory, client, create)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"dispatcherWrapper=INFERRED; createConsumer=UNSOLVED; output={args.output.resolve()}")


if __name__ == "__main__":
    main()
