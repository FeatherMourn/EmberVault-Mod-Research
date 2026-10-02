#!/usr/bin/env python3
"""Offline CODE-0005C parent-call relay and downstream correlation map."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from tools.SemanticActionObserver.scan_blueprint_selection_authority_static import StaticImage
from tools.SemanticActionObserver.build_observer_relocation_plan import plan_from_bytes

EXE = ROOT.parent.parent / "enshrouded.exe"
SUPPORTED = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
DEPLOYED = "C3AAF673001CBE08C508F703C0D9219836067A7A9818A4A9473D3BA49F89A801"

def hx(v): return f"0x{v:X}"

def build(exe: Path):
    parent = json.loads((ROOT/"bridge/placement_helper_observer_site_qualification_static_map.json").read_text(encoding="utf-8"))
    cap = json.loads((ROOT/"bridge/observer_trampoline_capability_map.json").read_text(encoding="utf-8"))
    if parent.get("selectedDesign",{}).get("status") != "NO_SAFE_OBSERVER_SITE" or cap.get("trampoline",{}).get("status") != "PARTIAL_HARNESS":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY")
    im = StaticImage(exe)
    if im.digest != SUPPORTED: raise RuntimeError("BUILD_MISMATCH")
    call_rva, target = 0x2807C8, 0x8D5CA0
    ins = next(i for i in im.disassemble(call_rva, call_rva+5) if i.address == call_rva)
    target_actual = int(ins.operands[0].imm) if ins.operands else None
    raw = bytes(ins.bytes)
    rel32 = int.from_bytes(raw[1:5], "little", signed=True)
    expected_target = call_rva + 5 + rel32
    return {
      "schemaVersion": 1, "codeId": "CODE-0005C", "analysisMode": "STAGING_IMPLEMENTATION_OFFLINE_HARNESS",
      "build": {"revision": 1076226, "exeSha256": im.digest, "deployedDllSha256": DEPLOYED},
      "parentRuntimeEvidence": {"rva": hx(call_rva), "targetRva": hx(target), "status": "OBSERVED_IN_RUNTIME_DUMP", "semanticOwner": "UNSOLVED", "hardwareBreakpointNotUsed": True},
      "site": {"callRva": hx(call_rva), "originalBytes": raw.hex(" ").upper(), "decodedTargetRva": hx(expected_target), "targetMatchesExpected": expected_target == target_actual == target, "patchWidth": 5, "returnRva": hx(call_rva+5), "callerFunction": im.function_for(call_rva)},
      "relay": {
        "kind": "site_specific_parent_call_tail_jump", "patchInstruction": "CALL rel32 relay", "patchWidth": 5,
        "originalBytes": raw.hex(" ").upper(), "tailJumpOriginalTarget": True, "helperTargetRva": hx(target),
        "modifiesReturnAddress": False, "callsFromRelay": False, "createsStackFrame": False,
        "usesScratch": ["r10 (state pointer)", "r11 (final helper JMP target only)"],
        "preserves": ["rcx","rdx","r8","r9","rax","rbp","rbx","rsi","rdi","r12","r13","r14","r15","rsp","xmm/ymm"],
        "rflags": {"status": "SITE_CONDITIONALLY_UNOBSERVABLE", "evidence": "helper entry does not read flags before 0x8D5CB2 cmp", "contract": "must be rechecked if helper bytes change"},
        "stateOffsets": {"busy": "0x08", "generation": "0x10", "dropped": "0x18", "capturedRdx": "0x20", "capturedRsp": "0x28", "capturedRbp": "0x30", "capturedRcx": "0x38", "capturedR8": "0x40", "capturedR9": "0x48", "helperTarget": "0x50"},
        "nearIsland": {"required": True, "rel32Range": "signed 32-bit", "allocation": "VirtualAlloc-owned relay/state in staging design only", "failClosedOutOfRange": True},
        "status": "DESIGN_ONLY_NOT_INSTALLED"
      },
      "callerContracts": [
        {"callRva": "0x2807C8", "rcx": "r15", "rdx": "rbp-0x30", "r8": "0x100", "r9": "unresolved caller-preserved", "returnRva": "0x2807CD"},
        {"callRva": "0x2810A3", "rcx": "r15", "rdx": "rbp-0x30", "r8": "0x100", "r9": "unresolved caller-preserved", "returnRva": "0x2810A8"}
      ],
      "correlation": {"usesExistingStableBuildingPlaceObserver": True, "requiresNewGameHook": False, "sameFrameProof": "UNPROVEN", "bufferLifetimeStatus": "PARTIAL_STATIC", "algorithm": ["coherent generation/busy snapshot", "RDX == capturedRbp-0x30", "known downstream stack/caller marker", "same-thread stack-range validation", "safe reads of buffer+0x38/+0x78"], "status": "CORRELATION_UNPROVEN"},
      "boundedWriteBetweenConsumers": {"status": "NO_STATIC_WRITE_FOUND_IN_BOUNDED_PATH", "meaning": "absence of a proven write is not immutability proof", "range": "consumer reads through 0x280F86"},
      "diagnosticState": {"schemaVersion": 1, "fixedScalarRecord": True, "producer": "nonblocking busy-bit; drop on contention", "derefInRelay": False, "readBufferInRelay": False, "fileIoInRelay": False, "drain": "existing stable worker path not integrated in this delivery"},
      "runtimeEligibility": {"installNow": False, "gameHookInstallAuthorized": False, "currentSourceDesignationAuthorized": False, "reason": "same-frame/lifetime, producer ownership, and production drain remain unproven"},
      "semanticClaims": {"field38MeaningProven": False, "field78MeaningProven": False, "selectionPreviewOwnerProven": False}
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--exe",type=Path,default=EXE); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args(); out=build(a.exe); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")

if __name__ == "__main__": main()
