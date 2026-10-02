"""Bounded, offline BuildingPlaceEvent -> transform/snap static map.

This scanner deliberately follows only the already proven placement anchors.  It
does not attach to Enshrouded, inspect process memory, install a detour, or
invoke any game code.  The output is evidence (decoded instructions and call
edges), not semantic guesses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import capstone
import pefile


SUPPORTED_SHA256 = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
EXE_DEFAULT = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe")

ANCHORS = {
    "buildingPlaceEvent": 0x3EBB70,
    "buildingPlaceCall": 0x3E3505,
    "placementFunction": 0x3E2CD0,
    "placementConsumer": 0x3E40D0,
    "upstreamPlacementCaller": 0x2807D5,
    "blueprintCacheLookup": 0xCA90E0,
    "candidateFilter": 0x3E79C0,
    "candidateRecordDecoder": 0x3E74B0,
}

RANGES = {
    "placementFunction": (0x3E2CD0, 0x3E354E),
    "placementConsumer": (0x3E40D0, 0x3E4838),
    "upstreamPlacementCaller": (0x2807D5, 0x2810E8),
    "candidateFilter": (0x3E79C0, 0x3E7DED),
    "candidateRecordDecoder": (0x3E74B0, 0x3E771F),
    "buildingPlaceEvent": (0x3EBB70, 0x3EBCA5),
}


def hx(value: int | None) -> str | None:
    return None if value is None else f"0x{value:X}"


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def pdata_functions(pe: pefile.PE) -> list[tuple[int, int, int]]:
    sec = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".pdata")
    raw = sec.get_data()
    out = []
    for off in range(0, len(raw) - 11, 12):
        begin, end, unwind = struct.unpack_from("<III", raw, off)
        if begin < end:
            out.append((begin, end, unwind))
    return out


def boundaries(pe: pefile.PE, targets: list[int]) -> dict[str, dict[str, str | None]]:
    rows = pdata_functions(pe)
    out = {}
    for name, target in [(n, v) for n, v in ANCHORS.items()]:
        matches = [(b, e, u) for b, e, u in rows if b <= target < e]
        if not matches:
            out[name] = {"startRva": None, "endRva": None, "unwindInfoRva": None, "status": "UNKNOWN"}
            continue
        b, e, u = matches[0]
        out[name] = {"startRva": hx(b), "endRva": hx(e), "unwindInfoRva": hx(u), "status": "PROVEN_STATIC_BUILD_1076226"}
    return out


def disasm(pe: pefile.PE, start: int, end: int) -> list[dict]:
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    rows = []
    for ins in md.disasm(pe.get_data(start, max(0, end - start)), start):
        rows.append({"rva": hx(ins.address), "instruction": f"{ins.mnemonic} {ins.op_str}".strip(), "bytes": ins.bytes.hex(" ").upper()})
    return rows


def direct_calls(pe: pefile.PE, start: int, end: int) -> list[dict]:
    rows = []
    for ins in disasm(pe, start, end):
        text = ins["instruction"]
        if not text.startswith("call 0x"):
            continue
        try:
            target = int(text.split("0x", 1)[1], 16)
        except ValueError:
            continue
        rows.append({"callRva": ins["rva"], "targetRva": hx(target), "bytes": ins["bytes"]})
    return rows


def call_xrefs(pe: pefile.PE, target: int) -> list[dict]:
    sec = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".text")
    raw = sec.get_data()
    base = sec.VirtualAddress
    result = []
    pos = raw.find(b"\xE8")
    while pos >= 0 and pos + 5 <= len(raw):
        src = base + pos
        dst = src + 5 + struct.unpack_from("<i", raw, pos + 1)[0]
        if dst == target:
            result.append({"callRva": hx(src), "returnRva": hx(src + 5), "bytes": raw[pos:pos + 5].hex(" ").upper()})
        pos = raw.find(b"\xE8", pos + 1)
    return result


def relevant(rows: list[dict], needles: tuple[str, ...]) -> list[dict]:
    return [r for r in rows if any(n.lower() in r["instruction"].lower() for n in needles)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", type=Path, default=EXE_DEFAULT)
    ap.add_argument("--output", type=Path, default=Path("bridge/building_snap_static_map.json"))
    args = ap.parse_args()
    exe_hash = hash_file(args.exe)
    pe = pefile.PE(str(args.exe))

    decoded = {name: disasm(pe, *span) for name, span in RANGES.items()}
    # The .pdata table splits two large functions into chained unwind ranges;
    # present their union as an approximate logical boundary while retaining
    # the authoritative fragments above.
    function_fragments = {
        "0x3E2CD0": [["0x3E2CD0", "0x3E3254"], ["0x3E3254", "0x3E33A7"], ["0x3E33A7", "0x3E354E"]],
        "0x3E40D0": [["0x3E40D0", "0x3E417D"], ["0x3E417D", "0x3E418F"], ["0x3E418F", "0x3E435C"], ["0x3E435C", "0x3E438D"], ["0x3E438D", "0x3E47C3"], ["0x3E47C3", "0x3E47F3"], ["0x3E47F3", "0x3E4838"]],
        "0x2807D5": [["0x2807D5", "0x2810E8"]],
        "0x3E79C0": [["0x3E79C0", "0x3E7AAA"], ["0x3E7AC0", "0x3E7DED"]],
        "0x3E74B0": [["0x3E74B0", "0x3E771F"]],
        "0x3EBB70": [["0x3EBB70", "0x3EBBA2"], ["0x3EBBA2", "0x3EBC91"], ["0x3EBC91", "0x3EBCA5"]],
    }

    p = decoded["placementFunction"]
    c = decoded["placementConsumer"]
    up = decoded["upstreamPlacementCaller"]
    filt = decoded["candidateFilter"]
    dec = decoded["candidateRecordDecoder"]
    event = decoded["buildingPlaceEvent"]

    data_flow = {
        "status": "PROVEN_STATIC_BUILD_1076226",
        "incomingTransformSource": {
            "baseRegister": "R15",
            "evidence": [
                {"rva": "0x3E2D85", "instruction": "movups xmm4, xmmword ptr [r15+0x0C]", "role": "orientation/transform lanes consumed"},
                {"rva": "0x3E2D92", "instruction": "movsd xmm2, qword ptr [r15]", "role": "first two position components consumed"},
                {"rva": "0x3E2DAF", "instruction": "movss xmm5, dword ptr [r15+0x08]", "role": "third position component consumed"},
                {"rva": "0x3E2E5C", "instruction": "movups xmm2, xmmword ptr [r15+0x0C]", "role": "second transform read"},
                {"rva": "0x3E2FE6", "instruction": "movups xmm2, xmmword ptr [r15+0x0C]", "role": "bounds/transform recomputation"},
            ],
            "status": "PROVEN_SOURCE_READ; SEMANTIC_LABELS_UNRESOLVED",
        },
        "positionAndGrid": {
            "evidence": [
                {"rva": "0x3E3445", "instruction": "movss [rbp-0x78], xmm2"},
                {"rva": "0x3E346E", "instruction": "mov [rsp+0x70], rax"},
                {"rva": "0x3E3491", "instruction": "mov [rsp+0x78], rax"},
                {"rva": "0x3E34DD", "instruction": "mov [rbp-0x80], rax"},
            ],
            "interpretation": "integerized/scaled coordinates and derived bounds feed the event helper; exact world/grid semantic split is UNSOLVED",
            "status": "PROVEN_DATA_FLOW; INFERRED_ROLE",
        },
        "buildingEventArguments": {
            "evidence": [
                {"rva": "0x3E33FF", "instruction": "mov rcx,rsi", "meaning": "placement state/context owner passed to helper"},
                {"rva": "0x3E3407", "instruction": "lea rdx,[rsp+0x70]", "meaning": "derived integer coordinate structure"},
                {"rva": "0x3E33FB", "instruction": "lea r8,[rbp-0x20]", "meaning": "derived float/quaternion/bounds structure"},
                {"rva": "0x3E34E1", "instruction": "mov eax,[r12]", "meaning": "resolved record item id"},
                {"rva": "0x3E34F1", "instruction": "mov [rsp+0x20],eax", "meaning": "fifth stack argument"},
                {"rva": "0x3E3505", "instruction": "call 0x3EBB70", "meaning": "BuildingPlaceEvent helper"},
            ],
            "status": "PROVEN_STATIC_BUILD_1076226",
        },
    }

    snap = {
        "candidateFilterFunction": {
            "rva": "0x3E79C0",
            "boundaryStatus": "PROVEN_STATIC_BUILD_1076226",
            "inputs": [
                {"register": "RDX", "evidence": "saved to RSI at 0x3E79EA; tests [RSI+0x110]", "status": "PROVEN"},
                {"register": "RCX", "evidence": "saved to R15 at 0x3E79ED; output list storage used at [R15+0x00/+0x08]", "status": "PROVEN"},
                {"register": "R8", "evidence": "saved to RBX at 0x3E79E7; source AABB/auxiliary input", "status": "PROVEN"},
                {"register": "R9", "evidence": "saved to RDI at 0x3E79E4; comparison/auxiliary pointer", "status": "PROVEN"},
            ],
            "algorithmEvidence": [
                {"rva": "0x3E7A81", "instruction": "mov rdx,[rsi+0x110]", "meaning": "source collection passed to 0x8EF920"},
                {"rva": "0x3E7A9A", "instruction": "call 0x8EF920", "meaning": "produces bounded candidate storage/count in local slots"},
                {"rva": "0x3E7AB5", "instruction": "cmp qword ptr [rsp+0x38],r14", "meaning": "zero/count guard before loop"},
                {"rva": "0x3E7B10", "instruction": "mov r12,qword ptr [rsp+0x30]", "meaning": "candidate array base"},
                {"rva": "0x3E7B15", "instruction": "mov rbx,qword ptr [r12+r14]", "meaning": "candidate_00 qword read"},
                {"rva": "0x3E7B1E", "instruction": "cmp rbx,rdi", "meaning": "candidate_00 identity/exclusion comparison"},
                {"rva": "0x3E7B27", "instruction": "movzx edx,byte ptr [r12+r14+0x1B]", "meaning": "candidate_1B byte passed to helper"},
                {"rva": "0x3E7B4A", "instruction": "movsd xmm0,qword ptr [r12+r14+0x0C]", "meaning": "candidate_0C packed/coordinate input"},
                {"rva": "0x3E7B91", "instruction": "movzx eax,byte ptr [r12+r14+0x1A]", "meaning": "candidate_1A byte"},
                {"rva": "0x3E7B97", "instruction": "add eax,dword ptr [r12+r14+0x14]", "meaning": "candidate_14 dword combined with candidate_1A"},
                {"rva": "0x3E7B40", "instruction": "movzx eax,word ptr [r12+r14+0x18]", "meaning": "candidate_18 word"},
                {"rva": "0x3E7C3F", "instruction": "comiss xmm1,xmm8", "meaning": "AABB containment test"},
                {"rva": "0x3E7C74", "instruction": "minss xmm0,xmm2", "meaning": "distance/extent threshold calculation"},
                {"rva": "0x3E7C86", "instruction": "mov edx,dword ptr [r12+r14+0x08]", "meaning": "candidate_08 lookup key/reference"},
                {"rva": "0x3E7C92", "instruction": "call 0xCA90E0", "meaning": "lookup candidate blueprint record from placement cache"},
                {"rva": "0x3E7D5D", "instruction": "mov [r8],rax", "meaning": "append resolved record pointer"},
                {"rva": "0x3E7DAB", "instruction": "add r14,0x20", "meaning": "candidate index stride 0x20"},
                {"rva": "0x3E7DB0", "instruction": "cmp r13,qword ptr [rsp+0x38]", "meaning": "loop count/end condition"},
            ],
            "pseudoStructure": {
                "name": "CandidateRecord_Observed",
                "stride": {"value": "0x20", "status": "PROVEN"},
                "fields": [
                    {"offset": "0x00", "width": 8, "access": "qword read; compared with RDI", "status": "PROVEN", "role": "unknown identity/pointer"},
                    {"offset": "0x08", "width": 4, "access": "dword read into EDX for 0xCA90E0", "status": "PROVEN", "role": "lookup key/reference (semantic type unresolved)"},
                    {"offset": "0x0C", "width": 8, "access": "qword read as packed value and split into 32-bit halves", "status": "PROVEN", "role": "coordinate/packed candidate input (unresolved)"},
                    {"offset": "0x14", "width": 4, "access": "dword added to byte at +0x1A", "status": "PROVEN", "role": "unknown scalar"},
                    {"offset": "0x18", "width": 2, "access": "word read; copied to temporary stack field", "status": "PROVEN", "role": "unknown scalar/flags"},
                    {"offset": "0x1A", "width": 1, "access": "byte read and combined with +0x14", "status": "PROVEN", "role": "unknown scalar"},
                    {"offset": "0x1B", "width": 1, "access": "byte passed to 0x248F50", "status": "PROVEN", "role": "unknown filter input"},
                ],
                "unaccessedRange": "0x1C-0x1F not accessed in bounded function",
            },
            "acceptedCollection": {
                "status": "PROVEN_STATIC_BUILD_1076226",
                "passedAs": "RCX (caller-owned collection object)",
                "header": [
                    {"offset": "0x00", "width": 8, "meaning": "element storage pointer", "status": "PROVEN"},
                    {"offset": "0x08", "width": 8, "meaning": "logical element count", "status": "PROVEN"},
                    {"offset": "0x10", "width": 8, "meaning": "capacity/end bound", "status": "PROVEN"},
                    {"offset": "0x18", "width": 8, "meaning": "grow callback used when count reaches capacity", "status": "PROVEN"},
                ],
                "elementStride": "0x50",
                "elementFields": [
                    {"offset": "0x00", "width": 8, "source": "normalized record payload pointer", "status": "PROVEN"},
                    {"offset": "0x08", "width": 8, "source": "normalized record payload length/count", "status": "PROVEN"},
                    {"offset": "0x10", "width": 1, "source": "normalized record compression flag", "status": "PROVEN"},
                    {"offset": "0x14", "width": 8, "source": "normalized record dimensions (+0x04)", "status": "PROVEN"},
                    {"offset": "0x1C", "width": 4, "source": "normalized record secondary extent (+0x0C)", "status": "PROVEN"},
                    {"offset": "0x20", "width": 8, "source": "candidate +0x0C packed/scalar value", "status": "PROVEN"},
                    {"offset": "0x28", "width": 4, "source": "candidate +0x14", "status": "PROVEN"},
                    {"offset": "0x2C", "width": 4, "source": "derived packed component", "status": "PROVEN"},
                    {"offset": "0x30", "width": 4, "source": "derived packed component", "status": "PROVEN"},
                    {"offset": "0x34", "width": 4, "source": "derived packed component", "status": "PROVEN"},
                    {"offset": "0x38", "width": 16, "source": "derived SIMD transform/vector", "status": "PROVEN"},
                    {"offset": "0x48", "width": 8, "source": "candidate +0x00 auxiliary pointer/value", "status": "PROVEN"},
                    {"offset": "0x4C-0x4F", "meaning": "not accessed in bounded append path", "status": "UNKNOWN"},
                ],
                "ownership": "Caller initializes and owns the collection; exact lifetime beyond each caller is unresolved.",
            },
            "loopControl": {
                "candidateBaseLocal": "[rsp+0x30] (filled by 0x8EF920)",
                "candidateCountLocal": "[rsp+0x38] (filled by 0x8EF920)",
                "candidateIndexRegister": "R14 (starts zero; increments by 0x20 at 0x3E7DAB)",
                "status": "PROVEN_STATIC_BUILD_1076226",
            },
            "branches": [
                {"rva": "0x3E7B21", "target": "0x3E7DA4", "condition": "candidate_00 == RDI", "classification": "reject/skip candidate"},
                {"rva": "0x3E7B3A", "target": "0x3E7DA4", "condition": "0x248F50 reports nonzero flag", "classification": "reject/skip candidate"},
                {"rva": "0x3E7C43", "target": "0x3E7DA4", "condition": "first COMISS below", "classification": "reject/skip candidate"},
                {"rva": "0x3E7C49", "target": "0x3E7DA4", "condition": "second COMISS below", "classification": "reject/skip candidate"},
                {"rva": "0x3E7C52", "target": "0x3E7DA4", "condition": "third COMISS below", "classification": "reject/skip candidate"},
                {"rva": "0x3E7C80", "target": "0x3E7DA4", "condition": "distance comparison >= threshold", "classification": "reject/skip candidate"},
                {"rva": "0x3E7C9D", "target": "0x3E7D9D", "condition": "0xCA90E0 returned null", "classification": "no resolved record / no append"},
                {"rva": "0x3E7D5D", "target": "0x3E7D99", "condition": "resolved record and output capacity available", "classification": "candidate survives and is accumulated"},
                {"rva": "0x3E7DF5", "target": "return", "condition": "BL=1 after loop", "classification": "function-level success indicator; not a best-candidate identity"},
            ],
            "classification": "STRUCTURALLY_IDENTIFIABLE_CANDIDATE_FILTER; exact snap semantics/rule identity UNSOLVED",
            "confidence": "HIGH_FOR_FILTER_AND_CACHE_LOOKUP; MEDIUM_FOR_SNAP_LABEL",
        },
        "cacheLookupRelationship": {
            "callSiteRva": "0x3E7C92",
            "arguments": [
                {"register": "RCX", "expression": "[RSI+0xF0]", "status": "PROVEN"},
                {"register": "EDX", "expression": "dword [candidateBase + index + 0x08]", "status": "PROVEN"},
            ],
            "return": {"register": "RAX", "status": "PROVEN_POINTER_OR_NULL", "nullBranchRva": "0x3E7C9D"},
            "returnedFieldsRead": ["+0x04 at 0x3E7CED", "+0x0C at 0x3E7CF6", "+0x10 via normalized copy", "+0x14 at 0x3E7D00", "+0x18 via 0x3E7D64"],
            "structuralConclusion": "candidate_08 is used as a key/reference to 0xCA90E0; non-null RAX is then consumed as a runtime blueprint/placement record-shaped pointer. Exact reflected type and whether key is ItemId remain UNSOLVED.",
            "confidence": "PROVEN_CALL_DATA_FLOW; INFERRED_RECORD_RELATIONSHIP",
        },
        "recordDecoderFunction": {
            "rva": "0x3E74B0",
            "algorithmEvidence": [
                {"rva": "0x3E7575", "instruction": "movsd xmm0,[r14+4]", "meaning": "record dimensions/extent input"},
                {"rva": "0x3E7580", "instruction": "mov eax,[r14+0x0C]", "meaning": "secondary extent input"},
                {"rva": "0x3E7665", "instruction": "movsxd rax,dword ptr [r14+0x10]", "meaning": "signed relative payload offset"},
                {"rva": "0x3E76B3", "instruction": "mov [rsi],rax", "meaning": "derived payload pointer/base"},
                {"rva": "0x3E76B6", "instruction": "mov [rsi+8],r15", "meaning": "derived payload length/count"},
                {"rva": "0x3E76BA", "instruction": "movzx eax,byte ptr [r14+0x18]", "meaning": "compression flag"},
                {"rva": "0x3E76BF", "instruction": "mov [rsi+0x10],al", "meaning": "propagated compression flag"},
            ],
            "status": "PROVEN_STATIC_BUILD_1076226",
        },
        "ruleIdentity": {"status": "UNSOLVED", "reason": "No connected instruction references KFC GUIDs or a runtime rule descriptor; offline catalog remains evidence only."},
    }

    output = {
        "schemaVersion": 1,
        "tool": "scan_building_snap_static.py",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "safety": {"processAccess": False, "memoryWrites": False, "hooksInstalled": False, "deploymentChanged": False},
        "executable": {"path": str(args.exe), "sha256": exe_hash, "supportedSha256": SUPPORTED_SHA256, "fingerprintMatches": exe_hash == SUPPORTED_SHA256, "imageBase": hx(pe.OPTIONAL_HEADER.ImageBase), "imageSize": hx(pe.OPTIONAL_HEADER.SizeOfImage), "timeDateStamp": hx(pe.FILE_HEADER.TimeDateStamp)},
        "anchors": {k: hx(v) for k, v in ANCHORS.items()},
        "expectedInstructionBytes": {
            "buildingPlaceCall": {"rva": "0x3E3505", "bytes": "E8 66 86 00 00", "targetRva": "0x3EBB70", "status": "PROVEN_STATIC_BUILD_1076226"},
            "candidateFilterCall": {"rva": "0x3E4347", "bytes": "E8 74 36 00 00", "targetRva": "0x3E79C0", "status": "PROVEN_STATIC_BUILD_1076226"},
            "candidateCacheLookup": {"rva": "0x3E7C92", "bytes": "E8 49 14 8C 00", "targetRva": "0xCA90E0", "status": "PROVEN_STATIC_BUILD_1076226"},
            "upstreamPlacementCall": {"rva": "0x280F86", "bytes": "E8 45 1D 16 00", "targetRva": "0x3E2CD0", "status": "PROVEN_STATIC_BUILD_1076226"},
        },
        "functionBoundaries": boundaries(pe, list(ANCHORS.values())),
        "logicalFunctionFragments": function_fragments,
        "connectedCallGraph": {k: {"range": [hx(a), hx(b)], "directCalls": direct_calls(pe, a, b)} for k, (a, b) in RANGES.items()},
        "connectedPaths": [
            {"path": ["0x280F86", "0x3E2CD0", "0x3EBB70"], "relationship": "upstream input transform -> placement arithmetic -> BuildingPlaceEvent construction", "status": "PROVEN_STATIC_BUILD_1076226"},
            {"path": ["0x3E40D0", "0x3E79C0", "0xCA90E0", "0x3E74B0", "0x3EBCB0"], "relationship": "alternate placement routine -> candidate filter -> blueprint cache lookup -> record normalization -> event construction", "status": "PROVEN_STATIC_BUILD_1076226"},
            {"path": ["0x3E2CD0", "0x3EAB80", "0x996F90", "0x3EBB70"], "relationship": "placement-owned helper/candidate preparation -> event construction; semantic roles of 0x3EAB80/0x996F90 remain unresolved", "status": "PROVEN_CALL_EDGES; INFERRED_ROLES"},
        ],
        "directCallers": {hx(t): call_xrefs(pe, t) for t in [0x3E2CD0, 0x3E40D0, 0x3EBB70, 0x3E79C0, 0x3E74B0]},
        "knownInstructionEvidence": {"placementFunction": relevant(p, ("r15", "r12", "3ebb70", "ca90e0")), "placementConsumer": relevant(c, ("rsi", "3e79c0", "ca90e0", "3ebcb0", "xmm")), "upstreamCaller": relevant(up, ("3e2cd0", "rsi", "rbx", "r8d")), "candidateFilter": relevant(filt, ("rsi+0x110", "r14", "ca90e0", "comiss", "minss", "r8")), "recordDecoder": relevant(dec, ("r14+0x10", "r14+0x18", "rsi+0x", "movsxd")), "buildingPlaceEvent": event},
        "placementDataFlow": data_flow,
        "snapAndTransformCandidates": snap,
        "offlineSemanticCatalog": {"source": "bridge/snap_rule_catalog.json", "configurationCount": 7, "ruleCount": 31, "runtimeItemToFamily": "UNSOLVED", "status": "OFFLINE_ONLY"},
        "observerDecision": {"install": False, "status": "FAIL_CLOSED_STATIC_ONLY", "reason": "Although 0x3E79C0 is a structurally strong candidate-filter path, no uniquely validated pre-placement callback/transform state boundary or safe observer signature was established. Existing BuildingPlaceEvent remains the only runtime hook."},
        "rejectedHypotheses": [
            {"hypothesis": "BuildingPlaceEvent context is the preview source", "status": "DISPROVEN_DOWNSTREAM_ANCHOR", "evidence": "helper is called after transform/bounds construction at 0x3E33F6-0x3E3505"},
            {"hypothesis": "0x3E79C0 directly identifies the selected KFC snap rule", "status": "UNSOLVED", "evidence": "it filters candidate AABBs and resolves cache records, but no rule GUID/flags are read in the bounded path"},
            {"hypothesis": "install a new transform detour for v0.25", "status": "REJECTED", "evidence": "no validated safe instruction window and no runtime requirement; DLL left unchanged"},
        ],
        "nextEvidence": ["Read-only capture of the existing BuildingPlaceEvent context can correlate final position/orientation only.", "A future observer would need a validated preview update callback or field writer, plus pre/post state evidence; none is proven in this build."],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} sha={exe_hash} fingerprintMatches={output['executable']['fingerprintMatches']} observerInstall={output['observerDecision']['install']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
