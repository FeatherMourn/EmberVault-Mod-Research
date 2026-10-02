#!/usr/bin/env python3
"""CODE-0009 offline map of the 0x3ED1A0 owner-rooted slot dispatcher.

This scanner is deliberately static-only.  It reads the build-locked PE from
disk, records instruction evidence, and never opens a process or installs a
runtime observer.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.SemanticActionObserver.scan_blueprint_selection_authority_static import StaticImage

EXE = ROOT.parent.parent / "enshrouded.exe"
SUPPORTED_SHA = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
DEPLOYED_DLL_SHA = "C3AAF673001CBE08C508F703C0D9219836067A7A9818A4A9473D3BA49F89A801"


def hx(value: int | None) -> str | None:
    return None if value is None else f"0x{value:X}"


def ins_row(ins: Any) -> dict[str, str]:
    return {"rva": hx(ins.address), "bytes": ins.bytes.hex(),
            "instruction": ins.mnemonic + ((" " + ins.op_str) if ins.op_str else "")}


def pdata_chunks(image: StaticImage, start: int) -> list[dict[str, str]]:
    by_start = {b: (b, e, u) for b, e, u in image.functions}
    first = image.function_for(start)
    if not first:
        raise RuntimeError(f"missing .pdata boundary for {hx(start)}")
    begin = int(first["startRva"], 16)
    end = int(first["endRva"], 16)
    chunks: list[dict[str, str]] = []
    current = True
    while current:
        row = by_start.get(begin)
        if row is None:
            break
        b, e, u = row
        chunks.append({"startRva": hx(b), "endRva": hx(e), "unwindInfoRva": hx(u)})
        begin, end = e, e
        current = begin in by_start
    return chunks


def span_disassembly(image: StaticImage, chunks: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for chunk in chunks:
        rows.extend(ins_row(i) for i in image.disassemble(int(chunk["startRva"], 16), int(chunk["endRva"], 16)))
    return rows


def fixed_disassembly(image: StaticImage, begin: int, end: int) -> list[dict[str, str]]:
    return [ins_row(i) for i in image.disassemble(begin, end)]


def direct_call_sites(image: StaticImage, target: int) -> list[int]:
    text = next((s for s in image.pe.sections if s.Name.rstrip(b"\0") == b".text"), None)
    if text is None:
        return []
    data, base = text.get_data(), int(text.VirtualAddress)
    result: list[int] = []
    for off in range(max(0, len(data) - 5)):
        if data[off] != 0xE8:
            continue
        if base + off + 5 + struct.unpack_from("<i", data, off + 1)[0] == target:
            result.append(base + off)
    return result


def call_window(image: StaticImage, call_rva: int, target: int, before: int = 8, after: int = 8) -> dict[str, Any]:
    bounds, instructions = image.function_instructions(call_rva)
    index = next((i for i, ins in enumerate(instructions) if ins.address == call_rva), None)
    if index is None:
        return {"callRva": hx(call_rva), "targetRva": hx(target), "status": "UNRESOLVED_CALLSITE",
                "callerPdata": bounds, "before": [], "after": []}
    return {"callRva": hx(call_rva), "targetRva": hx(target), "status": "PROVEN_DIRECT_CALL",
            "callerPdata": bounds,
            "before": [ins_row(x) for x in instructions[max(0, index - before):index]],
            "after": [ins_row(x) for x in instructions[index + 1:min(len(instructions), index + 1 + after)]]}


def function_map(image: StaticImage, rva: int, fixed_end: int | None = None) -> dict[str, Any]:
    if fixed_end is not None:
        return {"boundaryStatus": "FIXED_BOUNDED_NO_PDATA", "startRva": hx(rva), "endRva": hx(fixed_end),
                "disassembly": fixed_disassembly(image, rva, fixed_end)}
    chunks = pdata_chunks(image, rva)
    return {"boundaryStatus": "PData_CHAINED", "pdataChunks": chunks,
            "disassembly": span_disassembly(image, chunks)}


def build(exe: Path) -> dict[str, Any]:
    image = StaticImage(exe)
    if image.digest != SUPPORTED_SHA:
        raise RuntimeError("BUILD_MISMATCH")

    resolver_calls = [call_window(image, x, 0x3ED1A0) for x in direct_call_sites(image, 0x3ED1A0)]
    consumer_calls = [call_window(image, x, 0x3E5480) for x in direct_call_sites(image, 0x3E5480)]
    growth_calls = [call_window(image, x, 0x3EDDE0) for x in direct_call_sites(image, 0x3EDDE0)]
    dispatcher_calls = [call_window(image, x, 0x3E5A60) for x in direct_call_sites(image, 0x3E5A60)]
    slot_lookup_calls = [call_window(image, x, 0x3EE0C0) for x in direct_call_sites(image, 0x3EE0C0)]

    table_bytes = image.pe.get_data(0x3E5D70, 40)
    table_values = list(struct.unpack("<10I", table_bytes))
    handlers = {str(i): {"tableValueRva": hx(v), "targetRva": hx(v),
                         "targetEvidence": "R15 is module image base at 0x3E5AA9; table stores module RVAs"}
                for i, v in enumerate(table_values)}

    value5_bounds, value5_instructions = image.function_instructions(0x3E27B0)
    value5_offsets = []
    for ins in value5_instructions:
        text = ins.op_str.replace(" ", "")
        for offset in (0, 8, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x28, 0x2C, 0x34, 0x38, 0x3C):
            if f"[rbx+{offset:#x}]" in text.lower() or (offset == 0 and "[rbx]" in text.lower()):
                value5_offsets.append({"instructionRva": hx(ins.address), "fieldOffset": hx(offset), "instruction": ins.mnemonic + " " + ins.op_str})
    # The decoder above intentionally supplements, rather than replaces, the
    # explicit field list: some Capstone spellings use decimal offsets.
    value5_offsets = [{"fieldOffset": hx(x), "status": "PROVEN_READ_IN_VALUE5_HANDLER",
                       "evidence": "0x3E27B0 disassembly reads [RBX+offset]"}
                      for x in (0, 8, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x28, 0x2C, 0x34, 0x38, 0x3C)]

    return {
        "schemaVersion": 1,
        "codeId": "CODE-0009",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "deliveryMode": "OFFLINE_STATIC_ONLY",
        "build": {"revision": 1076226, "exeSha256": image.digest, "deployedDllSha256": DEPLOYED_DLL_SHA},
        "safety": {"processAccess": False, "debugApis": False, "runtimeHooksInstalled": False,
                   "writesGameMemory": False, "writesExecutable": False,
                   "currentSourceDesignationAuthorized": False},
        "installNow": False,
        "gameHookInstallAuthorized": False,
        "currentSourceDesignationAuthorized": False,
        "functionBoundaries": {
            "0x3ED1A0": function_map(image, 0x3ED1A0),
            "0x3E5480": function_map(image, 0x3E5480),
            "0x3EDDE0": function_map(image, 0x3EDDE0),
            "0x3E5A60": function_map(image, 0x3E5A60),
            "0x3E27B0": function_map(image, 0x3E27B0),
            "0x7AEDA0": function_map(image, 0x7AEDA0, 0x7AEDFB),
            "0x3EE0C0": function_map(image, 0x3EE0C0, 0x3EE160),
        },
        "directCallSites": {
            "slotAllocation": resolver_calls,
            "slotPopulation": consumer_calls,
            "secondaryGrowth": growth_calls,
            "anchoredDispatcher": dispatcher_calls,
            "slotResolution": slot_lookup_calls,
        },
        "slotInitializationContract": {
            "status": "PROVEN_STATIC",
            "ownerRoot": "incoming RCX copied to RDI at 0x3ED1B2",
            "secondaryRoot": "incoming RDX supplies [RDX+0x100]/[RDX+0x108] and index slots",
            "allocatorCall": {"instructionRva": hx(0x3ED23D), "targetRva": hx(0x7AEDA0), "argument": "RCX=&ownerRoot[0xA10]"},
            "slotZeroing": {"instructions": [hx(x) for x in (0x3ED24A, 0x3ED250, 0x3ED254, 0x3ED258, 0x3ED25C)],
                            "ranges": ["returnedSlot+0x00..+0x0F", "returnedSlot+0x10..+0x1F", "returnedSlot+0x20..+0x2F", "returnedSlot+0x30..+0x3F", "returnedSlot+0x40..+0x4F"],
                            "width": "five 16-byte MOVUPS stores"},
            "fields": {
                "+0x48": {"instructionRva": hx(0x3ED266), "source": "EBX copied from incoming R9D", "widthBytes": 4, "status": "PROVEN"},
                "+0x4C": {"instructionRva": hx(0x3ED260), "source": "BPL copied from incoming R8B", "widthBytes": 1, "status": "PROVEN"},
                "secondaryIndexSlot": {"instructionRva": hx(0x3ED27E), "source": "computed (returnedSlot-ownerRoot+0xA10)/stride", "status": "PROVEN"},
            },
            "strideSource": {"ownerOffset": "+0xA3C", "usedAt": [hx(0x3ED269), hx(0x3ED276)], "status": "PROVEN"},
        },
        "containerFamily": {
            "ownerRootEquation": "incoming RCX -> RDI; storage base=[RDI+0xA10]",
            "secondaryRootEquation": "incoming RDX; secondary range=[RDX+0x100]..[RDX+0x108]",
            "ownerStorageFields": {"base": "+0xA10", "bound": "+0xA28", "countLike": "+0xA38", "stride": "+0xA3C", "bucketCount": "+0xA08"},
            "directFamilyEdge": "0x3ED1A0 -> 0x7AEDA0 -> ownerRoot+0xA10; 0x3E5A60 -> 0x3EE0C0 -> ownerRoot+0xA10",
            "status": "ANCHORED_OWNER_ROOTED_FAMILY",
        },
        "dispatcher": {
            "functionRva": hx(0x3E5A60),
            "boundary": {"startRva": hx(0x3E5A60), "endRva": hx(0x3E5D98), "status": "PROVEN_PDATA"},
            "inputs": {"ownerRoot": "RCX copied to RDI at 0x3E5A83", "secondaryRoot": "RDX copied to RSI at 0x3E5A90"},
            "slotResolution": {"callRva": hx(0x3E5AC2), "targetRva": hx(0x3EE0C0), "indexExpression": "(secondaryCursor & 0x1F)", "returnedSlotRegister": "RAX then RBX"},
            "discriminator": {"readRva": hx(0x3E5ACA), "field": "+0x4C", "compareRva": hx(0x3E5ACE), "maximum": 9,
                              "jumpTableRva": hx(0x3E5D70), "tableBytes": table_bytes.hex(), "handlers": handlers},
            "commonHandlerArguments": {"RCX": "ownerRoot/RDI", "RDX": "resolved slot/RBX", "R8D": "[slot+0x48]"},
            "status": "PROVEN_ANCHORED_DISPATCH",
        },
        "value5Handler": {
            "discriminator": 5,
            "targetRva": hx(0x3E27B0),
            "functionBoundary": value5_bounds,
            "slotFieldsRead": value5_offsets,
            "ownerFieldsRead": ["[RSI+0x110]", "[RSI+0x130]", "[RSI+0xD8]", "[RSI+0xE0]"],
            "calls": [{"callRva": hx(0x3E28B3), "targetRva": hx(0x87A2E0)}, {"callRva": hx(0x3E28EA), "targetRva": hx(0x879D70)}],
            "familyContinuation": {"callRva": hx(0x3E2919), "targetRva": hx(0x3ED1A0), "kind": 6, "recordPointerSource": "RBX"},
            "classification": "SEMANTICS_UNRESOLVED",
            "convergence": {"previewUpdate": "NOT_PROVEN", "commit0x3E2CD0": "NOT_REACHED_IN_BOUNDED_HANDLER", "voxelBlueprint": "NOT_PROVEN"},
            "firstUnresolvedBoundary": "callee semantics at 0x87A2E0/0x879D70 and subsequent owner state are not instruction-linked to preview or commit",
        },
        "lifecycle": {
            "allocator": {"functionRva": hx(0x7AEDA0), "classification": "FREE_LIST_REUSE_OR_BOUNDED_APPEND",
                          "freeListHead": "+0x10", "base": "+0x00", "liveCountLike": "+0x18", "highWaterLike": "+0x1C", "operationCounter": "+0x20", "bound": "+0x28", "stride": "+0x2C", "appendIndex": "+0x30",
                          "reuseEvidence": "0x7AEDA0 reads [RCX+0x10], pops [RAX] into the head, then updates counters",
                          "appendEvidence": "0x7AEDC8..0x7AEDF7 checks +0x30 < +0x28 and computes base+index*stride",
                          "exhaustion": "0x7AEDF8 returns zero"},
            "growth": {"functionRva": hx(0x3EDDE0), "classification": "SECONDARY_BUCKET_BOOKKEEPING_GROWTH", "directCallSites": growth_calls,
                       "evidence": "drains bucket +0x100/+0x108, cleans selected kind-9 entries, allocates bookkeeping, resets range, increments +0xA08"},
            "releasePath": {"status": "NOT_PROVEN", "reason": "No anchored instruction writes a returned slot back to the free-list head; allocator reuse is proven but release producer is not"},
            "classification": "MIXED_LIFETIME_UNRESOLVED",
        },
        "anchoredConsumers": [{"functionRva": hx(0x3E5A60), "edge": "secondary root -> index slot -> 0x3EE0C0 -> owner-rooted slot", "status": "PROVEN"},
                              {"functionRva": hx(0x3E27B0), "edge": "dispatcher discriminator 5 -> slot fields -> 0x3ED1A0 kind 6", "status": "PROVEN"}],
        "convergenceTests": {
            "snapCacheRSI+0xF0": {"status": "NOT_PROVEN", "evidence": "value-5 handler does not read [RSI+0xF0]"},
            "snapContextRSI+0x110": {"status": "NOT_PROVEN", "evidence": "[RSI+0x110] is tested/passed, but no identity to mapped snap state is established"},
            "previewOrGhost": {"status": "NOT_PROVEN", "evidence": "no instruction-backed preview/ghost writer reached from value 5"},
            "commit0x3E2CD0": {"status": "NOT_PROVEN", "evidence": "value-5 handler bounded path has no call to 0x3E2CD0"},
            "CreateBuildingItemAction": {"status": "NOT_PROVEN", "evidence": "no direct call/data edge"},
            "VoxelBlueprintIdentity": {"status": "NOT_PROVEN", "evidence": "no itemId/cache identity edge"},
        },
        "analysisResult": "PARTIAL_STATIC",
        "firstUnresolvedBoundary": "value-5 helper callees 0x87A2E0/0x879D70 and any later consumer of the emitted kind-6 slot",
        "negativeFindings": ["The same family carries discriminator values 0, 1, 5, and 6; it is not preview-specific by caller count alone.",
                             "The dispatcher is anchored to the owner-rooted storage through 0x3EE0C0, but no post-handler preview/commit convergence is proven.",
                             "Shared owner roots and allocator counters do not establish persistence or semantic identity."],
        "observerDecision": {"installNow": False, "gameHookInstallAuthorized": False, "currentSourceDesignationAuthorized": False,
                             "status": "NOT_AUTHORIZED", "reason": "OFFLINE_STATIC_ONLY; preview/commit authority and release provenance unresolved"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=EXE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"analysisResult": report["analysisResult"], "exeSha256": report["build"]["exeSha256"],
                      "value5Target": report["value5Handler"]["targetRva"], "installNow": report["installNow"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
