#!/usr/bin/env python3
"""CODE-0005 Gate 1: offline qualification of possible helper observation sites.

This module only decodes the supported on-disk PE and the CODE-0004 map.  It
does not attach to a process, patch bytes, install a hook, or produce a runtime
capture.  The result is intentionally conservative: no site is promoted to a
staged observer unless every ABI/relocation/lifetime requirement is proven.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import capstone

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from tools.SemanticActionObserver.scan_blueprint_selection_authority_static import (  # noqa: E402
    StaticImage, build_basic_blocks, call_target, canonical_reg, hx, instruction_row,
)

SUPPORTED_SHA256 = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
DEPLOYED_SHA256 = "C3AAF673001CBE08C508F703C0D9219836067A7A9818A4A9473D3BA49F89A801"
PARENT_MAP = "bridge/placement_computed_destination_arithmetic_static_map.json"
PARENT_START, PARENT_END = 0x280790, 0x2810E8
MIN_OVERWRITE = 15  # write_abs_jump() and the existing stable hook use 15 bytes


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parent_gate(parent: dict[str, Any]) -> None:
    if parent.get("analysisMode") != "OFFLINE_STATIC_ONLY" or parent.get("build", {}).get("sha256") != SUPPORTED_SHA256:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: CODE-0004 mode/fingerprint")
    if parent.get("convergenceDelta", {}).get("status") != "PARTIAL_STATIC":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: CODE-0004 convergence")
    if parent.get("observerDecision", {}).get("install") is not False:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: CODE-0004 observer gate")
    targets = parent.get("targets", {})
    if targets.get("field38", {}).get("byteRange") != [0x38, 0x40] or targets.get("field78", {}).get("byteRange") != [0x78, 0x80]:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: target ranges")
    if targets.get("field38", {}).get("consumerRva") != "0x280897" or targets.get("field78", {}).get("consumerRva") != "0x28088B":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: consumers")
    writes = {row.get("rva") for row in parent.get("helper8D5CA0", {}).get("writes", [])}
    expected = {"0x8D5D35", "0x8D5D77", "0x8D5DA3", "0x8D5DCC", "0x8D5DF7", "0x8D5E25", "0x8D5E46"}
    if writes != expected:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: primary writes")
    if parent.get("helper8DA7C0", {}).get("computedDestination8DA992", {}).get("normalizedExpression") != "output + (8*G + 8*A + 8*C + 16*B + 8*D + 8*E + 8*F + 8)":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: G expression")
    for helper in (parent.get("helper8D5CA0", {}), parent.get("helper8DA7C0", {})):
        if helper.get("outputBaseAlias", {}).get("instruction") not in ("mov rdi, rdx", "mov rdi, rdx"):
            raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: output alias")


def span_for(instructions: list[Any], start: int, minimum: int = MIN_OVERWRITE) -> tuple[list[Any], bool]:
    chosen, total = [], 0
    for ins in instructions:
        if ins.address < start:
            continue
        chosen.append(ins); total += ins.size
        if total >= minimum:
            return chosen, total == minimum
    return chosen, total == minimum


def branch_kind(ins: Any) -> str | None:
    if ins.group(capstone.CS_GRP_CALL): return "CALL"
    if ins.group(capstone.CS_GRP_JUMP): return "JUMP"
    return None


def inspect_site(image: StaticImage, site_id: str, rva: int, role: str,
                 extra_reason: str = "") -> dict[str, Any]:
    fn = image.function_for(rva)
    function_start = int(fn["startRva"], 16) if fn else rva
    around = image.disassemble(max(function_start, rva - 16), rva + 48)
    # Decode the overwrite span from the candidate RVA itself.  Starting a
    # Capstone stream in the middle of a preceding instruction can otherwise
    # hide the first candidate instruction (notably at 0x8D5CA0).
    candidate_stream = image.disassemble(rva, rva + 64)
    span, exact = span_for(candidate_stream, rva)
    cfg = build_basic_blocks(image.disassemble(PARENT_START, PARENT_END)) if PARENT_START <= rva < PARENT_END else {"blocks": [], "predecessors": {}}
    branch_targets = []
    relative = []
    rip_relative = []
    for ins in span:
        kind = branch_kind(ins)
        if kind:
            relative.append({"rva": hx(ins.address), "kind": kind, "targetRva": hx(call_target(ins))})
            if ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
                branch_targets.append(int(ins.operands[0].imm))
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base and canonical_reg(ins.reg_name(op.mem.base)) == "rip":
                rip_relative.append(instruction_row(ins))
    start, end = rva, rva + sum(i.size for i in span)
    branch_into = [hx(t) for t in branch_targets if start < t < end]
    split = not exact
    reasons = []
    if split: reasons.append("existing 15-byte detour span would split an instruction")
    if relative: reasons.append("overwrite span contains relative control flow requiring relocation")
    if rip_relative: reasons.append("overwrite span contains RIP-relative memory requiring relocation")
    if branch_into: reasons.append("a branch target lands inside the overwrite span")
    if extra_reason: reasons.append(extra_reason)
    if role == "helper_entry":
        reasons.append("no reviewed helper-entry observer ABI/return-state wrapper exists; helper output lifetime and nonblocking drain are not proven for all callers")
    return {
        "siteId": site_id, "role": role, "rva": hx(rva), "function": fn,
        "decodedAround": [instruction_row(i) for i in around],
        "overwrite": {"minimumBytes": MIN_OVERWRITE, "wholeInstructionSpanBytes": sum(i.size for i in span),
                       "exactMinimumBoundary": exact, "instructions": [instruction_row(i) for i in span],
                       "continuationRva": hx(end)},
        "controlFlow": {"relativeCallsJumps": relative, "branchTargetsInsideSpan": branch_into,
                        "cfgAvailable": bool(cfg.get("blocks"))},
        "relocationRequirements": {"ripRelative": rip_relative, "relativeControlFlow": relative,
                                    "status": "UNRESOLVED" if (relative or rip_relative or split) else "NONE"},
        "registerFlagsStack": {"registers": "not clobber-proven for a new helper wrapper", "eflags": "not proven",
                                "stackAlignment": "caller-dependent at helper entry; wrapper contract not reviewed",
                                "nonvolatile": "requires a new reviewed ABI shim", "xmm": "not proven"},
        "liveness": {"outputBufferPointer": role in {"helper_entry", "parent_post_helper"},
                     "targetFieldsReadable": role == "parent_pre_resolver",
                     "runtimeInputsARB G": False, "status": "UNPROVEN"},
        "frequencyReentrancy": "helper may be called by multiple paths; no bounded placement-only filter is proven at this site",
        "existingHookConflict": False,
        "expectedBytes": span[0].bytes.hex(" ").upper() if span else "",
        "uninstall": "exact original-byte restore is mechanically possible only after a valid whole-instruction span and reviewed thunk",
        "status": "NOT_QUALIFIED" if reasons else "PARTIAL_STATIC",
        "disqualificationReasons": reasons,
    }


def qualify_synthetic(candidate: dict[str, Any]) -> dict[str, Any]:
    """Pure rule evaluator used by unit tests and kept independent of PE data."""
    reasons = list(candidate.get("reasons", []))
    if candidate.get("splitInstruction"): reasons.append("split instruction")
    if candidate.get("ripRelative"): reasons.append("RIP-relative relocation")
    if candidate.get("relativeBranch"): reasons.append("relative control flow")
    if candidate.get("branchIntoSpan"): reasons.append("branch target inside span")
    if candidate.get("flagsNotPreserved"): reasons.append("live flags not preserved")
    if candidate.get("stackMisaligned"): reasons.append("stack alignment mismatch")
    if candidate.get("hookOverlap"): reasons.append("existing hook overlap")
    if candidate.get("expectedBytesMismatch"): reasons.append("expected-byte mismatch")
    if not candidate.get("outputLifetimeProven", False): reasons.append("output-buffer lifetime unproven")
    return {"status": "NOT_QUALIFIED" if reasons else "QUALIFIED_SAFE_OBSERVER_SITE", "reasons": reasons}


def analyze(image: StaticImage, parent: dict[str, Any]) -> dict[str, Any]:
    parent_gate(parent)
    sites = [
        inspect_site(image, "parent_call_2807B6", 0x2807B6, "parent_call", "relative helper CALL is not relocatable by the existing raw-copy trampoline"),
        inspect_site(image, "parent_call_2807C8", 0x2807C8, "parent_call"),
        inspect_site(image, "parent_call_2810A3", 0x2810A3, "parent_call"),
        inspect_site(image, "helper_entry_8DA7C0", 0x8DA7C0, "helper_entry"),
        inspect_site(image, "helper_entry_8D5CA0", 0x8D5CA0, "helper_entry"),
        inspect_site(image, "parent_post_helper_2807CD", 0x2807CD, "parent_post_helper"),
        inspect_site(image, "parent_pre_resolver_280897", 0x280897, "parent_pre_resolver"),
    ]
    rejected = [
        {"rva": "0xCB4B50", "reason": "boot ACCESS_VIOLATION from resolver detour", "hookEligible": False},
        {"rva": "0x3E2CD0", "reason": "function-entry trampoline corrupted RAX", "hookEligible": False},
        {"rva": "0x280F86", "reason": "selector detour ACCESS_VIOLATION", "hookEligible": False},
        {"rva": "0xCA5BC0", "reason": "rejected absent reviewed design", "hookEligible": False},
        {"rva": "0xCA90E0", "reason": "rejected absent reviewed design", "hookEligible": False},
    ]
    # The helper-entry candidates have no reviewed wrapper/diagnostic ABI in the
    # current runtime; all parent boundaries have split/relocation hazards.
    reasons = [s for s in sites if s["status"] != "QUALIFIED_SAFE_OBSERVER_SITE"]
    return {
        "schemaVersion": 1, "tool": "scan_placement_helper_observer_site_qualification_static.py",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "parentEvidence": {"delivery": "CODE-0004", "map": PARENT_MAP, "status": "PARTIAL_STATIC"},
        "build": {"revision": 1076226, "sha256": image.digest, "fingerprintMatches": image.digest == SUPPORTED_SHA256,
                   "supportedExecutableSha256": SUPPORTED_SHA256},
        "knownRejectedSites": rejected,
        "candidateSites": sites,
        "selectedDesign": {"status": "NO_SAFE_OBSERVER_SITE", "sites": [],
            "reason": "All parent call/post-helper boundaries require split-instruction or relocation work, while helper-entry observation would require a new unreviewed ABI/return-state wrapper and caller/lifetime/diagnostic-drain proof. Gate 1 therefore fails closed.",
            "capturesPreState": False, "capturesPostState": False, "capturesRuntimeInputs": False,
            "capturesParentPathIdentity": False},
        "safety": {"gameStateWrites": False, "argumentSubstitution": False, "returnValueSubstitution": False,
                    "controlFlowMutation": False, "fileIoInHook": False, "heapAllocationInHook": False,
                    "blockingInHook": False, "cleanUninstallRequired": True, "failClosed": True},
        "observerDecision": {"installNow": False, "stagingBuildEligible": False,
                             "reason": "NO_SAFE_OBSERVER_SITE; no Phase B staging observer is built"},
        "deployedDllSha256": DEPLOYED_SHA256,
        "nextEvidence": ["CODE-0005 requires a reviewed helper-entry ABI/trampoline that preserves all state and a proven nonblocking diagnostic drain, or offline debugger evidence of a lower-risk boundary. Do not install a detour from this map."]}


def render_doc(result: dict[str, Any]) -> str:
    lines = ["# CODE-0005 Placement Helper Observer Site Qualification", "",
             f"- Mode: `{result['analysisMode']}`; build revision `{result['build']['revision']}`.",
             f"- Executable SHA-256: `{result['build']['sha256']}`.",
             "- No process access, hooks, executable writes, or game-memory writes.", "",
             "## Candidate sites", "",
             "| Site | RVA | Status | Reason |", "|---|---:|---|---|"]
    for s in result["candidateSites"]:
        lines.append(f"| {s['siteId']} | `{s['rva']}` | {s['status']} | {'; '.join(s['disqualificationReasons']) or 'none'} |")
    lines += ["", "## Gate result", "",
              "**NO_SAFE_OBSERVER_SITE.** Parent call boundaries contain split instructions or relative control flow that the existing raw-copy trampoline does not relocate. Helper-entry candidates lack a reviewed observer ABI, caller/lifetime proof, and validated nonblocking drain. No staging observer was built.", "",
              "## Historical rejected paths", "",
              "The resolver, selector, and function-entry detours remain explicitly non-eligible per their prior crash evidence.", "",
              "## Next boundary", "", result["nextEvidence"][0], ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", type=Path, default=Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"))
    ap.add_argument("--parent", type=Path, default=REPO_ROOT / PARENT_MAP)
    ap.add_argument("--output", type=Path, default=REPO_ROOT / "bridge" / "placement_helper_observer_site_qualification_static_map.json")
    ap.add_argument("--doc", type=Path, default=REPO_ROOT / "docs" / "research" / "PlacementHelperObserverSiteQualification-StaticMap-v1.md")
    args = ap.parse_args()
    image = StaticImage(args.exe)
    result = analyze(image, load_json(args.parent))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text(render_doc(result), encoding="utf-8")
    json.loads(args.output.read_text(encoding="utf-8"))
    print(json.dumps({"output": str(args.output), "status": result["selectedDesign"]["status"], "sha256": image.digest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
