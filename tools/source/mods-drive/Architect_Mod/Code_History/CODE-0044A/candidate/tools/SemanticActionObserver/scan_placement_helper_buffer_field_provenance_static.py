#!/usr/bin/env python3
"""Offline CODE-0003 analysis of the placement helper output buffer.

Only fixed output-buffer writes with explicit aliases are promoted. Indexed or
opaque writes remain unresolved.
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
REVISION = 1076226
PARENT_MAP = "bridge/placement_frame_input_provenance_static_map.json"
TARGET_RESOLVER_CALL, RESOLVER = 0x28089E, 0xCB4B50
PLACEMENT_LOAD, PLACEMENT_CALL, PLACEMENT_TARGET = 0x280F75, 0x280F86, 0x3E2CD0
PARENT_START, PARENT_END = 0x280790, 0x2810E8
BUFFER_BASE_DISP, FIELD38, FIELD78 = -0x30, 0x38, 0x78
VOLATILE = {"rax", "rcx", "rdx", "r8", "r9", "r10", "r11"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parent_gate(parent: dict[str, Any]) -> None:
    if parent.get("analysisMode") != "OFFLINE_STATIC_ONLY" or parent.get("build", {}).get("sha256") != SUPPORTED_SHA256:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: CODE-0002 mode/fingerprint changed")
    if not parent.get("build", {}).get("fingerprintMatches") or parent.get("convergenceDelta", {}).get("status") != "PARTIAL_STATIC":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: CODE-0002 status changed")
    frame = parent.get("frameModel", {})
    if (frame.get("functionStartRva"), frame.get("functionEndRva")) != (hx(PARENT_START), hx(PARENT_END)):
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: logical range changed")
    if frame.get("rbpOffsetFromEntryRsp") != -0x76D8 or frame.get("normalizedCurrentRspExpression") != "RBP - 0x100":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: frame arithmetic changed")
    if not frame.get("rspStableFromPrologueToResolver"):
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: RSP stability changed")
    for key, expected in (("normalizedRbpPlus08", FIELD38), ("normalizedRbpPlus48", FIELD78)):
        location = frame.get(key, {})
        if location.get("classification") != "FUNCTION_LOCAL_STACK_SLOT" or location.get("bufferFieldOffset") != hx(expected):
            raise RuntimeError(f"MISSING_OR_DIVERGENT_PARENT_DELIVERY: {key} alias changed")
    if parent.get("observerDecision", {}).get("install") is not False:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: observer gate changed")
    uses = {row.get("instructionRva"): row.get("instruction", "") for row in parent.get("resolverCallsite", {}).get("returnUse", [])}
    if uses.get(hx(TARGET_RESOLVER_CALL)) != "call 0xcb4b50":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: resolver call changed")
    if "[rbx]" not in uses.get(hx(PLACEMENT_LOAD), "") or "0x3e2cd0" not in uses.get(hx(PLACEMENT_CALL), ""):
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: placement chain changed")
    calls = {int(row["callsiteRva"], 16) for row in parent.get("localBufferConstruction", {}).get("bufferCallSites", [])}
    if not {0x2807B6, 0x2807C8}.issubset(calls):
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: established helper callsites changed")
    if parent.get("localBufferConstruction", {}).get("fixedOffsetWriteToTargetSlotsFound") is not False:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: exact field write was promoted")


def function_chain(image: StaticImage, start_rva: int) -> list[dict[str, str]]:
    first = image.function_for(start_rva)
    if not first:
        raise RuntimeError(f"function {hx(start_rva)} is not covered by .pdata")
    result = [first]
    start = int(first["startRva"], 16)
    from tools.SemanticActionObserver.scan_placement_frame_input_provenance_static import parse_unwind_info
    while True:
        end = int(result[-1]["endRva"], 16)
        nxt = next((row for row in image.functions if row[0] == end), None)
        if not nxt:
            break
        unwind = parse_unwind_info(image, nxt[2])
        chain = unwind.get("chainedRuntimeFunction")
        if not chain or int(chain["startRva"], 16) != start:
            break
        result.append({"startRva": hx(nxt[0]), "endRva": hx(nxt[1]), "unwindInfoRva": hx(nxt[2])})
    return result


def decode_chain(image: StaticImage, start_rva: int) -> tuple[dict[str, Any], list[Any]]:
    pieces = function_chain(image, start_rva)
    end = int(pieces[-1]["endRva"], 16)
    return {"startRva": pieces[0]["startRva"], "endRva": pieces[-1]["endRva"],
            "firstPdata": pieces[0], "pdataPieces": pieces}, image.disassemble(start_rva, end)


def reg_name(ins: Any, operand: Any) -> str | None:
    return canonical_reg(ins.reg_name(operand.reg)) if operand.type == capstone.x86.X86_OP_REG else None


def memory_effect(ins: Any, operand: Any) -> str:
    if operand.type != capstone.x86.X86_OP_MEM:
        return "none"
    try:
        if operand.access & capstone.CS_AC_WRITE:
            return "write"
        if operand.access & capstone.CS_AC_READ:
            return "read"
    except Exception:
        pass
    return "write" if ins.operands and ins.operands[0] is operand else "read"


def alias_text(value: int | str | None) -> str:
    if isinstance(value, int):
        return f"output+0x{value:X}"
    return str(value) if value is not None else "unknown"


def resolve_memory_operand(ins: Any, operand: Any, aliases: dict[str, int | str],
                           stack_aliases: dict[int, int | str]) -> tuple[int | None, str, bool]:
    if operand.type != capstone.x86.X86_OP_MEM:
        return None, "", False
    mem = operand.mem
    base = canonical_reg(ins.reg_name(mem.base)) if mem.base else None
    index = canonical_reg(ins.reg_name(mem.index)) if mem.index else None
    if base in aliases:
        value = aliases[base]
        if index:
            index_value = aliases.get(index)
            index_text = alias_text(index_value) if index_value is not None else index.upper()
            return None, f"{alias_text(value)} + {index_text}*{mem.scale} + {mem.disp:+#x}", True
        if isinstance(value, int):
            return value + mem.disp, f"output+0x{value + mem.disp:X}", False
        return None, f"{value} + {mem.disp:+#x}", True
    if base == "rsp" and not index and mem.disp in stack_aliases:
        return None, f"stack[{mem.disp:+#x}] ({alias_text(stack_aliases[mem.disp])})", True
    return None, f"[{base.upper() if base else 'absolute'}{mem.disp:+#x}]", bool(index)


def classify_target_range(offset: int | None, width: int, target: int) -> tuple[bool | None, bool | None]:
    if offset is None:
        return False, None
    return offset == target, offset < target + 8 and offset + width > target


def write_record(helper_rva: int, bounds: dict[str, Any], ins: Any, offset: int | None,
                 destination: str, dynamic: bool) -> dict[str, Any]:
    width = int(ins.operands[0].size or 0) if ins.operands else 0
    exact38, overlap38 = classify_target_range(offset, width, FIELD38)
    exact78, overlap78 = classify_target_range(offset, width, FIELD78)
    row = {
        "helperRva": hx(helper_rva), "functionRange": bounds,
        "instructionRva": hx(ins.address), "instruction": f"{ins.mnemonic} {ins.op_str}".strip(),
        "bytes": ins.bytes.hex(" ").upper(), "destinationBaseExpression": "outputBuffer",
        "destinationOffset": hx(offset),
        "destinationRange": f"[{hx(offset)}, {hx(offset + width)})" if offset is not None else "unknown/dynamic",
        "destinationExpression": destination, "writeWidth": width,
        "sourceExpression": ins.op_str.split(",", 1)[1].strip() if "," in ins.op_str else "instruction effect",
        "controlFlowPath": "reachable helper instruction; branch predicates intentionally unnamed",
        "exactTargetHit38": exact38, "overlapsTarget38": overlap38,
        "exactTargetHit78": exact78, "overlapsTarget78": overlap78,
        "evidenceStatus": "PROVEN_STATIC" if offset is not None else "UNSOLVED_DYNAMIC_DESTINATION",
    }
    if dynamic:
        row["dynamicDestination"] = True
    return row


def analyze_helper_instructions(instructions: list[Any], helper_rva: int,
                                bounds: dict[str, Any] | None = None) -> dict[str, Any]:
    bounds = bounds or {"startRva": hx(instructions[0].address), "endRva": hx(instructions[-1].address + instructions[-1].size)}
    aliases: dict[str, int | str] = {}
    stack_aliases: dict[int, int | str] = {}
    writes, nested = [], []
    output_setup = None
    for ins in instructions:
        mnem = ins.mnemonic.lower()
        if mnem == "mov" and len(ins.operands) >= 2 and reg_name(ins, ins.operands[0]) == "rdi":
            src = reg_name(ins, ins.operands[1])
            if src == "rdx":
                aliases["rdi"] = 0
                output_setup = instruction_row(ins)
            elif src in aliases:
                aliases["rdi"] = aliases[src]
            else:
                aliases.pop("rdi", None)
        for operand in ins.operands:
            if memory_effect(ins, operand) != "write":
                continue
            offset, destination, dynamic = resolve_memory_operand(ins, operand, aliases, stack_aliases)
            if offset is not None or (dynamic and "output" in destination.lower()):
                writes.append(write_record(helper_rva, bounds, ins, offset, destination, dynamic))
            if operand.type == capstone.x86.X86_OP_MEM:
                mem = operand.mem
                base = canonical_reg(ins.reg_name(mem.base)) if mem.base else None
                if base == "rsp" and not mem.index and len(ins.operands) > 1:
                    src = reg_name(ins, ins.operands[1])
                    if src in aliases:
                        stack_aliases[mem.disp] = aliases[src]
        if ins.group(capstone.CS_GRP_CALL):
            arg_aliases = {arg.upper(): alias_text(aliases[arg]) for arg in ("rcx", "rdx", "r8", "r9") if arg in aliases}
            if arg_aliases:
                nested.append({
                    "callsiteRva": hx(ins.address), "targetRva": hx(call_target(ins)),
                    "callInstruction": instruction_row(ins), "outputPointerArguments": arg_aliases,
                    "directCallEvidence": True,
                    "argumentMappingStatus": "PROVEN_OUTPUT_ALIAS" if any(v.startswith("output+") for v in arg_aliases.values()) else "INFERRED_OR_DYNAMIC",
                    "fieldWriterFollowed": False,
                    "stopReason": "No fixed alias to +0x38/+0x78 was proven; nested writer not promoted.",
                })
            for volatile in VOLATILE:
                aliases.pop(volatile, None)
            continue
        if mnem == "lea" and len(ins.operands) >= 2 and ins.operands[0].type == capstone.x86.X86_OP_REG:
            dest = reg_name(ins, ins.operands[0])
            off, expr, _ = resolve_memory_operand(ins, ins.operands[1], aliases, stack_aliases)
            if dest:
                aliases[dest] = off if off is not None else expr
        elif mnem == "mov" and len(ins.operands) >= 2 and ins.operands[0].type == capstone.x86.X86_OP_REG:
            dest, src = reg_name(ins, ins.operands[0]), reg_name(ins, ins.operands[1])
            if dest:
                aliases[dest] = aliases[src] if src in aliases else aliases.pop(dest, None)
        elif mnem == "add" and len(ins.operands) >= 2 and reg_name(ins, ins.operands[0]):
            dest, src = reg_name(ins, ins.operands[0]), reg_name(ins, ins.operands[1])
            if dest and src in aliases:
                if isinstance(aliases.get(dest), int) and isinstance(aliases[src], int):
                    aliases[dest] += aliases[src]
                else:
                    aliases[dest] = f"{alias_text(aliases.get(dest))} + {alias_text(aliases[src])}"
        elif mnem == "sub" and len(ins.operands) >= 2 and reg_name(ins, ins.operands[0]):
            dest, src = reg_name(ins, ins.operands[0]), reg_name(ins, ins.operands[1])
            if dest and src in aliases:
                if isinstance(aliases.get(dest), int) and isinstance(aliases[src], int):
                    aliases[dest] -= aliases[src]
                else:
                    aliases[dest] = f"{alias_text(aliases.get(dest))} - {alias_text(aliases[src])}"
    fixed = [row for row in writes if row["evidenceStatus"] == "PROVEN_STATIC" and (row["overlapsTarget38"] or row["overlapsTarget78"])]
    dynamic = [row for row in writes if row["evidenceStatus"] != "PROVEN_STATIC"]
    return {
        "functionRange": bounds,
        "outputBufferArgument": {"register": "RDX", "mappedRegister": "RDI", "mappingInstruction": output_setup,
                                 "sourceExpression": "incoming RDX", "status": "PROVEN_STATIC" if output_setup else "UNSOLVED"},
        "writes": writes, "fixedFieldWrites": fixed, "dynamicOutputWrites": dynamic,
        "nestedDirectCallees": nested,
        "analysisNotes": ["Constant output offsets only are promoted.", "Indexed/register-computed destinations remain unresolved."],
    }


def analyze_helper(image: StaticImage, helper_rva: int) -> dict[str, Any]:
    bounds, instructions = decode_chain(image, helper_rva)
    return analyze_helper_instructions(instructions, helper_rva, bounds)


def path_to(cfg: dict[str, Any], start: int, target: int) -> tuple[bool, list[int]]:
    queue, seen = [(start, [start])], set()
    while queue:
        node, path = queue.pop(0)
        if node == target:
            return True, path
        if node in seen:
            continue
        seen.add(node)
        for child in cfg["blocks"][node]["successors"]:
            if child not in seen:
                queue.append((child, path + [child]))
    return False, []


def helper_callsites(image: StaticImage, instructions: list[Any], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    targets = {0x8DA7C0, 0x8D5CA0}
    resolver_index = next(i for i, ins in enumerate(instructions) if ins.address == TARGET_RESOLVER_CALL)
    resolver_block = cfg["instructionToBlock"][resolver_index]
    rows = []
    for idx, ins in enumerate(instructions):
        target = call_target(ins)
        if target not in targets:
            continue
        block_id = cfg["instructionToBlock"][idx]
        block = next(row for row in cfg["blocks"] if row["id"] == block_id)
        next_block = cfg["instructionToBlock"].get(idx + 1, block_id)
        can_reach, path = path_to(cfg, next_block, resolver_block)
        setup = [instruction_row(row) for row in instructions[max(0, idx - 8):idx]]
        local = next((row for row in reversed(setup) if "lea rdx, [rbp - 0x30]" in row["instruction"]), None)
        rcx = next((row["instruction"] for row in reversed(setup) if row["instruction"].startswith("mov rcx")), "not recovered")
        r8 = next((row["instruction"] for row in reversed(setup) if row["instruction"].startswith(("mov r8", "lea r8"))), "not recovered")
        rows.append({
            "callsiteRva": hx(ins.address), "targetRva": hx(target), "callInstruction": instruction_row(ins),
            "containingBasicBlock": {"id": block_id, "startRva": hx(block["start"]), "endRva": hx(block["end"])},
            "predecessorBlocks": cfg["predecessors"].get(block_id, []),
            "pathCondition": "entry/straight-line path" if idx < resolver_index and not cfg["predecessors"].get(block_id) else "conditional or loop path; predicates unnamed",
            "localBufferArgument": {"register": "RDX", "expression": "RBP-0x30", "aliasProven": local is not None, "evidence": local},
            "otherArgumentExpressions": {"RCX": rcx, "RDX": local["instruction"] if local else "not recovered", "R8": r8},
            "canReachResolverCall": can_reach, "pathToResolverBlocks": path,
            "evidenceStatus": "PROVEN_STATIC_CALLSITE_AND_BUFFER_ALIAS" if local else "UNSOLVED_BUFFER_ALIAS",
        })
    return rows


def field_result(field: int, consumer: list[dict[str, Any]], helpers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    fixed = []
    dynamic = []
    label = "38" if field == FIELD38 else "78"
    for helper in helpers.values():
        fixed.extend(row for row in helper["fixedFieldWrites"] if row[f"overlapsTarget{label}"])
        dynamic.extend(row for row in helper["dynamicOutputWrites"] if row[f"overlapsTarget{label}"] is None)
    return {
        "targetOffset": hx(field), "consumedReadChain": consumer, "reachingWrites": fixed,
        "overwrittenCandidates": [], "pathSpecificCandidates": [], "unresolvedDynamicWriteCandidates": dynamic,
        "lastProvenWriter": fixed[-1] if len(fixed) == 1 else None,
        "sourceProvenance": [], "dependsOnIncomingR15": False,
        "firstUnresolvedBoundary": "No fixed destination write to this field was found; indexed/register-computed helper writes remain unresolved.",
        "ambiguityReason": "No field-level fixed writer; dynamic output writes cannot be assigned to this offset.",
        "status": "PROVEN_STATIC_BUILD_1076226" if len(fixed) == 1 and not dynamic else "UNSOLVED",
    }


def select_last_unique_writer(writes: list[dict[str, Any]], ambiguous: bool = False) -> dict[str, Any] | None:
    """Select only a single proven writer; branch ambiguity never gets collapsed."""
    if ambiguous or len(writes) != 1:
        return None
    return writes[0]


def source_provenance(ins: Any) -> dict[str, Any]:
    """Decode one simple source operand without crossing an opaque call."""
    if len(ins.operands) < 2 or ins.operands[1].type != capstone.x86.X86_OP_MEM:
        if len(ins.operands) >= 2 and ins.operands[1].type == capstone.x86.X86_OP_REG:
            return {"sourceExpression": ins.op_str.split(",", 1)[1].strip(), "terminalSource": "incoming register or alias", "status": "INFERRED"}
        return {"sourceExpression": ins.op_str, "terminalSource": None, "status": "UNSOLVED"}
    mem = ins.operands[1].mem
    base = canonical_reg(ins.reg_name(mem.base)) if mem.base else None
    return {"sourceExpression": ins.op_str.split(",", 1)[1].strip(),
            "baseRegister": base.upper() if base else None, "fieldOffset": hx(mem.disp),
            "terminalSource": f"{base.upper()}+{hx(mem.disp)}" if base else None, "status": "PROVEN_STATIC"}


def build_report(exe: Path, repo: Path, parent: dict[str, Any]) -> dict[str, Any]:
    image = StaticImage(exe)
    instructions = image.disassemble(PARENT_START, PARENT_END)
    cfg = build_basic_blocks(instructions)
    callsites = helper_callsites(image, instructions, cfg)
    helpers = {hx(0x8DA7C0): analyze_helper(image, 0x8DA7C0), hx(0x8D5CA0): analyze_helper(image, 0x8D5CA0)}
    by_addr = {ins.address: ins for ins in instructions}
    field38 = field_result(FIELD38, [instruction_row(by_addr[rva]) for rva in (0x280897, 0x28089B)], helpers)
    field78 = field_result(FIELD78, [instruction_row(by_addr[0x28088B])], helpers)
    correlations = {
        name: {"status": "NOT_ESTABLISHED", "sourceEvidence": "Helper output aliases and target-field writers are not proven.",
               "targetEvidence": "Existing CODE-0001/CODE-0002 maps contain no connected owner edge.",
               "connectingInstructions": [], "pointerIdentity": "NOT_ESTABLISHED",
               "contradictions": ["No field-level writer/source chain connects this buffer to the named subsystem."]}
        for name in ("createBuildingItem", "clientPlayerInput", "selectionFrontier", "snapPreview", "blueprintCache")
    }
    mapping_evidence = [row["callInstruction"] for row in callsites]
    alias_evidence = [helper["outputBufferArgument"]["mappingInstruction"] for helper in helpers.values()
                      if helper["outputBufferArgument"]["mappingInstruction"]]
    return {
        "schemaVersion": 1, "tool": "scan_placement_helper_buffer_field_provenance_static.py",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "parentEvidence": {"delivery": "CODE-0002", "map": PARENT_MAP, "status": parent["convergenceDelta"]["status"],
                           "mapFingerprintMatches": parent["build"]["fingerprintMatches"]},
        "build": {"revision": REVISION, "sha256": image.digest, "supportedSha256": SUPPORTED_SHA256,
                  "fingerprintMatches": image.digest == SUPPORTED_SHA256, "imageBase": hx(image.base),
                  "imageSize": hx(image.pe.OPTIONAL_HEADER.SizeOfImage), "executablePath": str(exe.resolve())},
        "safety": {"processAccess": False, "debugApis": False, "writesExecutable": False, "writesGameMemory": False,
                   "runtimeHooksInstalled": False},
        "parentAnchors": {"logicalFunctionStartRva": hx(PARENT_START), "logicalFunctionEndRva": hx(PARENT_END),
                          "resolverCallRva": hx(TARGET_RESOLVER_CALL), "resolverTargetRva": hx(RESOLVER),
                          "itemLoadRva": hx(PLACEMENT_LOAD), "placementCallRva": hx(PLACEMENT_CALL),
                          "placementTargetRva": hx(PLACEMENT_TARGET), "localBufferField38": hx(FIELD38),
                          "localBufferField78": hx(FIELD78)},
        "helperCallsites": callsites, "helpers": helpers, "field38": field38, "field78": field78,
        "crossSystemCorrelation": correlations,
        "convergenceDelta": {
            "field38WriterProven": bool(field38["lastProvenWriter"]), "field78WriterProven": bool(field78["lastProvenWriter"]),
            "field38SourceProven": False, "field78SourceProven": False, "incomingR15DependencyProven": False,
            "selectionConnectionProven": False, "previewConnectionProven": False, "blueprintRecordConnectionProven": False,
            "commonOwnerProven": False, "status": "PARTIAL_STATIC",
            "evidence": [{"claim": "helper targets decoded from executable E8 rel32", "instructionEvidence": mapping_evidence},
                         {"claim": "helper output buffer maps incoming RDX to RDI", "instructionEvidence": alias_evidence}],
            "contradictions": ["No constant write overlaps +0x38 or +0x78.", "Dynamic indexed writes cannot be assigned to either field.",
                               "Receiving a buffer does not prove its source field or semantic owner."],
        },
        "observerDecision": {"install": False, "failClosed": True,
                             "reason": "CODE-0003 is static helper-buffer field provenance only; no runtime hook or mutation is allowed."},
        "nextEvidence": [
            "Resolve indexed destination arithmetic in 0x8D5CA0 and variable-size nested writes from 0x8DA7C0.",
            "If a writer is recovered, backward-slice only direct aliases/direct callees and keep semantic ownership separate.",
            "Keep opaque/indirect boundaries explicit; no runtime instrumentation is justified by this map.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Placement Helper Buffer Field Provenance — Static Map v1", "",
        f"Scope: Enshrouded revision {report['build']['revision']}; executable SHA-256 {report['build']['sha256']}.",
        "Offline/static only. No process access, hooks, executable patching, game-memory writes, or deployed-DLL changes.", "",
        "## Parent CODE-0002 frontier", "",
        "CODE-0002 remains PARTIAL_STATIC; its frame model maps RBP+0x08 to localBuffer+0x38 and RBP+0x48 to localBuffer+0x78.", "",
        "## Helper callsite-to-target map", "",
    ]
    for row in report["helperCallsites"]:
        lines.append(f"- {row['callsiteRva']} -> {row['targetRva']}; buffer alias {row['localBufferArgument']['aliasProven']}; reaches resolver {row['canReachResolverCall']}; {row['pathCondition']}.")
    for key, helper in report["helpers"].items():
        lines.extend(["", f"## Helper {key}", "",
                      f"Range {helper['functionRange']['startRva']}..{helper['functionRange']['endRva']}. Output mapping {helper['outputBufferArgument']['status']}.",
                      f"Fixed writes {len(helper['fixedFieldWrites'])}; dynamic output candidates {len(helper['dynamicOutputWrites'])}; nested callees {len(helper['nestedDirectCallees'])}.", ""])
        for write in helper["writes"]:
            lines.append(f"- {write['instructionRva']} {write['instruction']} -> {write['destinationRange']}; width {write['writeWidth']}; +0x38 {write['overlapsTarget38']}; +0x78 {write['overlapsTarget78']}; {write['evidenceStatus']}.")
    for title, key in (("localBuffer+0x38", "field38"), ("localBuffer+0x78", "field78")):
        field = report[key]
        lines.extend(["", f"## {title}", "",
                      f"Status {field['status']}. Fixed reaching writers {len(field['reachingWrites'])}; dynamic unresolved candidates {len(field['unresolvedDynamicWriteCandidates'])}.",
                      f"Last proven writer {field['lastProvenWriter']['instructionRva'] if field['lastProvenWriter'] else 'none'}.",
                      f"First unresolved boundary: {field['firstUnresolvedBoundary']}"])
    lines.extend(["", "## Cross-system correlation", ""])
    for name, row in report["crossSystemCorrelation"].items():
        lines.append(f"- {name}: {row['status']}; pointer identity {row['pointerIdentity']}.")
    conv = report["convergenceDelta"]
    lines.extend(["", "## Convergence delta versus CODE-0002", "",
                  f"Field +0x38 writer {conv['field38WriterProven']}; field +0x78 writer {conv['field78WriterProven']}; incoming R15 {conv['incomingR15DependencyProven']}; common owner {conv['commonOwnerProven']}; overall {conv['status']}.",
                  "", "## Findings", "",
                  "PROVEN_STATIC: executable callsite targets, helper ranges, RDX-to-RDI output aliases, and fixed/dynamic write classification.",
                  "INFERRED: helpers can populate the caller-provided buffer.",
                  "UNSOLVED: exact target-field writers, source values, semantic owner, and cross-system identity.", "",
                  "## Exact next static boundary", "",
                  *[f"- {row}" for row in report["nextEvidence"]], "",
                  "No runtime hook, mutation, executable patch, or native DLL change was added.", ""])
    return "\n".join(lines)


def main() -> int:
    game_root = Path(__file__).resolve().parents[4]
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=game_root / "enshrouded.exe")
    parser.add_argument("--repo", type=Path, default=repo)
    parser.add_argument("--output", type=Path, default=repo / "bridge" / "placement_helper_buffer_field_provenance_static_map.json")
    parser.add_argument("--doc", type=Path, default=repo / "docs" / "research" / "PlacementHelperBufferFieldProvenance-StaticMap-v1.md")
    args = parser.parse_args()
    parent = load_json(args.repo / PARENT_MAP)
    parent_gate(parent)
    report = build_report(args.exe.resolve(), args.repo.resolve(), parent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"executableSha256": report["build"]["sha256"],
                      "helperCallsites": [(row["callsiteRva"], row["targetRva"]) for row in report["helperCallsites"]],
                      "field38Status": report["field38"]["status"], "field78Status": report["field78"]["status"],
                      "convergence": report["convergenceDelta"]["status"],
                      "observerInstall": report["observerDecision"]["install"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
