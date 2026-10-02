#!/usr/bin/env python3
"""Generate CODE-0005A capability and offline requalification artifacts."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOYED_SHA = "C3AAF673001CBE08C508F703C0D9219836067A7A9818A4A9473D3BA49F89A801"
SUPPORTED_EXE_SHA = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_map(parent):
    candidates = []
    for row in parent.get("candidateSites", []):
        rel = row.get("relocationRequirements", {})
        classes = []
        if rel.get("ripRelative"): classes.append("RIP_RELATIVE")
        if rel.get("relativeControlFlow"): classes.append("RELATIVE_CONTROL_FLOW")
        candidates.append({
            "siteId": row.get("siteId"), "rva": row.get("rva"),
            "parentStatus": row.get("status"), "relocationClasses": classes,
            "requalified": False,
            "reason": "site-specific ABI/lifetime/drain proof remains unresolved"
        })
    return {
        "schemaVersion": 1, "codeId": "CODE-0005A",
        "analysisMode": "OFFLINE_AND_NATIVE_HARNESS",
        "parentEvidence": {"delivery": "CODE-0005", "result": "NO_SAFE_OBSERVER_SITE",
                           "map": "bridge/placement_helper_observer_site_qualification_static_map.json",
                           "supportedExecutableSha256": SUPPORTED_EXE_SHA},
        "trampoline": {
            "wholeInstructionSelection": "OFFLINE_CAPSTONE_BOUNDARY_PLANNER",
            "minimumPatchEncodingBytes": 12,
            "supportedRelocations": [{"class": "ordinary_non_rip", "status": "SUPPORTED_HARNESS_PROVEN"}],
            "unsupportedRelocations": [
                {"class": "RIP_RELATIVE", "status": "UNSUPPORTED_FAIL_CLOSED", "reason": "no semantics-preserving emitter yet"},
                {"class": "RELATIVE_CALL", "status": "UNSUPPORTED_FAIL_CLOSED", "reason": "call/return semantics require reviewed emitter"},
                {"class": "RELATIVE_JMP", "status": "UNSUPPORTED_FAIL_CLOSED"},
                {"class": "RELATIVE_JCC", "status": "UNSUPPORTED_FAIL_CLOSED"},
                {"class": "UNSUPPORTED_OR_AMBIGUOUS", "status": "UNSUPPORTED_FAIL_CLOSED"}],
            "planIdentity": {"algorithm": "SHA-256", "inputs": ["siteRva", "originalBytes", "decodedInstructions", "continuationRva", "relocationRecipe"]},
            "installRollback": {"expectedBytes": True, "overlapCheck": True, "syntheticOnly": True, "exactRestore": "HARNESS_PROVEN"},
            "unwindSupport": "UNWIND_SUPPORT_UNSOLVED",
            "status": "PARTIAL_HARNESS"
        },
        "observerWrapper": {
            "gprContract": {"reads": "site-supplied scalar values only", "writesInternal": "Architect-owned ring memory", "restored": "no game registers in SPSC producer"},
            "rflagsContract": "UNSOLVED_FOR_GENERIC_WRAPPER",
            "stackContract": "leaf producer; no frame or C call in native publisher; site wrapper not implemented",
            "vectorContract": "no XMM/YMM use in publisher; future wrapper must qualify live vector state",
            "reentrancyContract": "SPSC only; nested/reentrant producer is rejected by site gate",
            "status": "PARTIAL_HARNESS"
        },
        "diagnostics": {
            "producerModel": "preallocated fixed SPSC ring; scalar-only event copy",
            "capacity": 64, "recordSize": 104, "concurrencyModel": "single producer / single consumer only",
            "overflowBehavior": "drop-newest and increment bounded counter",
            "forbiddenHotPathCalls": [],
            "drainModel": "consumer copies one event; formatting/export is host responsibility outside producer",
            "drainHostStatus": "UNSOLVED", "status": "HARNESS_PROVEN"
        },
        "nativeHarness": {"tests": ["synthetic ring ordering/overflow", "synthetic byte transaction rollback", "planner Python suite"], "status": "PARTIAL"},
        "runtimeEligibility": {"infrastructureReadyForSiteRequalification": False, "gameHookInstallAuthorized": False,
                               "reason": "wrapper ABI, relocation classes, unwind, lifetime, and production drain are not all proven"},
        "siteCandidates": candidates,
        "nextEvidence": ["review relocation emitter or keep rejecting relative/RIP forms", "prove wrapper ABI/flags/vector/unwind", "prove an out-of-hook drain host"]
    }


def requal_map(parent, capability):
    sites = []
    for row in parent.get("candidateSites", []):
        sites.append({"siteId": row.get("siteId"), "rva": row.get("rva"),
                      "originalStatus": row.get("status"),
                      "status": "NOT_QUALIFIED",
                      "reason": "CODE-0005A planner/diagnostic harness exists, but site ABI/lifetime/drain proof is unresolved",
                      "infrastructureUsed": True, "installNow": False})
    return {"schemaVersion": 1, "codeId": "CODE-0005A", "analysisMode": "OFFLINE_STATIC_ONLY",
            "parentEvidence": {"delivery": "CODE-0005", "result": "NO_SAFE_OBSERVER_SITE"},
            "capabilityMap": "bridge/observer_trampoline_capability_map.json", "sites": sites,
            "result": "NO_SAFE_OBSERVER_SITE", "infrastructureReadyForSiteRequalification": False,
            "observerDecision": {"installNow": False, "gameHookInstallAuthorized": False,
                                  "reason": "No candidate satisfies all site-specific ABI/lifetime/drain requirements"},
            "runtimeExperiment": False}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output", type=Path, required=True); ap.add_argument("--delta", type=Path, required=True)
    args = ap.parse_args()
    parent = load(ROOT / "bridge/placement_helper_observer_site_qualification_static_map.json")
    if parent.get("selectedDesign", {}).get("status") != "NO_SAFE_OBSERVER_SITE" or parent.get("observerDecision", {}).get("installNow") is not False:
        raise SystemExit("MISSING_OR_DIVERGENT_PARENT_DELIVERY")
    capability = build_map(parent); delta = requal_map(parent, capability)
    args.output.parent.mkdir(parents=True, exist_ok=True); args.delta.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(capability, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.delta.write_text(json.dumps(delta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__": raise SystemExit(main())
