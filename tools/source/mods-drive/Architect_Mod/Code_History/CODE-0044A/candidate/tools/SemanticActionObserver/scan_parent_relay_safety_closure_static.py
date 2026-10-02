#!/usr/bin/env python3
"""Generate CODE-0005E offline relay-safety closure map."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from tools.SemanticActionObserver.scan_blueprint_selection_authority_static import StaticImage
EXE = ROOT.parent.parent / "enshrouded.exe"
SHA = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
DLLSHA = "C3AAF673001CBE08C508F703C0D9219836067A7A9818A4A9473D3BA49F89A801"

def build(exe: Path) -> dict:
    parent = json.loads((ROOT / "bridge/parent_frame_lifetime_correlation_static_map.json").read_text(encoding="utf-8"))
    relay = json.loads((ROOT / "bridge/parent_call_relay_correlation_static_map.json").read_text(encoding="utf-8"))
    if parent.get("siteEligibility", {}).get("installNow") is not False or relay.get("site", {}).get("originalBytes") != "E8 D3 54 65 00":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY")
    image = StaticImage(exe)
    if image.digest != SHA: raise RuntimeError("BUILD_MISMATCH")
    helper = image.disassemble(0x8D5CA0, 0x8D5CCB)
    first_flag = next((i for i in helper if i.mnemonic in ("cmp", "test")), None)
    return {
      "schemaVersion": 1, "codeId": "CODE-0005E", "analysisMode": "OFFLINE_STATIC_PLUS_NATIVE_HARNESS_ONLY",
      "build": {"revision": 1076226, "exeSha256": image.digest, "deployedDllSha256": DLLSHA},
      "parentEvidence": {"code0005d": "PARTIAL_STATIC", "code0005c": "CORRELATION_UNPROVEN", "relayCallRva": "0x2807C8", "helperTargetRva": "0x8D5CA0"},
      "publication": {"slotCount": 8, "powerOfTwo": True, "ticket": "uint64 monotonic modulo 2^64", "perSlotSequence": True, "busyState": True, "scalarFields": ["generation", "capturedRdxBuffer", "capturedParentRbp", "capturedRelayEntryRsp", "capturedRcx", "capturedR8", "capturedR9"], "producer": {"leaf": True, "calls": False, "heap": False, "fileIo": False, "blocking": False, "stackFrame": False, "dropOnContention": True, "falseAcceptancePolicy": "drop/reject"}, "concurrency": "bounded multi-slot model; runtime SPSC compatibility not claimed"},
      "matcher": {"gates": ["coherent publication sequence", "generation nonzero/unconsumed", "nonzero buffer/rbp/entryRsp", "buffer == rbp-0x30", "entryRsp == rbp-0x108", "[entryRsp] == moduleBase+0x280F8B", "known stack marker", "same stack allocation identity", "downstream buffer ranges readable", "sequence unchanged after reads", "exactly one candidate", "atomic consume-once"], "outputs": {"downstreamSnapshot38": "VALUE_STABILITY_AFTER_CONSUMPTION=UNPROVEN", "downstreamSnapshot78": "VALUE_STABILITY_AFTER_CONSUMPTION=UNPROVEN"}, "status": "HARNESS_FAIL_CLOSED"},
      "controlFlow": {"originalCallBytes": "E8 D3 54 65 00", "target": "0x8D5CA0", "return": "0x2807CD", "relayCalls": False, "returnRewrite": False, "rspChanged": False, "nonvolatileChanged": False, "xmmChanged": False, "rflags": {"status": "CONDITIONALLY_SAFE_SITE_CONTRACT", "firstHelperFlagConsumer": f"0x{first_flag.address:X}" if first_flag else None, "evidence": "helper establishes flags at cmp/test before flag-dependent branch"}},
      "unwind": {"status": "UNWIND_SUPPORT_UNSOLVED", "normalReturnHarness": True, "exceptionHarness": "not proven"},
      "drain": {"host": "existing native worker", "status": "DRAIN_INTEGRATION_UNSOLVED", "producerIo": False, "secondQueue": False},
      "lifecycle": {"patchWidth": 5, "exactExpectedBytes": True, "nearRel32RangeChecked": True, "syntheticInstallRollback": True, "freeAfterRestore": True, "defaultInstall": False, "oneShot": True},
      "runtimeEligibility": {"status": "PARTIAL_STATIC_OR_HARNESS", "installNow": False, "gameHookInstallAuthorized": False, "currentSourceDesignationAuthorized": False, "reason": "publication/matcher harness is fail-closed, but runtime same-stack evidence, unwind, and drain integration remain unresolved"},
      "semanticClaims": {"field38MeaningProven": False, "field78MeaningProven": False, "selectionPreviewOwnerProven": False, "worldAuthorityProven": False},
      "nextEvidence": ["complete exception/unwind harness or register staging unwind metadata", "prove bounded worker drain integration", "obtain explicit review before any one-shot runtime capture"]
    }

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--exe", type=Path, default=EXE); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    result = build(a.exe); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

if __name__ == "__main__": raise SystemExit(main())
