#!/usr/bin/env python3
"""CODE-0006 offline snap-winner/preview-writeback authority map."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.SemanticActionObserver.scan_blueprint_selection_authority_static import StaticImage

EXE = ROOT.parent.parent / "enshrouded.exe"
SHA = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
DLLSHA = "C3AAF673001CBE08C508F703C0D9219836067A7A9818A4A9473D3BA49F89A801"

def hx(v): return f"0x{v:X}"
def dis_rows(im, start, end):
    return [{"rva": hx(i.address), "bytes": i.bytes.hex(), "instruction": i.mnemonic + (" " + i.op_str if i.op_str else "")} for i in im.disassemble(start, end)]

def build(exe: Path) -> dict:
    parent = json.loads((ROOT / "bridge/snap_candidate_selection_static_map.json").read_text(encoding="utf-8"))
    if parent.get("analysisMode") != "OFFLINE_STATIC_ONLY" or parent.get("observerDecision", {}).get("install") is not False:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY")
    image = StaticImage(exe)
    if image.digest != SHA: raise RuntimeError("BUILD_MISMATCH")
    fam_a = dis_rows(image, 0x3EB810, 0x3EB8C3)
    fam_b = dis_rows(image, 0x99F970, 0x99FD29)
    caller_rvas = (0x3E377D, 0x3E4347, 0x3E6C9C, 0x3EB297)
    caller_windows = {}
    for rva in caller_rvas:
        bounds, _ = image.function_instructions(rva)
        caller_windows[hx(rva)] = bounds
    return {
      "schemaVersion": 1, "codeId": "CODE-0006", "analysisMode": "OFFLINE_STATIC_ONLY",
      "deliveryMode": "OFFLINE_STATIC_ONLY",
      "installNow": False, "gameHookInstallAuthorized": False,
      "currentSourceDesignationAuthorized": False,
      "build": {"revision": 1076226, "exeSha256": image.digest, "deployedDllSha256": DLLSHA},
      "safety": {"processAccess": False, "debugApis": False, "writesGameMemory": False, "writesExecutable": False, "runtimeHooksInstalled": False, "hookInstallationAuthorized": False, "currentSourceDesignationAuthorized": False},
      "parentEvidence": {"candidateFilter": "0x3E79C0", "acceptedStride": "0x50", "directCallers": ["0x3E377D", "0x3E4347", "0x3E6C9C", "0x3EB297"], "callerWindows": caller_windows},
      "consumerFamilies": [
        {"functionRva": "0x3EB810", "functionRange": ["0x3EB810", "0x3EB8C3"], "callers": ["0x3E377D", "0x3EB297"], "acceptedCollection": {"count": "[RDX+0x08] -> R14", "storage": "[RDX] -> RDI", "stride": "0x50", "elementFields": ["+0x48"], "evidence": ["0x3EB82F mov r14,[rdx+8]", "0x3EB83A mov rdi,[rdx]", "0x3EB89F add rdi,0x50"]}, "directElementCalls": [{"callRva": "0x3EB84E", "targetRva": "0x99ECF0", "argumentEvidence": ["R8=RDI (accepted element)", "RDX=[RBP+0x118]", "RCX=[RBP+0x30]"]}, {"callRva": "0x3EB872", "targetRva": "0x8CD2C0", "argumentEvidence": ["RBX=[RDI+0x48]", "R9=RBX (element-derived)", "R8D=[RBP+0x130]", "RDX=[RBP+0x110]"]}, {"callRva": "0x3EB893", "targetRva": "0x3E5480", "argumentEvidence": ["[RSP+0x90]=RBX (element-derived)", "RDX=&[RSP+0x90]", "RCX=RBP", "R8D=[RSP+0x28]"]}], "selection": {"status": "NO_WINNER_SELECTION_IN_BOUNDED_PATH", "evidence": ["per-element predicate 0x99ECF0", "per-element processing 0x8CD2C0 and 0x3E5480", "no retained best index/score"]}, "persistentWriteback": {"status": "UNSOLVED_NOT_PERSISTENCE_PROOF", "candidateOutput": "[RSP+0x90] passed to 0x3E5480; destination/lifetime unresolved", "downstreamEvidence": ["0x3E5480 calls 0x3ED1A0", "0x3E5578 receives the returned RAX", "0x3E5583..0x3E55E6 writes fields through returned RAX", "destination lifetime/owner and preview semantics unresolved"]}, "disassembly": fam_a},
        {"functionRva": "0x99F970", "functionRange": ["0x99F970", "0x99FD29"], "callers": ["0x3E4347", "0x3E6C9C"], "acceptedCollection": {"input": "caller-derived pointer loaded into RDI at [RBP+0x1C8]", "stride": "not proven", "fieldsRead": ["+0x14", "+0x1C", "+0x20", "+0x28", "+0x2C", "+0x34", "+0x38", "+0x40"], "evidence": ["0x99F9B7..0x99F9BA read fields from [RDI+offset]"]}, "directElementCalls": [{"callRva": "0x99FB33", "targetRva": "0x246FB0", "argumentEvidence": ["RDI-derived scalar/vector fields copied to local frame"]}, {"callRva": "0x99FB4C", "targetRva": "0x12A2560", "argumentEvidence": ["caller-frame array pointers/lengths"]}, {"callRva": "0x99FD09", "targetRva": "0x98EDD0", "argumentEvidence": ["constructed local output passed by RCX/RDX/R8/R9"]}], "selection": {"status": "NO_WINNER_SELECTION_IN_BOUNDED_PATH", "evidence": ["calculates one input record; no accepted-list traversal or candidate comparison"]}, "persistentWriteback": {"status": "UNSOLVED_NOT_PERSISTENCE_PROOF", "candidateOutput": "local frame objects/callees; stable owner unresolved"}, "disassembly": fam_b}
      ],
      "winnerSelection": {"status": "NO_WINNER_SELECTION_IN_BOUNDED_PATH", "confidence": "PARTIAL_STATIC", "reason": "Families process elements or compute one record; no instruction-backed winner choice was found."},
      "persistentWriteback": {"status": "UNSOLVED_NOT_PERSISTENCE_PROOF", "destinations": ["stack locals", "callee-dependent output of 0x3E5480"], "ownerProvenance": "unresolved"},
      "convergence": {"previewOwnerIdentity": "UNSOLVED", "blueprintIdentityOwner": "UNSOLVED", "commitTransformConvergence": "UNSOLVED", "createBuildingItemConvergence": "UNSOLVED", "frontier": "post-filter callee/output ownership; no proven edge to 0x3E2CD0 or preview state"},
      "observerEligibility": {"installNow": False, "gameHookInstallAuthorized": False, "currentSourceDesignationAuthorized": False, "status": "NOT_AUTHORIZED", "reason": "No persistent winner/writeback site proven"},
      "analysisResult": "PARTIAL_STATIC",
      "nextInvestigation": "Trace 0x3E5480 only if a concrete output-owner edge is established; remain static-only."
    }

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--exe", type=Path, default=EXE); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    result = build(a.exe); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

if __name__ == "__main__": raise SystemExit(main())
