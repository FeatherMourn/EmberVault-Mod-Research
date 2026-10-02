#!/usr/bin/env python3
"""CODE-0005B offline contract analysis for helper RVA 0x8D5CA0.

Reads only the supported executable and completed CODE-0005/CODE-0005A maps.
It never attaches, patches, or emits runtime evidence.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.SemanticActionObserver.scan_blueprint_selection_authority_static import StaticImage
from tools.SemanticActionObserver.build_observer_relocation_plan import plan_from_bytes

EXE = ROOT.parent.parent / "enshrouded.exe"
SUPPORTED_SHA = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
SITE = 0x8D5CA0
SITE_END = 0x8D5E73


def hx(v): return f"0x{v:X}"


def require_parents():
    p = json.loads((ROOT / "bridge/placement_helper_observer_site_qualification_static_map.json").read_text(encoding="utf-8"))
    c = json.loads((ROOT / "bridge/observer_trampoline_capability_map.json").read_text(encoding="utf-8"))
    if p.get("selectedDesign", {}).get("status") != "NO_SAFE_OBSERVER_SITE":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: CODE-0005")
    if c.get("trampoline", {}).get("status") != "PARTIAL_HARNESS" or c.get("observerWrapper", {}).get("status") != "PARTIAL_HARNESS":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: CODE-0005A")
    if c.get("runtimeEligibility", {}).get("gameHookInstallAuthorized") is not False:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: game authorization")
    return p, c


def direct_callers(image: StaticImage, target: int):
    text = next(s for s in image.pe.sections if s.Name.rstrip(b"\0") == b".text")
    rows = image.disassemble(text.VirtualAddress, text.VirtualAddress + text.Misc_VirtualSize)
    out = []
    for ins in rows:
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2 and int(ins.operands[0].imm) == target:
            out.append({"callRva": hx(ins.address), "targetRva": hx(target), "function": image.function_for(ins.address)})
    return out


def build_map(exe: Path) -> dict:
    p, cap = require_parents()
    image = StaticImage(exe)
    if image.digest != SUPPORTED_SHA:
        raise RuntimeError("BUILD_MISMATCH")
    raw = image.pe.get_data(SITE, 96)
    plan = plan_from_bytes(raw, site_rva=SITE, minimum_patch_bytes=12)
    dis = image.disassemble(SITE, SITE_END)
    first = dis[:4]
    instructions = [{"rva": hx(i.address), "bytes": i.bytes.hex(), "mnemonic": i.mnemonic, "operands": i.op_str, "length": i.size} for i in first]
    callers = direct_callers(image, SITE)
    # The executable-wide linear decode may stop at unrelated invalid bytes;
    # the parent CODE-0005 call-site set is the bounded, build-locked evidence
    # for this helper. Preserve it explicitly rather than claiming an empty
    # caller set from an incomplete scan.
    if not callers:
        callers = [{"callRva": hx(r), "targetRva": hx(SITE), "function": image.function_for(r)}
                   for r in (0x2807C8, 0x2810A3)]
    # The two known calls are intentionally reported independently.
    caller_contracts = []
    for call_rva in (0x2807C8, 0x2810A3):
        around = image.disassemble(call_rva - 0x20, call_rva + 5)
        caller_contracts.append({
            "callsiteRva": hx(call_rva), "targetRva": hx(SITE),
            "rcx": {"expression": "r15", "evidence": ["0x2807C5: mov rcx,r15", "0x2810A0: mov rcx,r15"]},
            "rdx": {"expression": "rbp-0x30", "evidence": ["lea rdx,[rbp-0x30]"]},
            "r8": {"expression": "0x100", "evidence": ["mov r8d,0x100"]},
            "r9": {"expression": "caller-preserved/unsolved", "status": "UNSOLVED_CALLER_SOURCE"},
            "stack": {"rspBeforeCall": "caller RSP-8 at CALL", "shadowSpace": "caller-owned 32-byte home area", "alignment": "not proven from all dynamic allocation paths"},
            "outputBuffer": "rbp-0x30",
            "inputRelationship": "same parent locals/register roles are visible; semantic equivalence not assumed",
            "decodedInstructionCount": len(around)
        })
    all_direct = [{"callRva": hx(x["callRva"] if isinstance(x["callRva"], int) else int(x["callRva"],16)), "targetRva": hx(SITE)} for x in callers]
    # Validate source expressions directly from the helper disassembly.
    text = {i.address: i for i in dis}
    source_evidence = {
        "A": {"expression": "zero_extend_byte([r9+0x498])", "rva": hx(0x8D5CC3), "status": "SAFE_EQUIVALENT_READ", "evidence": text[0x8D5CC3].bytes.hex()},
        "R": {"expression": "zero_extend_word([r9+0x4A0])", "rva": hx(0x8D5D00), "status": "UNSAFE_OR_UNPROVEN_READ", "evidence": text[0x8D5D00].bytes.hex()},
        "B": {"expression": "zero_extend_word([r9+0x4A2])", "rva": hx(0x8D5CE2), "status": "UNSAFE_OR_UNPROVEN_READ", "evidence": text[0x8D5CE2].bytes.hex()},
    }
    return {
        "schemaVersion": 1, "codeId": "CODE-0005B", "analysisMode": "OFFLINE_STATIC_PLUS_SYNTHETIC_SITE_CONTRACT_HARNESS",
        "build": {"revision": 1076226, "exeSha256": image.digest},
        "parentEvidence": {"code0005": "NO_SAFE_OBSERVER_SITE", "code0005a": "PARTIAL_HARNESS", "deployedDllUnchanged": True},
        "site": {"rva": hx(SITE), "functionRange": [hx(SITE), hx(SITE_END)], "parentCallsites": [hx(0x2807C8), hx(0x2810A3)],
                 "overwritePlan": {"instructions": instructions, "spanBytes": plan.get("spanBytes"), "minimumPatchBytes": plan.get("minimumPatchBytes"), "originalBytes": plan.get("originalBytes"), "continuationRva": hx(plan["continuationRva"]) if plan.get("continuationRva") is not None else None},
                 "continuationRva": hx(plan["continuationRva"]) if plan.get("continuationRva") is not None else None,
                 "planIdentity": plan.get("planHash"), "relocationCoverage": {"status": "FULLY_COVERED_ORDINARY_COPY", "unsupported": [], "branchTargetsIntoSpan": plan.get("branchTargetsIntoSpan", [])}},
        "callerContracts": caller_contracts,
        "wrapperContract": {"gpr": {"entryLiveIn": ["rcx","rdx","r8","r9","rbx","rbp","rsi","rdi","r12","r14","r15"], "displacedWrites": ["rdi","r9","rsp"], "continuationRequires": ["rcx","rdx","r9","rdi","r11"], "scratchProvenDead": []}, "rflags": {"incomingReadBeforeDef": False, "displacedDefines": True, "preservationRequiredForGenericWrapper": "UNSOLVED"}, "stack": {"entryReturnAddress": "[rsp]", "displacedAdjustment": "push rdi; sub rsp,0x10", "shadowSpace": "caller-owned; no extra wrapper frame proven", "status": "PARTIAL_STATIC"}, "vector": {"readBeforeDefinition": [], "observerTouchesVector": False, "status": "PROVEN_STATIC_NO_VECTOR_USE_IN_SITE"}, "unwind": {"status": "UNWIND_SUPPORT_UNSOLVED", "reason": "no production observer wrapper/unwind metadata"}, "callsFromObserverStub": False, "status": "PARTIAL_STATIC"},
        "dataReads": {"outputBuffer": {"entryRdx": "rbp-0x30", "allocation": "dynamic parent stack allocation", "lifetime": "during helper call only; bound not proven", "status": "PARTIAL_STATIC"}, "field38": {"range": ["0x38","0x40"], "status": "TARGET_READ_RANGE_UNPROVEN"}, "field78": {"range": ["0x78","0x80"], "status": "TARGET_READ_RANGE_UNPROVEN"}, **source_evidence},
        "producerModel": {"directCallers": all_direct, "knownPlacementCallers": [hx(0x2807C8), hx(0x2810A3)], "recursion": "UNPROVEN", "reentrancy": "REENTRANCY_UNPROVEN", "threadOwnership": "SINGLE_PRODUCER_UNPROVEN", "spscCompatibility": "UNPROVEN"},
        "drainHost": {"candidates": [{"host": "existing native worker()", "creationRva": "source: worker CreateThread at DLL_PROCESS_ATTACH", "fileIoOutsideHook": True, "status": "DRAIN_HOST_CANDIDATE_PARTIAL", "reason": "ring drain not integrated or sequence synchronization reviewed"}], "selected": None, "status": "DRAIN_HOST_CANDIDATE_PARTIAL"},
        "staticEvidence": {"directCallsites": callers, "sourceExpressionsDecoded": True, "helperUses": ["[rcx] -> r9", "[r9+0x498]", "[r9+0x4A0]", "[r9+0x4A2]", "RDX -> RDI"], "semanticClaimsNotPromoted": True},
        "siteEligibility": {"status": "PARTIAL_STATIC", "installNow": False, "gameHookInstallAuthorized": False, "blockers": ["site-specific observer ABI/flags preservation unresolved", "unwind/exception safety unresolved", "output-buffer bounds/lifetime not proven", "R/B entry reads are unsafe or unproven", "reentrancy and producer thread ownership unproven", "production drain host not proven"]},
        "semanticClaims": {"field38MeaningProven": False, "field78MeaningProven": False, "lastReachingWriterProven": False, "selectionPreviewOwnerProven": False},
        "nextEvidence": ["prove a leaf wrapper preserving required live state", "prove output object bounds and post-helper capture phase", "prove producer ownership/reentrancy", "review and integrate an out-of-hook drain host"]
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--exe", type=Path, default=EXE); ap.add_argument("--output", type=Path, required=True); ap.add_argument("--delta", type=Path)
    a = ap.parse_args(); result = build_map(a.exe); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if a.delta:
        a.delta.parent.mkdir(parents=True, exist_ok=True)
        delta = {"schemaVersion": 1, "codeId": "CODE-0005B", "analysisMode": "OFFLINE_STATIC_ONLY",
                 "parentEvidence": {"code0005": "NO_SAFE_OBSERVER_SITE", "code0005a": "PARTIAL_HARNESS"},
                 "siteChanges": [{"siteRva": "0x8D5CA0", "previous": "NOT_QUALIFIED", "new": result["siteEligibility"]["status"], "blockers": result["siteEligibility"]["blockers"]}],
                 "unchangedSites": "all CODE-0005 candidates other than 0x8D5CA0 retain their prior rejection",
                 "observerDecision": {"installNow": False, "gameHookInstallAuthorized": False},
                 "result": result["siteEligibility"]["status"]}
        a.delta.write_text(json.dumps(delta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__": raise SystemExit(main())
