#!/usr/bin/env python3
"""CODE-0007 offline ownership/lifetime map for 0x3E5480 -> 0x3ED1A0.

This tool consumes only the supported executable image.  It never opens a
process, installs a hook, writes an image, or emits deployment artifacts.
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


def row(ins: Any) -> dict[str, str]:
    return {"rva": hx(ins.address), "bytes": ins.bytes.hex(),
            "instruction": ins.mnemonic + ((" " + ins.op_str) if ins.op_str else "")}


def pdata_chunks(image: StaticImage, start: int) -> list[dict[str, str]]:
    """Return adjacent unwind chunks for a split function.

    The adjacent chunks are retained as separate evidence rows.  This is
    intentionally conservative: it only joins exact `.pdata` adjacency.
    """
    bounds = image.function_for(start)
    if not bounds:
        raise RuntimeError(f"no .pdata boundary for {hx(start)}")
    by_start = {b: (b, e, u) for b, e, u in image.functions}
    chunks: list[dict[str, str]] = []
    current_end = int(bounds["endRva"], 16)
    current_start = int(bounds["startRva"], 16)
    first = True
    while True:
        if first:
            b, e, u = by_start[current_start]
            first = False
        else:
            nxt = by_start.get(current_end)
            if nxt is None:
                break
            b, e, u = nxt
        chunks.append({"startRva": hx(b), "endRva": hx(e), "unwindInfoRva": hx(u)})
        current_end = e
    return chunks


def chained_disassembly(image: StaticImage, start: int) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    chunks = pdata_chunks(image, start)
    instructions: list[dict[str, str]] = []
    for chunk in chunks:
        b, e = int(chunk["startRva"], 16), int(chunk["endRva"], 16)
        instructions.extend(row(i) for i in image.disassemble(b, e))
    return chunks, instructions


def direct_call_sites(image: StaticImage, target: int) -> list[int]:
    """Find direct E8 rel32 calls in .text without broad semantic inference."""
    text = next((s for s in image.pe.sections if s.Name.rstrip(b"\0") == b".text"), None)
    if text is None:
        return []
    data = text.get_data()
    base = int(text.VirtualAddress)
    sites: list[int] = []
    for off in range(max(0, len(data) - 5)):
        if data[off] != 0xE8:
            continue
        destination = base + off + 5 + struct.unpack_from("<i", data, off + 1)[0]
        if destination == target:
            sites.append(base + off)
    return sites


def caller_contract(image: StaticImage, call_rva: int, target: int) -> dict[str, Any]:
    bounds, instructions = image.function_instructions(call_rva)
    idx = next((i for i, ins in enumerate(instructions) if ins.address == call_rva), None)
    if idx is None:
        return {"callRva": hx(call_rva), "targetRva": hx(target), "callerPdata": bounds,
                "argumentSetup": [], "returnUse": [], "status": "UNRESOLVED_CALLSITE"}
    # A short bounded window is enough to capture ABI setup and immediate RAX use.
    before = [row(ins) for ins in instructions[max(0, idx - 8):idx]]
    after = [row(ins) for ins in instructions[idx + 1:min(len(instructions), idx + 7)]]
    return {"callRva": hx(call_rva), "targetRva": hx(target), "callerPdata": bounds,
            "argumentSetup": before, "returnUse": after, "status": "PROVEN_DIRECT_CALL"}


def three_e5480_writes(image: StaticImage) -> list[dict[str, Any]]:
    bounds, instructions = image.function_instructions(0x3E5480)
    # Explicit instruction-backed writes through RAX, or RDX after RDX=RAX.
    writes: list[dict[str, Any]] = []
    source = {
        0x00: "RCX=[RSI] (input record pointer; in 0x3EB810 this is [acceptedElement+0x48])",
        0x08: "XMM0=[RSP+0x60] (derived by 0x8CD2C0)",
        0x10: "ECX=[RSP+0x68] (derived by 0x8CD2C0)",
        0x14: "XMM0=[RSP+0x6C] (derived by 0x8CD2C0)",
        0x1C: "ECX=[RSP+0x74] (derived by 0x8CD2C0)",
        0x20: "XMM0=[RSP+0x78] (derived by 0x8CD2C0)",
        0x28: "EAX=[RSP+0x80] (derived by 0x8CD2C0)",
        0x2C: "XMM0=[RSP+0x84] (derived by 0x8CD2C0)",
        0x34: "EAX=[RSP+0x8C] (derived by 0x8CD2C0)",
        0x38: "AL=[RSP+0x90] (derived by 0x8CD2C0)",
        0x3C: "EAX=[RSP+0x5C] (derived by 0x8CD2C0)",
    }
    widths = {0x00: 8, 0x08: 8, 0x10: 4, 0x14: 8, 0x1C: 4, 0x20: 8,
              0x28: 4, 0x2C: 8, 0x34: 4, 0x38: 1, 0x3C: 4}
    for ins in instructions:
        if ins.address < 0x3E5580 or ins.address > 0x3E55E6:
            continue
        if not ins.operands or ins.operands[0].type != 3:  # X86_OP_MEM
            continue
        mem = ins.operands[0].mem
        base = ins.reg_name(mem.base).lower()
        if base not in {"rax", "rdx"}:
            continue
        offset = mem.disp
        if offset not in widths:
            continue
        writes.append({"instructionRva": hx(ins.address), "widthBytes": widths[offset],
                       "destination": f"returnedRAX+{hx(offset)}",
                       "sourceExpression": source[offset],
                       "classification": "candidate-derived" if offset == 0 else "derived-transform-or-state",
                       "evidence": row(ins)})
    return writes


def build(exe: Path) -> dict[str, Any]:
    image = StaticImage(exe)
    if image.digest != SUPPORTED_SHA:
        raise RuntimeError("BUILD_MISMATCH")
    chunks_3e5480, dis_3e5480 = chained_disassembly(image, 0x3E5480)
    chunks_3ed1a0, dis_3ed1a0 = chained_disassembly(image, 0x3ED1A0)
    calls_3ed1a0 = [caller_contract(image, call, 0x3ED1A0)
                    for call in direct_call_sites(image, 0x3ED1A0)]
    calls_3e5480 = [caller_contract(image, call, 0x3E5480)
                    for call in direct_call_sites(image, 0x3E5480)]

    resolver_contract = {
        "callRva": "0x3E5578",
        "targetRva": "0x3ED1A0",
        "arguments": {
            "RCX": "[RDI+0xD8]",
            "RDX": "[RDI+0xE0]",
            "R8B": "5",
            "R9D": "EBX (saved incoming R8D of 0x3E5480)",
        },
        "returnUse": "RAX becomes destination record pointer; RDX=RAX at 0x3E5580",
    }
    returned_source = {
        "classification": "OWNER_ROOTED_CONTAINER_SLOT",
        "confidence": "PROVEN_STATIC_SHAPE_INFERRED_ALLOCATION_SEMANTICS",
        "ownerRoot": "incoming RCX to 0x3ED1A0, copied to RDI",
        "storageExpression": "[ownerRoot+0xA10] passed by address to 0x7AEDA0",
        "growthExpression": "[ownerRoot+0xA28] compared with [ownerRoot+0xA38]; 0x3EDDE0 called when equal",
        "strideExpression": "[ownerRoot+0xA3C] used to derive index",
        "secondaryBookkeepingRoot": "incoming RDX; [RDX+0x100]/[RDX+0x108] and RDX-relative index slots",
        "keyOrIndex": "index = (returnedRAX - [ownerRoot+0xA10]) / [ownerRoot+0xA3C], stored through RDX-relative slot",
        "notGlobalOrStack": "returned pointer comes from 0x7AEDA0 and is not an address of a local stack object or RIP-relative global",
        "allocationSemantics": "UNKNOWN whether 0x7AEDA0 reuses or allocates; 0x3EDDE0 is a growth path",
    }
    per_candidate = {
        "status": "OWNER_SHARED_STORAGE_PER_CALL",
        "ownerExpressionIn3EB810": "3EB810 RBP=its RCX input; 3E5480 receives RCX=RBP",
        "secondaryRootExpression": "3E5480 loads RDX=[ownerRoot+0xE0]",
        "candidateInputExpression": "3EB810 [RSP+0x90]=RBX=[acceptedElement+0x48]",
        "relationship": "same owner/secondary roots across one 0x3EB810 invocation; candidate-derived input varies per iteration",
        "separateSlotEvidence": "0x3ED1A0 obtains a record from ownerRoot+0xA10 and computes a storage index; separate allocation per call is inferred, not allocator-proven",
        "postLoopRetention": "no post-loop read of returned records is present in 0x3EB810; no last-candidate claim made",
    }
    convergence = {
        "previewOwner": "UNSOLVED",
        "placementCommit0x3E2CD0": "NO_CONNECTED_READER_PROVEN",
        "createBuildingItemAction": "NO_CONNECTED_READER_PROVEN",
        "cacheOwnerRSIPlusF0": "NO_CONNECTED_READER_PROVEN",
        "candidateSourceRSIPlus110": "NO_CONNECTED_READER_PROVEN",
        "frontier": "owner-rooted output returned by 0x3ED1A0 / fields written by 0x3E5480; downstream reader and lifetime remain unresolved",
    }
    return {
        "schemaVersion": 1,
        "codeId": "CODE-0007",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "deliveryMode": "OFFLINE_STATIC_ONLY",
        "build": {"revision": 1076226, "exeSha256": image.digest, "deployedDllSha256": DEPLOYED_DLL_SHA},
        "safety": {"processAccess": False, "debugApis": False, "runtimeHooksInstalled": False,
                   "writesGameMemory": False, "writesExecutable": False,
                   "currentSourceDesignationAuthorized": False},
        "installNow": False,
        "gameHookInstallAuthorized": False,
        "currentSourceDesignationAuthorized": False,
        "functions": {
            "0x3E5480": {"pdataChunks": chunks_3e5480, "disassembly": dis_3e5480,
                         "directCallers": calls_3e5480, "returnedPointerWrites": three_e5480_writes(image)},
            "0x3ED1A0": {"pdataChunks": chunks_3ed1a0, "disassembly": dis_3ed1a0,
                         "directCallers": calls_3ed1a0},
        },
        "callContract": resolver_contract,
        "returnedPointerSource": returned_source,
        "perCandidateDestination": per_candidate,
        "anchoredReadersWriters": {
            "instructionBackedWrites": "0x3E5583..0x3E55E6 through returned RAX/RDX",
            "postLoopReaders": "none proven in 0x3EB810; callers consume only AL success",
            "connectedReaders": [],
            "connectedWriters": ["0x3E5480 writes returned object fields", "0x3ED1A0 initializes returned slot"],
        },
        "lifetime": {"classification": "PERSISTENCE_UNRESOLVED", "evidence": [
            "storage is rooted in an incoming owner object and has explicit count/capacity/stride fields",
            "storage acquisition/growth is delegated to 0x7AEDA0/0x3EDDE0",
            "no post-loop reader or owner lifetime chain reaches preview/commit state",
        ]},
        "convergence": convergence,
        "contradictionsAndNegativeFindings": [
            "0x3EB810 loops all accepted candidates but does not retain a winner",
            "0x99F970 remains a one-record arithmetic consumer per CODE-0006",
            "a returned owner-rooted slot is not by itself proof of persistent preview authority",
            "no semantic type name is assigned to the owner, secondary root, or returned record",
        ],
        "observerEligibility": {"installNow": False, "gameHookInstallAuthorized": False,
                                "currentSourceDesignationAuthorized": False, "status": "NOT_AUTHORIZED",
                                "reason": "Static ownership/lifetime and downstream preview/commit readers are unresolved"},
        "analysisResult": "PARTIAL_STATIC",
        "nextInvestigation": "Trace only the owner-rooted output reader/caller boundary if an instruction-backed reader is identified; do not add a runtime hook based on this map.",
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
