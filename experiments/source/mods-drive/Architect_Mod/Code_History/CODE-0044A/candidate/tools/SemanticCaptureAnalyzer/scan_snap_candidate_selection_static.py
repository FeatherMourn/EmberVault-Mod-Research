"""Offline v0.27 accepted snap-candidate collection/selection map.

This companion scanner consumes only the supported executable on disk.  It
decodes bounded instruction windows around the already known 0x3E79C0 callers;
it never opens a process, installs a hook, or writes game memory.
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


def hx(v: int | None) -> str | None:
    return None if v is None else f"0x{v:X}"


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest().upper()


def disasm(pe: pefile.PE, start: int, end: int) -> list[dict]:
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    rows = []
    for ins in md.disasm(pe.get_data(start, end - start), start):
        rows.append({"rva": hx(ins.address), "instruction": f"{ins.mnemonic} {ins.op_str}".strip(), "bytes": ins.bytes.hex(" ").upper()})
    return rows


def pdata_bounds(pe: pefile.PE, target: int) -> dict:
    sec = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".pdata")
    raw = sec.get_data()
    for off in range(0, len(raw) - 11, 12):
        begin, end, unwind = struct.unpack_from("<III", raw, off)
        if begin <= target < end:
            return {"startRva": hx(begin), "endRva": hx(end), "unwindInfoRva": hx(unwind), "status": "PROVEN_STATIC_BUILD_1076226"}
    return {"startRva": None, "endRva": None, "unwindInfoRva": None, "status": "UNKNOWN"}


def call_xrefs(pe: pefile.PE, target: int) -> list[dict]:
    sec = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".text")
    raw, base = sec.get_data(), sec.VirtualAddress
    out = []
    pos = raw.find(b"\xE8")
    while pos >= 0 and pos + 5 <= len(raw):
        src = base + pos
        dst = src + 5 + struct.unpack_from("<i", raw, pos + 1)[0]
        if dst == target:
            out.append({"callRva": hx(src), "returnRva": hx(src + 5), "bytes": raw[pos:pos + 5].hex(" ").upper()})
        pos = raw.find(b"\xE8", pos + 1)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", type=Path, default=EXE_DEFAULT)
    ap.add_argument("--output", type=Path, default=Path("bridge/snap_candidate_selection_static_map.json"))
    args = ap.parse_args()
    digest = file_hash(args.exe)
    pe = pefile.PE(str(args.exe))

    callers = {
        "0x3E377D": {"function": "0x3E35FF-0x3E3828", "outputLocal": "[RBP+0x190]", "postReturn": ["0x3E3782 test AL,AL", "0x3E3A20 load [RBP+0x190]", "0x3E3A40 call 0x3EB810"]},
        "0x3E4347": {"function": "0x3E418F-0x3E435C", "outputLocal": "[RBP+0x1B0]", "postReturn": ["0x3E4354 test AL,AL", "0x3E4537 load [RBP+0x1B0]", "0x3E4379 call 0x3E5480"]},
        "0x3E6C9C": {"function": "0x3E6C13-0x3E6DBF", "outputLocal": "[RBP+0xD0]", "postReturn": ["0x3E6CA1 test AL,AL", "0x3E6CB8 load [RBP+0xD0]", "0x3E6CB3 call 0x3EAB80"]},
        "0x3EB297": {"function": "0x3EAFE0-0x3EB640", "outputLocal": "[RBP+0x3D0]", "postReturn": ["0x3EB29C test AL,AL", "0x3EB588 load [RBP+0x3D0]", "0x3EB5A8 call 0x3EB810"]},
    }
    caller_windows = {
        "0x3E377D": disasm(pe, 0x3E3726, 0x3E37A5),
        "0x3E4347": disasm(pe, 0x3E42F0, 0x3E4385),
        "0x3E6C9C": disasm(pe, 0x3E6C08, 0x3E6CC8),
        "0x3EB297": disasm(pe, 0x3EB250, 0x3EB2B0),
    }
    for k in callers:
        callers[k]["instructionEvidence"] = caller_windows[k]
        callers[k]["boundary"] = pdata_bounds(pe, int(k, 16))

    output = {
        "schemaVersion": 1,
        "tool": "scan_snap_candidate_selection_static.py",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "safety": {"processAccess": False, "memoryWrites": False, "hooksInstalled": False, "deploymentChanged": False},
        "executable": {"path": str(args.exe), "sha256": digest, "supportedSha256": SUPPORTED_SHA256, "fingerprintMatches": digest == SUPPORTED_SHA256, "imageBase": hx(pe.OPTIONAL_HEADER.ImageBase)},
        "anchors": {"candidateFilter": "0x3E79C0", "cacheLookup": "0xCA90E0", "recordNormalizer": "0x3E74B0"},
        "functionBoundaries": {
            "candidateFilter": {"logicalStartRva": "0x3E79C0", "logicalEndRva": "0x3E7E4A", "pdataFragments": [["0x3E79C0", "0x3E7AAA"], ["0x3E7AC0", "0x3E7DED"], ["0x3E7DED", "0x3E7DF7"], ["0x3E7DF7", "0x3E7E4A"]], "status": "PROVEN_STATIC_BUILD_1076226"},
            "consumer_0x3EB810": pdata_bounds(pe, 0x3EB810),
            "consumer_0x3E5480": pdata_bounds(pe, 0x3E5480),
            "consumer_0x3EAB80": pdata_bounds(pe, 0x3EAB80),
        },
        "candidateFilter": {
            "rva": "0x3E79C0",
            "inputRecordStride": "0x20",
            "outputRecordStride": "0x50",
            "sourceCollection": {"base": "[RSI+0x110]", "producerCall": "0x8EF920", "countLocal": "[RSP+0x38]", "status": "PROVEN"},
            "acceptedCollection": {
                "argument": "RCX",
                "header": {"0x00": "storage pointer", "0x08": "logical count", "0x10": "capacity", "0x18": "grow callback"},
                "appendEvidence": ["0x3E7CA3 read [R15+0x08]", "0x3E7CA8 read [R15+0x10]", "0x3E7CC6 indirect grow", "0x3E7D5D write element", "0x3E7D99 increment count"],
                "elementFields": {
                    "0x00": "normalized payload pointer",
                    "0x08": "normalized payload length",
                    "0x10": "compression flag",
                    "0x14": "dimensions",
                    "0x1C": "secondary extent",
                    "0x20": "candidate +0x0C packed value",
                    "0x28": "candidate +0x14",
                    "0x2C-0x34": "derived packed components",
                    "0x38": "derived SIMD vector (16 bytes)",
                    "0x48": "candidate +0x00 auxiliary value/pointer",
                },
                "ownership": "caller-owned local/container; persistence after caller is unresolved",
                "status": "PROVEN_STATIC_BUILD_1076226",
            },
            "rejectConvergence": ["0x3E7B21", "0x3E7B3A", "0x3E7C43", "0x3E7C49", "0x3E7C52", "0x3E7C80"],
            "cacheLookupCall": {"rva": "0x3E7C92", "target": "0xCA90E0", "key": "candidate +0x08", "owner": "[RSI+0xF0]", "nullBranch": "0x3E7C9D"},
        },
        "callers": callers,
        "selectionAndRanking": {
            "insideCandidateFilter": "No score accumulator, sort, min/max winner, or selected-candidate pointer is present; all passing records are appended.",
            "returnValue": "AL/BL boolean at 0x3E7DF5 indicates that processing completed, not which candidate won.",
            "firstUnresolvedBoundary": ["caller-specific post-return code", "0x3E5480", "0x3EAB80", "0x3EB810", "0xE81920"],
            "status": "UNRESOLVED_STATIC_BOUNDARY",
        },
        "consumerAnalysis": [
            {"caller": "0x3E377D", "collectionLocal": "[RBP+0x190]", "evidence": ["0x3E3A20 loads collection storage", "0x3E3A31 loads collection count", "0x3E3A40 calls 0x3EB810"], "classification": "forwarded-to-secondary-candidate-processing", "selectionStatus": "UNRESOLVED"},
            {"caller": "0x3E4347", "collectionLocal": "[RBP+0x1B0]", "evidence": ["0x3E4537 loads collection storage", "0x3E4557 loads collection count", "0x3E4379 calls 0x3E5480 with placement state"], "classification": "forwarded-to-transform-or-commit-helper", "selectionStatus": "UNRESOLVED"},
            {"caller": "0x3E6C9C", "collectionLocal": "[RBP+0xD0]", "evidence": ["0x3E6CB8 loads collection storage", "0x3E6CD1 passes it in a later call frame", "0x3E6CB3 calls 0x3EAB80"], "classification": "forwarded-to-placement-helper", "selectionStatus": "UNRESOLVED"},
            {"caller": "0x3EB297", "collectionLocal": "[RBP+0x3D0]", "evidence": ["0x3EB588 loads collection storage", "0x3EB59C loads collection count", "0x3EB5A8 calls 0x3EB810"], "classification": "forwarded-to-secondary-candidate-processing", "selectionStatus": "UNRESOLVED"},
            {"function": "0x3EB810", "structure": "iterates a 0x50-byte accepted element array; calls 0x99ECF0 and 0x8CD2C0 per element", "selectionStatus": "no winner comparison proven in bounded window", "status": "PROVEN_CALL_DATA_FLOW"},
            {"function": "0x3E5480", "structure": "consumes placement state and derived records; writes a separate output object", "selectionStatus": "winner/transform relation unresolved", "status": "INFERRED_CONSUMER"},
        ],
        "transformConnection": {"evidence": "accepted elements carry payload/dimensions plus packed/vector fields consumed by callers", "finalSelectionOrTransform": "UNPROVEN", "status": "INFERRED_DATA_HANDOFF"},
        "cacheRelationship": {"status": "PROVEN_CALL_DATA_FLOW", "meaning": "0xCA90E0 resolves each candidate +0x08 against placement cache [RSI+0xF0]; it does not itself rank the accepted list."},
        "collectionLifecycle": {"clearedOrRebuiltPerUpdate": "UNKNOWN", "recordPersistence": "UNKNOWN", "clientServerSeparation": "UNKNOWN", "evidence": "all four observed callers initialize stack-backed collection headers before invoking 0x3E79C0; no cross-frame owner was proven"},
        "alternatePlacementPath": {"rva": "0x3E40D0", "relationshipToCandidateFilter": "direct caller at 0x3E4347", "semanticClassification": "UNRESOLVED", "evidence": "same filter is called with a distinct stack-backed output collection; post-return path forwards collection data to 0x3E5480"},
        "blueprintIdentity": {"candidateKeyField": "candidate +0x08", "lookupRva": "0xCA90E0", "recordNormalizationRva": "0x3E74B0", "stableItemIdCapture": "record normalization reads dimensions/payload/compression but item-id field is not read in the bounded filter", "status": "PARTIAL_PROVEN"},
        "observerSites": [
            {"kind": "collection_complete", "rva": "0x3E7DED", "enclosingFunction": "0x3E79C0", "frequency": "per filter invocation", "availableData": "output collection and count", "safety": "medium-risk/high-frequency", "recommended": False},
            {"kind": "caller_result", "rva": "0x3E3782/0x3E4354/0x3E6CA1/0x3EB29C", "enclosingFunction": "caller-specific", "frequency": "per candidate-filter invocation", "availableData": "boolean only; collection local remains addressable in some callers", "safety": "lower than loop but lifetime/consumer not proven", "recommended": False},
            {"kind": "consumer_entry", "rva": "0x3EB810/0x3E5480/0x3EAB80/0xE81920", "enclosingFunction": "consumer-specific", "frequency": "unknown", "availableData": "collection storage/count in selected call frames", "safety": "unvalidated; no observer installed", "recommended": False},
        ],
        "observerDecision": {"install": False, "status": "FAIL_CLOSED_STATIC_ONLY", "reason": "No low-frequency site was proven to expose a stable accepted collection and selected winner without entering a high-frequency or stateful path."},
        "nextInvestigation": "Trace each caller's post-return consumer and identify the first instruction that chooses/forwards one 0x50-byte accepted element; keep any future observer read-only and low-frequency.",
        "confidence": {"outputStrideAndAppend": "HIGH", "callerEdges": "HIGH", "selectionWinner": "UNKNOWN", "transformSemantics": "UNKNOWN"},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} fingerprintMatches={output['executable']['fingerprintMatches']} observerInstall=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
