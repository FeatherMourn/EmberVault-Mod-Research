"""Bounded offline static map for CreateBuildingItemAction.

This scanner never opens a process and never writes game files.  It uses the
on-disk PE, its unwind function table, and decoded instructions to separate
metadata references from executable consumers.  A complete-field match is a
candidate only; it is not promoted to a hook site without data-flow evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import defaultdict
from pathlib import Path
from typing import Any

import capstone
import pefile


GAME_SHA = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
ACTION_STRINGS = {
    "createBuildingItemAction": "createBuildingItemAction",
    "buildingStockCycleAction": "buildingStockCycleAction",
    "CreateBuildingItemAction": "CreateBuildingItemAction",
    "UiCreateBuildingItemEvent": "UiCreateBuildingItemEvent",
    "consumedCreateBuildingItemAction": "consumedCreateBuildingItemAction",
    "ServerConsumedPlayerInput": "ServerConsumedPlayerInput",
    "selectedIndex": "selectedIndex",
    "versionData": "versionData",
}


def hexrva(value: int | None) -> str | None:
    return None if value is None else f"0x{value:X}"


def find_string_rvas(pe: pefile.PE, blob: bytes) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for label, text in ACTION_STRINGS.items():
        needle = text.encode("ascii")
        rvas: list[int] = []
        start = 0
        while True:
            offset = blob.find(needle, start)
            if offset < 0:
                break
            try:
                rvas.append(pe.get_rva_from_offset(offset))
            except pefile.PEFormatError:
                pass
            start = offset + 1
        result[label] = rvas
    return result


def section(pe: pefile.PE, prefix: bytes):
    for value in pe.sections:
        if value.Name.startswith(prefix):
            return value
    raise RuntimeError(f"missing PE section {prefix!r}")


def pointer_refs(pe: pefile.PE, target_rvas: set[int]) -> dict[str, list[str]]:
    image_base = pe.OPTIONAL_HEADER.ImageBase
    result: dict[str, list[str]] = defaultdict(list)
    for sec in pe.sections:
        data = sec.get_data()
        for off in range(0, max(0, len(data) - 7), 8):
            value = struct.unpack_from("<Q", data, off)[0]
            if value < image_base:
                continue
            rva = value - image_base
            if rva in target_rvas:
                result[hexrva(rva)].append(hexrva(sec.VirtualAddress + off))
    return dict(result)


def direct_rip_xrefs(pe: pefile.PE, target_rvas: set[int]) -> dict[str, list[dict[str, str]]]:
    image_base = pe.OPTIONAL_HEADER.ImageBase
    text = section(pe, b".text")
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    result: dict[str, list[dict[str, str]]] = defaultdict(list)
    for ins in md.disasm(text.get_data(), image_base + text.VirtualAddress):
        for operand in ins.operands:
            if operand.type != capstone.x86.X86_OP_MEM:
                continue
            if operand.mem.base != capstone.x86.X86_REG_RIP:
                continue
            target = ins.address + ins.size + operand.mem.disp - image_base
            if target in target_rvas:
                result[hexrva(target)].append(
                    {"instructionRva": hexrva(ins.address - image_base),
                     "instruction": f"{ins.mnemonic} {ins.op_str}"}
                )
    return dict(result)


def unwind_functions(pe: pefile.PE) -> list[tuple[int, int, int]]:
    pdata = section(pe, b".pdata").get_data()
    functions: list[tuple[int, int, int]] = []
    for offset in range(0, len(pdata) - 11, 12):
        begin, end, unwind = struct.unpack_from("<III", pdata, offset)
        if 0x1000 <= begin < end <= pe.OPTIONAL_HEADER.SizeOfImage:
            functions.append((begin, end, unwind))
    return functions


def operand_access(ins) -> list[tuple[int, str, bool]]:
    accesses: list[tuple[int, str, bool]] = []
    for operand in ins.operands:
        if operand.type != capstone.x86.X86_OP_MEM:
            continue
        base = operand.mem.base
        if base == 0:
            continue
        if operand.mem.disp in (0, 4, 8):
            name = ins.reg_name(base).upper()
            writes = ins.id in {
                capstone.x86.X86_INS_MOV,
                capstone.x86.X86_INS_MOVABS,
                capstone.x86.X86_INS_XCHG,
                capstone.x86.X86_INS_STOSB,
                capstone.x86.X86_INS_STOSW,
                capstone.x86.X86_INS_STOSD,
                capstone.x86.X86_INS_STOSQ,
            } and operand == ins.operands[0]
            accesses.append((operand.mem.disp, name, writes))
    return accesses


def candidate_functions(pe: pefile.PE, limit: int = 96) -> list[dict[str, Any]]:
    image_base = pe.OPTIONAL_HEADER.ImageBase
    text = section(pe, b".text")
    text_bytes = text.get_data()
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    result: list[dict[str, Any]] = []
    for begin, end, unwind in unwind_functions(pe):
        raw_begin = begin - text.VirtualAddress
        raw_end = end - text.VirtualAddress
        if raw_begin < 0 or raw_end <= raw_begin or raw_end > len(text_bytes):
            continue
        instructions = list(md.disasm(text_bytes[raw_begin:raw_end], image_base + begin))
        if not instructions:
            continue
        by_base: dict[str, dict[int, list[Any]]] = defaultdict(lambda: defaultdict(list))
        for ins in instructions:
            for offset, base, writes in operand_access(ins):
                by_base[base][offset].append(ins)
        for base, offsets in by_base.items():
            if not {0, 4, 8}.issubset(offsets):
                continue
            # Prefer a genuinely local three-field use over unrelated accesses
            # scattered through a large dispatcher.
            all_ins = [ins for values in offsets.values() for ins in values]
            first = min(ins.address for ins in all_ins)
            last = max(ins.address for ins in all_ins)
            local = last - first <= 0x180
            calls = [ins for ins in instructions if ins.mnemonic == "call"]
            call_targets = []
            for ins in calls:
                if ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
                    call_targets.append(hexrva(ins.operands[0].imm - image_base))
            evidence = []
            for offset in (0, 4, 8):
                evidence.extend(
                    {"offset": f"+0x{offset:X}",
                     "instructionRva": hexrva(ins.address - image_base),
                     "instruction": f"{ins.mnemonic} {ins.op_str}",
                     "write": writes}
                    for ins in offsets[offset]
                    for writes in [any(a[2] for a in operand_access(ins) if a[0] == offset and a[1] == base)]
                )
            score = (100 if local else 0) + min(len(calls), 10) + min(len(all_ins), 20)
            result.append({"functionStartRva": hexrva(begin), "functionEndRva": hexrva(end),
                           "unwindInfoRva": hexrva(unwind), "baseRegister": base,
                           "localThreeFieldWindow": local, "score": score,
                           "confidence": "UNRESOLVED_GENERIC_SHAPE",
                           "actionPointerProvenance": "UNKNOWN",
                           "consumedVersionFlow": "UNKNOWN",
                           "buildingPlaceDownstreamEdge": "UNKNOWN",
                           "fieldAccesses": evidence[:24],
                           "directCallTargets": call_targets[:32]})
    result.sort(key=lambda row: (-row["score"], int(row["functionStartRva"], 16)))
    return result[:limit]


def build_map(executable: Path) -> dict[str, Any]:
    blob = executable.read_bytes()
    pe = pefile.PE(data=blob, fast_load=True)
    sha = hashlib.sha256(blob).hexdigest().upper()
    strings = find_string_rvas(pe, blob)
    target_rvas = {rva for values in strings.values() for rva in values}
    refs = pointer_refs(pe, target_rvas)
    rip = direct_rip_xrefs(pe, target_rvas)
    candidates = candidate_functions(pe)
    shape_candidates = [row for row in candidates if row["localThreeFieldWindow"]]
    known_calls = {"buildingPlaceEventHelper": "0x3EBB70",
                   "buildingPlaceCallSite": "0x3E3505",
                   "placementConsumerBegin": "0x3E40D0",
                   "placementConsumerEnd": "0x3E4838"}
    return {
        "schemaVersion": 1,
        "tool": "scan_create_building_item_static.py",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "executable": {"path": str(executable), "sha256": sha,
                        "supportedSha256": GAME_SHA,
                        "fingerprintMatches": sha == GAME_SHA,
                        "imageBase": hexrva(pe.OPTIONAL_HEADER.ImageBase),
                        "imageSize": hexrva(pe.OPTIONAL_HEADER.SizeOfImage),
                        "timeDateStamp": hexrva(pe.FILE_HEADER.TimeDateStamp)},
        "reflectedLayout": {
            "type": "keen::ecs::CreateBuildingItemAction", "size": "0x0C",
            "alignment": 4,
            "fields": [{"name": "versionData", "offset": "0x00", "width": 4, "status": "PROVEN_STATIC_BUILD_1076226"},
                       {"name": "selectedIndex", "offset": "0x04", "width": 4, "status": "PROVEN_STATIC_BUILD_1076226"},
                       {"name": "itemId", "offset": "0x08", "width": 4, "status": "PROVEN_STATIC_BUILD_1076226"}]},
        "metadata": {"stringRvas": {k: [hexrva(x) for x in v] for k, v in strings.items()},
                      "pointerReferences": refs, "directExecutableRipXrefs": rip,
                      "interpretation": "String and data-table references are metadata evidence, not execution sites."},
        "knownPlacementAnchors": known_calls,
        "knownPlacementDataFlow": {
            "status": "PROVEN_DOWNSTREAM_ITEM_PATH; ACTION_LINK_UNSOLVED",
            "instructions": [
                {"rva": "0x3E2D00", "instruction": "mov edx, r8d", "meaning": "copies the placement-path item argument to EDX"},
                {"rva": "0x3E2D08", "instruction": "mov ebx, r8d", "meaning": "retains the same value in a nonvolatile temporary"},
                {"rva": "0x3E2D45", "instruction": "mov ecx, ebx", "meaning": "passes the retained value as resolver key"},
                {"rva": "0x3E2D47", "instruction": "call 0xCB4B50", "meaning": "Item-ID keyed placement resolver"},
                {"rva": "0x3E2D4C", "instruction": "mov r12, rax", "meaning": "retains returned record"},
                {"rva": "0x3E34E1", "instruction": "mov eax, dword ptr [r12]", "meaning": "reads resolved record item ID"},
                {"rva": "0x3E34F1", "instruction": "mov dword ptr [rsp+0x20], eax", "meaning": "stores fifth BuildingPlaceEvent argument"},
                {"rva": "0x3E3505", "instruction": "call 0x3EBB70", "meaning": "proven BuildingPlaceEvent call site"},
            ],
            "conclusion": "The normal placement function has a proven item-ID argument path, but no static edge currently proves that keen::ecs::CreateBuildingItemAction is the source of R8D or that its reflected 0x0C payload is consumed here.",
        },
        "completeFieldConsumerCandidates": candidates,
        "staticConclusion": {
            "consumerFound": False,
            "consumerHookEligible": False,
            "status": "UNSOLVED",
            "reason": "No candidate is promoted: complete-field shape matches are generic object accesses and no candidate has validated action provenance, consumed-version flow, or a call/data path into the proven BuildingPlaceEvent chain.",
            "completeFieldShapeCandidateCount": len(shape_candidates),
            "actionQualifiedCandidateCount": 0,
            "rejectedCandidates": [{"functionStartRva": row["functionStartRva"], "reason": "generic three-offset object access; action identity and downstream path unproven"} for row in shape_candidates[:24]],
        },
        "observerDecision": {"install": False, "failClosed": True,
                             "reason": "Static consumer boundary unresolved; no native detour or runtime observer is enabled in v0.21."},
        "nextEvidence": ["Recover an action-specific dispatch/data-flow edge from metadata registration to a complete-field consumer.",
                         "Validate the action pointer and calling convention at a uniquely identified site before any hook proposal.",
                         "Only then correlate action itemId/selectedIndex/version with BuildingPlaceEvent records."],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"))
    parser.add_argument("--output", type=Path, default=Path("bridge/create_building_item_static_map.json"))
    args = parser.parse_args()
    report = build_map(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} consumerHookEligible={report['observerDecision']['install']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
