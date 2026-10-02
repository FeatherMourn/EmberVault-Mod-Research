#!/usr/bin/env python3
"""Offline CODE-0005D parent-frame/lifetime and correlation qualification."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from tools.SemanticActionObserver.scan_blueprint_selection_authority_static import StaticImage

EXE = ROOT.parent.parent / "enshrouded.exe"
SHA = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
DEPLOYED = "C3AAF673001CBE08C508F703C0D9219836067A7A9818A4A9473D3BA49F89A801"

def hx(v): return f"0x{v:X}"

def build(exe: Path) -> dict:
    parent = json.loads((ROOT / "bridge/parent_call_relay_correlation_static_map.json").read_text(encoding="utf-8"))
    cap = json.loads((ROOT / "bridge/observer_trampoline_capability_map.json").read_text(encoding="utf-8"))
    if parent.get("site", {}).get("originalBytes") != "E8 D3 54 65 00" or cap.get("runtimeEligibility", {}).get("gameHookInstallAuthorized") is not False:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY")
    image = StaticImage(exe)
    if image.digest != SHA: raise RuntimeError("BUILD_MISMATCH")
    xs = image.disassemble(0x2807C8, 0x280F86)
    rsp = [{"rva": hx(i.address), "instruction": i.mnemonic + (" " + i.op_str if i.op_str else "")} for i in xs if any(r in ("rsp", "esp") for r in i.regs_write)]
    rbp = [{"rva": hx(i.address), "instruction": i.mnemonic + (" " + i.op_str if i.op_str else "")} for i in xs if any(r in ("rbp", "ebp") for r in i.regs_write)]
    aliases, calls = [], []
    for i in image.disassemble(0x28088B, 0x280F86):
        s = i.op_str.lower()
        if i.mnemonic == "call": calls.append({"rva": hx(i.address), "target": hx(int(i.operands[0].imm)) if i.operands and i.operands[0].type == 2 else "unknown"})
        if (i.mnemonic.startswith("mov") or i.mnemonic.startswith("lea")) and ("[rbp + 8]" in s or "[rbp + 0x48]" in s):
            aliases.append({"rva": hx(i.address), "instruction": i.mnemonic + " " + i.op_str, "possibleCalleeSideEffect": i.address in (0x280945, 0x280B23)})
    return {
      "schemaVersion": 1, "codeId": "CODE-0005D", "analysisMode": "OFFLINE_STATIC_PLUS_NATIVE_HARNESS_ONLY",
      "build": {"revision": 1076226, "exeSha256": image.digest, "deployedDllSha256": DEPLOYED},
      "parentEvidence": {"code0005c": "CORRELATION_UNPROVEN", "relayCallRva": "0x2807C8", "helperTargetRva": "0x8D5CA0"},
      "frameAnalysis": {"interval": ["0x2807C8", "0x280F86"], "rspWrites": rsp, "rbpWrites": rbp, "effectiveRspStatus": "PROVEN_STATIC_BUILD_1076226" if not rsp else "UNRESOLVED_PATH_VARIANCE", "rbpRelationStatus": "PROVEN_STATIC_BUILD_1076226" if not rbp else "UNRESOLVED_PATH_VARIANCE", "equations": {"parentRsp": "RBP-0x100", "relayEntryRsp": "RBP-0x108", "buffer": "relayEntryRSP+0xD8", "bufferPlus38": "relayEntryRSP+0x110", "bufferPlus78": "relayEntryRSP+0x150", "relayReturn": "moduleBase+0x2807CD", "downstreamReturn": "moduleBase+0x280F8B"}, "equationsValidated": False},
      "outputRange": {"bufferExpression": "RBP-0x30", "allocation": "dynamic sub rsp,rax after RBP setup", "bufferInFrame": "UNPROVEN", "field38": "TARGET_READ_RANGE_UNPROVEN", "field78": "TARGET_READ_RANGE_UNPROVEN"},
      "postConsumerHazards": {"field38": {"status": "ALIAS/CALLEE_SIDE_EFFECT_UNRESOLVED", "directWrites": [], "aliases": aliases}, "field78": {"status": "ALIAS/CALLEE_SIDE_EFFECT_UNRESOLVED", "directWrites": [], "aliases": aliases}, "callsReceivingAliases": calls, "boundedResult": "NO_STATIC_WRITE_FOUND_IN_BOUNDED_PATH does not prove value immutability"},
      "correlationGate": {"generationCoherence": True, "consumeOnce": True, "sameThreadStackRange": "UNPROVEN", "stackMarker280F8B": True, "safeBufferReads": True, "status": "CORRELATION_UNPROVEN", "failureMode": "discard stale/racing/mismatched snapshots"},
      "producerModel": {"concurrentProducers": "REJECT/DROP in SPSC design", "reentrancy": "UNPROVEN", "threadOwnership": "UNPROVEN", "spscCompatibility": "UNPROVEN"},
      "unwind": {"status": "UNWIND_SUPPORT_UNSOLVED", "normalReturnHarnessOnly": True, "exceptionHarness": "not claimed"},
      "drainIntegration": {"existingWorker": "DRAIN_HOST_CANDIDATE_PARTIAL", "productionIntegration": "DRAIN_INTEGRATION_UNSOLVED"},
      "siteEligibility": {"status": "PARTIAL_STATIC", "installNow": False, "gameHookInstallAuthorized": False, "currentSourceDesignationAuthorized": False, "blockers": ["frame equations not connected to runtime stack evidence", "buffer/field bounds and lifetime unproven", "callee alias side effects unresolved", "SPSC/thread/reentrancy unproven", "unwind exception safety unresolved", "drain integration unresolved"]},
      "semanticClaims": {"field38MeaningProven": False, "field78MeaningProven": False, "selectionPreviewOwnerProven": False, "worldAuthorityProven": False}
    }

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--exe", type=Path, default=EXE); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    result = build(a.exe); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

if __name__ == "__main__": raise SystemExit(main())
