#!/usr/bin/env python3
"""CODE-0008 offline map of the 0x3ED1A0 owner-rooted container family."""
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
    bounds = image.function_for(start)
    if not bounds:
        raise RuntimeError(f"missing .pdata boundary for {hx(start)}")
    current = int(bounds["startRva"], 16)
    end = int(bounds["endRva"], 16)
    chunks: list[dict[str, str]] = []
    first = True
    while True:
        if first:
            b, e, u = by_start[current]
            first = False
        else:
            nxt = by_start.get(end)
            if nxt is None:
                break
            b, e, u = nxt
        chunks.append({"startRva": hx(b), "endRva": hx(e), "unwindInfoRva": hx(u)})
        end = e
    return chunks


def span_disassembly(image: StaticImage, chunks: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for chunk in chunks:
        begin, end = int(chunk["startRva"], 16), int(chunk["endRva"], 16)
        rows.extend(ins_row(i) for i in image.disassemble(begin, end))
    return rows


def fixed_disassembly(image: StaticImage, begin: int, end: int) -> list[dict[str, str]]:
    return [ins_row(i) for i in image.disassemble(begin, end)]


def direct_call_sites(image: StaticImage, target: int) -> list[int]:
    text = next((s for s in image.pe.sections if s.Name.rstrip(b"\0") == b".text"), None)
    if text is None:
        return []
    data, base = text.get_data(), int(text.VirtualAddress)
    sites: list[int] = []
    for off in range(max(0, len(data) - 5)):
        if data[off] != 0xE8:
            continue
        if base + off + 5 + struct.unpack_from("<i", data, off + 1)[0] == target:
            sites.append(base + off)
    return sites


def call_window(image: StaticImage, call_rva: int, target: int) -> dict[str, Any]:
    bounds, instructions = image.function_instructions(call_rva)
    idx = next((i for i, item in enumerate(instructions) if item.address == call_rva), None)
    if idx is None:
        return {"callRva": hx(call_rva), "targetRva": hx(target), "callerPdata": bounds,
                "status": "UNRESOLVED_CALLSITE", "before": [], "after": []}
    return {"callRva": hx(call_rva), "targetRva": hx(target), "callerPdata": bounds,
            "status": "PROVEN_DIRECT_CALL",
            "before": [ins_row(i) for i in instructions[max(0, idx - 8):idx]],
            "after": [ins_row(i) for i in instructions[idx + 1:min(len(instructions), idx + 7)]]}


def resolver_argument_contract(call_rva: int) -> dict[str, Any]:
    contracts = {
        0x3E262B: {"RCX": "[R14+0xD8]", "RDX": "[R14+0xE0]", "R8B": "1", "R9D": "EBX", "returnUse": "writes [RAX+0x00] and [RAX+0x04]"},
        0x3E2919: {"RCX": "[RSI+0xD8]", "RDX": "[RSI+0xE0]", "R8B": "6", "R9D": "EDI", "returnUse": "writes [RAX+0x00]"},
        0x3E52BD: {"RCX": "[R14+0xD8]", "RDX": "[R14+0xE0]", "R8B": "0", "R9D": "EDI", "returnUse": "copies vector/local fields through returned RAX"},
        0x3E5578: {"RCX": "[RDI+0xD8]", "RDX": "[RDI+0xE0]", "R8B": "5", "R9D": "EBX", "returnUse": "RDX=RAX at 0x3E5580; writes 11 returned-record fields"},
    }
    return contracts.get(call_rva, {"RCX": "UNKNOWN", "RDX": "UNKNOWN", "R8B": "UNKNOWN", "R9D": "UNKNOWN", "returnUse": "UNKNOWN"})


def returned_writes() -> list[dict[str, Any]]:
    rows = [
        (0x3E5583, 8, "+0x00", "RCX=[RSI]", "candidate-derived pointer on 0x3EB810 path"),
        (0x3E558C, 8, "+0x08", "XMM0=[RSP+0x60]", "derived transform/state"),
        (0x3E5595, 4, "+0x10", "ECX=[RSP+0x68]", "derived transform/state"),
        (0x3E559E, 8, "+0x14", "XMM0=[RSP+0x6C]", "derived transform/state"),
        (0x3E55A7, 4, "+0x1C", "ECX=[RSP+0x74]", "derived transform/state"),
        (0x3E55B0, 8, "+0x20", "XMM0=[RSP+0x78]", "derived transform/state"),
        (0x3E55BC, 4, "returnedRAX+0x28", "EAX=[RSP+0x80]", "derived transform/state"),
        (0x3E55C8, 8, "returnedRAX+0x2C", "XMM0=[RSP+0x84]", "derived transform/state"),
        (0x3E55D4, 4, "returnedRAX+0x34", "EAX=[RSP+0x8C]", "derived transform/state"),
        (0x3E55DF, 1, "returnedRAX+0x38", "AL=[RSP+0x90]", "derived transform/state"),
        (0x3E55E6, 4, "returnedRAX+0x3C", "EAX=[RSP+0x5C]", "derived transform/state"),
    ]
    return [{"instructionRva": hx(rva), "widthBytes": width, "destination": dest,
             "sourceExpression": src, "classification": cls} for rva, width, dest, src, cls in rows]


def build(exe: Path) -> dict[str, Any]:
    image = StaticImage(exe)
    if image.digest != SUPPORTED_SHA:
        raise RuntimeError("BUILD_MISMATCH")
    chunks_3e5480 = pdata_chunks(image, 0x3E5480)
    chunks_3ed1a0 = pdata_chunks(image, 0x3ED1A0)
    chunks_3edde0 = pdata_chunks(image, 0x3EDDE0)
    resolver_calls = []
    for call in direct_call_sites(image, 0x3ED1A0):
        item = call_window(image, call, 0x3ED1A0)
        item["argumentProvenance"] = resolver_argument_contract(call)
        resolver_calls.append(item)
    owner_calls = [call_window(image, call, 0x3E5480) for call in direct_call_sites(image, 0x3E5480)]
    allocator_chunks = [{"startRva": hx(0x7AEDA0), "endRva": hx(0x7AEDFB), "unwindInfoRva": None}]
    allocator_disassembly = fixed_disassembly(image, 0x7AEDA0, 0x7AEDFB)
    growth_calls = [call_window(image, call, 0x3EDDE0) for call in direct_call_sites(image, 0x3EDDE0)]
    return {
        "schemaVersion": 1,
        "codeId": "CODE-0008",
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
            "0x3E5480": {"pdataChunks": chunks_3e5480, "disassembly": span_disassembly(image, chunks_3e5480)},
            "0x3ED1A0": {"pdataChunks": chunks_3ed1a0, "disassembly": span_disassembly(image, chunks_3ed1a0)},
            "0x7AEDA0": {"pdataChunks": allocator_chunks, "disassembly": allocator_disassembly, "boundaryStatus": "FIXED_RET_AND_INT3_BOUNDARY_NO_PDATA"},
            "0x3EDDE0": {"pdataChunks": chunks_3edde0, "disassembly": span_disassembly(image, chunks_3edde0)},
        },
        "directCallSites": {"resolver3ED1A0": resolver_calls, "consumer3E5480": owner_calls, "growth3EDDE0": growth_calls},
        "argumentContracts": resolver_calls,
        "returnedPointerSource": {"classification": "OWNER_ROOTED_CONTAINER_SLOT", "evidence": "0x3ED1A0 passes ownerRoot+0xA10 to 0x7AEDA0 and returns its RAX"},
        "containerFamily": {
            "ownerRootEquation": "incoming RCX to 0x3ED1A0 -> RDI (ownerRoot)",
            "secondaryRootEquation": "incoming RDX to 0x3ED1A0; [RDX+0x100]/[RDX+0x108] and RDX-relative index slots",
            "ownerStorage": {"baseField": "+0xA10", "countLikeFields": ["+0xA28", "+0xA38"], "strideField": "+0xA3C"},
            "recordInitialization": ["returnedRAX+0x00..0x40 cleared", "returnedRAX+0x48 = R9D", "returnedRAX+0x4C = R8B"],
            "r8bValues": {"0x3E262B": 1, "0x3E2919": 6, "0x3E52BD": 0, "0x3E5578": 5},
            "r8bRole": "DISCRIMINATOR_OR_RECORD_KIND_INFERRED; semantic name unresolved",
            "r9dRole": "SCALAR_COPIED_TO_RETURNED_PLUS_0x48; index/key/generation semantics unresolved",
        },
        "allocator7AEDA0": {
            "classification": "FREE_LIST_REUSE_OR_BOUNDED_APPEND",
            "confidence": "PROVEN_STATIC_BEHAVIOR",
            "controlBlockFields": {
                "+0x00": "base storage pointer used for append address",
                "+0x10": "free-list head pointer; popped when nonzero",
                "+0x18": "32-bit count-like field incremented on allocation/reuse",
                "+0x1C": "32-bit high-water/count-like field adjusted with +0x18",
                "+0x20": "64-bit operation counter incremented",
                "+0x28": "32-bit bound checked against +0x30",
                "+0x2C": "32-bit element stride used for append address",
                "+0x30": "32-bit next-index/count-like field incremented for append",
            },
            "reusePath": "[RCX+0x10] != 0 -> RAX=[RCX+0x10], next free pointer=[RAX], update counters",
            "appendPath": "[RCX+0x10] == 0 and [RCX+0x30] < [RCX+0x28] -> base+[index*stride], increment +0x30",
            "notFoundOrExhausted": "returns RAX=0 when append bound is reached",
        },
        "growth3EDDE0": {
            "classification": "BUCKET_AND_BOOKKEEPING_GROWTH",
            "confidence": "PROVEN_STATIC_BEHAVIOR_FOR_CONNECTED_CALL",
            "connectedCall": "0x3ED223 from 0x3ED1A0 after [ownerRoot+0xA28] == [ownerRoot+0xA38]",
            "behavior": ["selects bucket from ownerRoot+[ownerRoot+0xA08]*0x200-derived offset", "drains/cleans kind-9 entries through 0x7C4180 and 0x7C3EA0", "allocates new bucket bookkeeping through 0x263470", "zeros bucket +0x100/+0x108 and increments ownerRoot+0xA08"],
            "directCallSites": growth_calls,
            "recordArrayCapacityChange": "not directly proven; this helper grows the secondary bucket/bookkeeping family",
        },
        "returnedSlotWrites": returned_writes(),
        "perCandidateRelationship": {
            "ownerRoot": "shared across one 0x3EB810 invocation (RBP=consumer RCX; 0x3E5480 receives RCX=RBP)",
            "candidateInput": "[RSP+0x90]=[acceptedElement+0x48] on 0x3EB810 path",
            "destination": "same owner-rooted storage service, with reuse/append slot selection per call",
            "status": "OWNER_SHARED_STORAGE_REUSE_OR_APPEND",
            "postLoopRead": "none in 0x3EB810; only AL success is consumed",
        },
        "anchoredReadersWriters": {
            "writers": ["0x3ED1A0 initializes returned slot and bookkeeping", "0x3E5480 writes returned slot fields", "0x3EDDE0 resets/grows secondary buckets"],
            "readers": ["0x7AEDA0 reads/writes allocator control fields", "0x3ED1A0 reads owner/secondary metadata"],
            "postLoopReaders": [],
            "previewOrCommitReaders": [],
            "readerStatus": "NO_CONNECTED_READER_PROVEN",
        },
        "lifetime": {"classification": "PERSISTENCE_UNRESOLVED", "evidence": ["owner-rooted storage has explicit counters/stride and growth", "allocator may reuse or append slots", "no owner lifetime chain or connected post-loop reader reaches preview/commit"]},
        "convergence": {"previewOwner": "UNSOLVED", "placementCommit0x3E2CD0": "NO_CONNECTED_READER_PROVEN", "snapRSIPlusF0": "NO_CONNECTED_READER_PROVEN", "snapRSIPlus110": "NO_CONNECTED_READER_PROVEN", "createBuildingItemAction": "NO_CONNECTED_READER_PROVEN", "voxelBlueprintIdentity": "NO_CONNECTED_READER_PROVEN", "status": "UNRESOLVED"},
        "contradictionsAndNegativeFindings": ["Multiple callers use discriminator values 0,1,5,6, so 0x3ED1A0 is not proven preview-specific.", "R9D is copied to returned +0x48 but no key/index/generation semantics are established.", "A shared owner root and reusable storage do not prove persistent preview authority.", "No post-loop winner retention is present in 0x3EB810."],
        "observerDecision": {"installNow": False, "gameHookInstallAuthorized": False, "currentSourceDesignationAuthorized": False, "status": "NOT_AUTHORIZED", "reason": "Static readers, lifetime, and preview/commit convergence remain unresolved"},
        "analysisResult": "PARTIAL_STATIC",
        "nextInvestigation": "Follow only an instruction-backed reader of the owner-rooted returned-slot fields; do not install a runtime hook from this map.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", type=Path, default=EXE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = build(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
