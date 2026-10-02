"""Offline map of the 0x3E2CD0 commit transform and event construction path.

The scanner is intentionally static-only.  It reads the supported PE from disk,
decodes bounded instruction windows, and emits evidence without opening a game
process or installing an observer.
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


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def decode(pe: pefile.PE, start: int, end: int) -> list[dict]:
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    out = []
    for ins in md.disasm(pe.get_data(start, end - start), start):
        out.append({"rva": hx(ins.address), "instruction": f"{ins.mnemonic} {ins.op_str}".strip(), "bytes": ins.bytes.hex(" ").upper()})
    return out


def pdata(pe: pefile.PE, target: int) -> dict:
    sec = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".pdata")
    raw = sec.get_data()
    for off in range(0, len(raw) - 11, 12):
        begin, end, unwind = struct.unpack_from("<III", raw, off)
        if begin <= target < end:
            return {"startRva": hx(begin), "endRva": hx(end), "unwindInfoRva": hx(unwind), "status": "PROVEN_STATIC_BUILD_1076226"}
    return {"startRva": None, "endRva": None, "unwindInfoRva": None, "status": "UNKNOWN"}


def direct_calls(pe: pefile.PE, start: int, end: int) -> list[dict]:
    rows = []
    for row in decode(pe, start, end):
        if row["instruction"].startswith("call 0x"):
            rows.append({"rva": row["rva"], "instruction": row["instruction"], "bytes": row["bytes"]})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", type=Path, default=EXE_DEFAULT)
    ap.add_argument("--output", type=Path, default=Path("bridge/building_commit_transform_static_map.json"))
    args = ap.parse_args()
    exe_hash = digest(args.exe)
    pe = pefile.PE(str(args.exe))
    full = decode(pe, 0x3E2CD0, 0x3E354E)
    r15_accesses = [r for r in full if "r15" in r["instruction"].lower()]

    output = {
        "schemaVersion": 1,
        "tool": "scan_building_commit_transform_static.py",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "safety": {"processAccess": False, "memoryWrites": False, "hooksInstalled": False, "deploymentChanged": False},
        "executable": {"path": str(args.exe), "sha256": exe_hash, "supportedSha256": SUPPORTED_SHA256, "fingerprintMatches": exe_hash == SUPPORTED_SHA256, "imageBase": hx(pe.OPTIONAL_HEADER.ImageBase)},
        "function": {"rva": "0x3E2CD0", "approximateRange": ["0x3E2CD0", "0x3E354E"], "pdata": pdata(pe, 0x3E2CD0), "callers": [{"callRva": "0x280F86", "returnRva": "0x280F8B"}, {"callRva": "0x3E2288", "returnRva": "0x3E228D"}, {"callRva": "0x3E5B10", "returnRva": "0x3E5B15"}]},
        "registerProvenance": {
            "R15": {"definition": "0x3E2CEF mov r15,rdx", "source": "function argument RDX", "role": "incoming transform/context-like structure", "status": "PROVEN"},
            "RSI": {"definition": "0x3E2CF6 mov rsi,rcx", "source": "function argument RCX", "role": "placement state/context owner", "status": "PROVEN"},
            "R12": {"definition": "0x3E2D4C mov r12,rax", "source": "return of 0xCB4B50 at 0x3E2D47", "role": "record whose +0 supplies tracking id", "status": "PROVEN"},
            "R14": {"definition": "0x3E2D65 mov r14,rax", "source": "return of 0xCB4B50 at 0x3E2D60", "role": "secondary resolved record used for fields +0x428/+0x430/+0x438", "status": "PROVEN"},
        },
        "incomingR15PseudoLayout": {
            "name": "CandidatePlacementInput_Observed",
            "fields": [
                {"offset": "0x00", "width": 8, "accesses": ["0x3E2D92", "0x3E2E69", "0x3E3402"], "role": "scalar lane consumed in coordinate arithmetic", "status": "PROVEN_ACCESS_INFERRED_ROLE"},
                {"offset": "0x04", "width": 4, "accesses": ["0x3E340C"], "role": "scalar lane consumed in coordinate arithmetic", "status": "PROVEN_ACCESS_INFERRED_ROLE"},
                {"offset": "0x08", "width": 4, "accesses": ["0x3E2DAF", "0x3E2E6E", "0x3E3463"], "role": "scalar lane consumed in coordinate arithmetic", "status": "PROVEN_ACCESS_INFERRED_ROLE"},
                {"offset": "0x0C", "width": 16, "accesses": ["0x3E2D85", "0x3E2E5C", "0x3E2FE6", "0x3E2FF5"], "role": "four-lane vector consumed by arithmetic/shuffles", "status": "PROVEN_ACCESS_INFERRED_ROLE"},
                {"offset": "0x1C", "width": 4, "accesses": ["0x3E2D5C", "0x3E3236"], "role": "dword copied into local [RBP-0x54] and supplied to resolver", "status": "PROVEN_ACCESS_SEMANTIC_UNRESOLVED"},
                {"offset": "0x20", "width": 1, "accesses": ["0x3E303E"], "role": "branch/control byte", "status": "PROVEN_ACCESS_SEMANTIC_UNRESOLVED"},
            ],
            "unaccessedRange": "0x21 and above are not asserted by this bounded map",
        },
        "eventFieldFlow": {
            "eventHelper": {"rva": "0x3EBB70", "callSite": "0x3E3505", "status": "PROVEN_STATIC_BUILD_1076226"},
            "position": {"eventOffsets": ["0x08", "0x0C", "0x10"], "source": "caller RDX -> [RSP+0x70]", "evidence": ["0x3E3407 lea rdx,[rsp+0x70]", "0x3E346E write first integerized coordinate", "0x3E3491 write second integerized coordinate", "0x3E34DD write third integerized coordinate", "0x3EBBFE-0x3EBC26 reads helper RDX offsets 0/8/0x10 and scales"], "normalization": "float arithmetic, scale constants, cvttss2si at 0x3E2FE1/0x3E2FF0/0x3E3006 and 0x3E345E/0x3E3473/0x3E3496", "confidence": "PROVEN_STATIC_BUILD_1076226"},
            "orientation": {"eventOffsets": ["0x14", "0x18", "0x1C", "0x20"], "source": "caller RDX -> [RSP+0x70] offsets +0x18/+0x1C/+0x20/+0x24", "evidence": ["0x3E34A2/0x3E34C7 build final SIMD lanes", "0x3E3507 passes RDX pointer", "0x3EBC2B-0x3EBC4E writes event orientation fields"], "confidence": "PROVEN_STATIC_BUILD_1076226"},
            "volumeMin": {"eventOffsets": ["0x24", "0x28", "0x2C"], "source": "caller R8 -> [RBP-0x20]", "evidence": ["0x3E33FB lea r8,[rbp-0x20]", "0x3E3415-0x3E3459 clamp/min/max arithmetic", "0x3E34E9 stores final vector", "0x3EBC53-0x3EBC68 copies helper R8 offsets 0/+8"], "confidence": "PROVEN_STATIC_BUILD_1076226"},
            "volumeMax": {"eventOffsets": ["0x30", "0x34", "0x38"], "source": "caller R8 -> [RBP-0x20]", "evidence": ["0x3E33FB lea r8,[rbp-0x20]", "0x3E3420-0x3E34D3 clamp/min/max arithmetic", "0x3EBC6D-0x3EBC7D copies helper R8 offsets +0x10/+0x18"], "confidence": "PROVEN_STATIC_BUILD_1076226"},
            "material": {"eventOffset": "0x3C", "source": "helper R9D", "evidence": ["0x3E339F mov r9d,eax after 0xCAEC50", "0x3E3505 call", "0x3EBC53/0x3EBC57 writes helper R9D to event +0x3C"], "confidence": "PROVEN_DATA_FLOW_SEMANTIC_UNRESOLVED"},
            "trackingItemId": {"eventOffset": "0x40", "source": "record pointer R12 + 0", "evidence": ["0x3E2D4C R12=return of 0xCB4B50", "0x3E34E1 mov eax,[r12]", "0x3E34F1 mov [rsp+0x20],eax", "0x3EBB70 reads caller fifth arg at helper [rsp+0x60] and writes event +0x40"], "confidence": "PROVEN_STATIC_BUILD_1076226"},
            "ownerId": {"eventOffset": "0x44", "source": "placement state RSI + 0x134", "evidence": ["0x3EB C82 mov eax,[r14+0x134]".replace(" ", ""), "0x3EBC89 writes event +0x44"], "confidence": "PROVEN_STATIC_BUILD_1076226"},
        },
        "normalizationStages": [
            {"stage": "record_dimensions", "input": "RDI/R14 resolved records +0x04/+0x0C", "operations": ["cvtsi2ss", "multiply scale constants"], "output": "RBP locals -0x50..-0x30", "evidence": ["0x3E2D8A-0x3E2E05"]},
            {"stage": "grid_integerization", "input": "R15 vector lanes and derived locals", "operations": ["multiply/add scale", "cvttss2si"], "output": "[RSP+0x70], [RSP+0x78], [RBP-0x80]", "evidence": ["0x3E2FE1-0x3E3006", "0x3E345E-0x3E3496"]},
            {"stage": "volume_clamp", "input": "derived float bounds", "operations": ["maxss/minss", "shuffle/pack"], "output": "[RBP-0x20] passed as R8", "evidence": ["0x3E3415-0x3E34E9"]},
        ],
        "rotationPath": {"incoming": "R15 +0x0C four-lane vector", "operations": ["movups/shufps", "vector arithmetic in 0x3E2D85-0x3E2EEC and 0x3E2FE6-0x3E3017"], "discreteRotationIndex": "NOT_PROVEN", "eventOrientationSource": "derived caller RDX struct", "status": "PROVEN_VECTOR_FLOW; SEMANTIC_ROTATION_UNRESOLVED"},
        "itemMaterialProvenance": {"trackingItemId": "resolved record R12[0] from 0xCB4B50; not read directly from R15", "material": "return value of 0xCAEC50 at 0x3E3392, forwarded in R9D", "ownerId": "placement state RSI+0x134", "status": "PROVEN_DATA_FLOW; SEMANTIC_NAMES_UNRESOLVED"},
        "alternatePathComparison": {"function": "0x3E40D0", "shared": ["calls 0x3E79C0 at 0x3E4347", "uses placement-state fields and normalized records", "event/commit helpers downstream"], "different": ["distinct caller-owned output collection at [RBP+0x1B0]", "distinct transform/commit sequence through 0x3E5480"], "equivalenceTo3E2CD0": "NOT_PROVEN", "status": "STRUCTURAL_SIMILARITY_ONLY"},
        "r15AccessInstructionEvidence": r15_accesses,
        "directCalls": direct_calls(pe, 0x3E2CD0, 0x3E354E),
        "observerDecision": {"install": False, "status": "FAIL_CLOSED_STATIC_ONLY", "reason": "0x3E2CD0 is a commit-path function but firing frequency and a safe pre-processing instruction window are not established; deployed runtime remains unchanged."},
        "unsolved": ["concrete R15 type", "semantic meaning of R15 fields +0x00/+0x04/+0x08/+0x0C/+0x1C/+0x20", "discrete rotation index", "material enum identity", "whether 0x3E40D0 is an alternate commit mode", "runtime firing frequency before commit"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} fingerprintMatches={output['executable']['fingerprintMatches']} observerInstall=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
