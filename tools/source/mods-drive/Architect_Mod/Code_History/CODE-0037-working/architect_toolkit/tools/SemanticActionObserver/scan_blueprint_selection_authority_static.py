#!/usr/bin/env python3
"""Build-locked, offline map of the build-selection/placement authority gap.

The scanner reads an on-disk PE, local reflection JSON, and reviewed static-map
JSON only. It never opens a process, uses debug APIs, writes executable/game
memory, or installs a hook. Unknown register/data-flow boundaries stay
explicit rather than being guessed through calls or aliases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import capstone
import pefile

SUPPORTED_SHA256 = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
REVISION = 1076226
VOLATILE_CALL_REGS = {"rax", "rcx", "rdx", "r8", "r9", "r10", "r11"}
ALIASES = {
    "al": "rax", "ah": "rax", "ax": "rax", "eax": "rax", "rax": "rax",
    "bl": "rbx", "bh": "rbx", "bx": "rbx", "ebx": "rbx", "rbx": "rbx",
    "cl": "rcx", "ch": "rcx", "cx": "rcx", "ecx": "rcx", "rcx": "rcx",
    "dl": "rdx", "dh": "rdx", "dx": "rdx", "edx": "rdx", "rdx": "rdx",
    "sil": "rsi", "si": "rsi", "esi": "rsi", "rsi": "rsi",
    "dil": "rdi", "di": "rdi", "edi": "rdi", "rdi": "rdi",
    "bpl": "rbp", "bp": "rbp", "ebp": "rbp", "rbp": "rbp",
    "spl": "rsp", "sp": "rsp", "esp": "rsp", "rsp": "rsp",
}
for _n in range(8, 16):
    ALIASES.update({f"r{_n}b": f"r{_n}", f"r{_n}w": f"r{_n}", f"r{_n}d": f"r{_n}", f"r{_n}": f"r{_n}"})


def hx(value: int | None) -> str | None:
    return None if value is None else f"0x{value:X}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def canonical_reg(name: str) -> str:
    return ALIASES.get(name.lower(), name.lower())


def operand_text(ins: Any, operand: Any) -> str:
    if operand.type == capstone.x86.X86_OP_REG:
        return ins.reg_name(operand.reg).upper()
    if operand.type == capstone.x86.X86_OP_IMM:
        return hx(operand.imm) or "0"
    if operand.type == capstone.x86.X86_OP_MEM:
        mem = operand.mem
        pieces = []
        if mem.base:
            pieces.append(ins.reg_name(mem.base).upper())
        if mem.index:
            pieces.append(f"{ins.reg_name(mem.index).upper()}*{mem.scale}")
        disp = mem.disp
        expr = "+".join(pieces) if pieces else "absolute"
        if disp > 0:
            expr += f"+0x{disp:X}"
        elif disp < 0:
            expr += f"-0x{-disp:X}"
        return f"[{expr}]"
    return "?"


def instruction_row(ins: Any) -> dict[str, str]:
    return {"instructionRva": hx(ins.address),
            "instruction": f"{ins.mnemonic} {ins.op_str}".strip(),
            "bytes": ins.bytes.hex(" ").upper()}


def build_basic_blocks(instructions: list[Any]) -> dict[str, Any]:
    """Build a small direct-branch CFG from one .pdata function range."""
    if not instructions:
        return {"blocks": [], "reachable": [], "predecessors": {}}
    addr_to_index = {ins.address: i for i, ins in enumerate(instructions)}
    leaders = {instructions[0].address}
    branch_targets: dict[int, int] = {}
    for index, ins in enumerate(instructions):
        is_jump = ins.group(capstone.CS_GRP_JUMP)
        is_ret = ins.group(capstone.CS_GRP_RET)
        if is_jump:
            if ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
                target = int(ins.operands[0].imm)
                if target in addr_to_index:
                    leaders.add(target)
                    branch_targets[index] = target
            if index + 1 < len(instructions):
                leaders.add(instructions[index + 1].address)
        elif is_ret and index + 1 < len(instructions):
            leaders.add(instructions[index + 1].address)
    leader_indices = sorted(addr_to_index[a] for a in leaders)
    blocks: list[dict[str, Any]] = []
    ins_to_block: dict[int, int] = {}
    for block_id, begin_idx in enumerate(leader_indices):
        end_idx = leader_indices[block_id + 1] if block_id + 1 < len(leader_indices) else len(instructions)
        body = list(range(begin_idx, end_idx))
        for idx in body:
            ins_to_block[idx] = block_id
        blocks.append({"id": block_id, "start": instructions[begin_idx].address,
                       "end": instructions[end_idx - 1].address + instructions[end_idx - 1].size,
                       "instructionIndices": body, "successors": []})
    predecessors: dict[int, set[int]] = {b["id"]: set() for b in blocks}
    for block in blocks:
        last_idx = block["instructionIndices"][-1]
        last = instructions[last_idx]
        succ: set[int] = set()
        if last.group(capstone.CS_GRP_JUMP):
            target = branch_targets.get(last_idx)
            if target is not None:
                succ.add(ins_to_block[addr_to_index[target]])
            if last.mnemonic.lower() not in {"jmp", "ljmp"} and last_idx + 1 < len(instructions):
                succ.add(ins_to_block[last_idx + 1])
        elif not last.group(capstone.CS_GRP_RET) and last_idx + 1 < len(instructions):
            succ.add(ins_to_block[last_idx + 1])
        block["successors"] = sorted(succ)
        for child in succ:
            predecessors[child].add(block["id"])
    reachable: set[int] = set()
    queue = deque([0])
    while queue:
        item = queue.popleft()
        if item in reachable:
            continue
        reachable.add(item)
        queue.extend(blocks[item]["successors"])
    return {"blocks": blocks, "reachable": sorted(reachable),
            "predecessors": {k: sorted(v) for k, v in predecessors.items()},
            "instructionToBlock": ins_to_block}


def written_registers(ins: Any) -> set[str]:
    try:
        _, written = ins.regs_access()
        result = {canonical_reg(ins.reg_name(reg)) for reg in written}
    except Exception:
        result = set()
        if ins.operands and ins.operands[0].type == capstone.x86.X86_OP_REG:
            result.add(canonical_reg(ins.reg_name(ins.operands[0].reg)))
    if ins.group(capstone.CS_GRP_CALL):
        result |= VOLATILE_CALL_REGS
    return result


def reaching_definitions(instructions: list[Any], cfg: dict[str, Any], register: str) -> dict[int, set[int]]:
    """Compute conservative per-register reaching definitions at block edges."""
    register = canonical_reg(register)
    blocks = cfg["blocks"]
    preds = cfg["predecessors"]
    reachable = set(cfg["reachable"])
    gen: dict[int, int | None] = {}
    for block in blocks:
        candidates = [idx for idx in block["instructionIndices"] if register in written_registers(instructions[idx])]
        gen[block["id"]] = candidates[-1] if candidates else None
    ins_in: dict[int, set[int]] = {b["id"]: set() for b in blocks}
    ins_out: dict[int, set[int]] = {b["id"]: set() for b in blocks}
    changed = True
    while changed:
        changed = False
        for block in blocks:
            bid = block["id"]
            if bid not in reachable:
                continue
            new_in = set().union(*(ins_out[pred] for pred in preds[bid] if pred in reachable)) if preds[bid] else set()
            new_out = {gen[bid]} if gen[bid] is not None else new_in
            if new_in != ins_in[bid] or new_out != ins_out[bid]:
                ins_in[bid], ins_out[bid] = new_in, new_out
                changed = True
    result: dict[int, set[int]] = {}
    for block in blocks:
        bid = block["id"]
        current = set(ins_in[bid])
        for idx in block["instructionIndices"]:
            result[idx] = set(current)
            if register in written_registers(instructions[idx]):
                current = {idx}
    result[-1] = set()  # function-entry unknown is represented by no in-function definition
    return result


class StaticImage:
    def __init__(self, path: Path):
        if not path.is_file():
            raise FileNotFoundError(f"required executable is missing: {path}")
        self.path = path.resolve()
        self.digest = sha256(self.path)
        if self.digest != SUPPORTED_SHA256:
            raise RuntimeError(f"BUILD_MISMATCH expected={SUPPORTED_SHA256} actual={self.digest}")
        self.pe = pefile.PE(str(self.path))
        self.base = int(self.pe.OPTIONAL_HEADER.ImageBase)
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        self.md.detail = True
        pdata = next((s for s in self.pe.sections if s.Name.rstrip(b"\0") == b".pdata"), None)
        if pdata is None:
            raise RuntimeError("required .pdata unwind section missing")
        pdata_bytes = pdata.get_data()
        self.functions: list[tuple[int, int, int]] = []
        for offset in range(0, len(pdata_bytes) - 11, 12):
            begin, end, unwind = struct.unpack_from("<III", pdata_bytes, offset)
            if 0x1000 <= begin < end <= self.pe.OPTIONAL_HEADER.SizeOfImage:
                self.functions.append((begin, end, unwind))

    def function_for(self, rva: int) -> dict[str, str] | None:
        matches = [row for row in self.functions if row[0] <= rva < row[1]]
        if not matches:
            return None
        begin, end, unwind = min(matches, key=lambda row: row[1] - row[0])
        return {"startRva": hx(begin) or "", "endRva": hx(end) or "", "unwindInfoRva": hx(unwind) or ""}

    def disassemble(self, begin: int, end: int) -> list[Any]:
        if end <= begin:
            return []
        return list(self.md.disasm(self.pe.get_data(begin, end - begin), begin))

    def function_instructions(self, rva: int) -> tuple[dict[str, str] | None, list[Any]]:
        bounds = self.function_for(rva)
        if not bounds:
            return None, []
        return bounds, self.disassemble(int(bounds["startRva"], 16), int(bounds["endRva"], 16))


def find_instruction(instructions: list[Any], rva: int) -> int | None:
    return next((idx for idx, ins in enumerate(instructions) if ins.address == rva), None)


def slice_register(image: StaticImage, instructions: list[Any], cfg: dict[str, Any], start_index: int,
                   register: str, max_depth: int = 8) -> tuple[list[dict[str, Any]], str, list[int]]:
    """Walk one unique reaching definition chain through explicit dependencies."""
    rows: list[dict[str, Any]] = []
    defs_by_reg = {reg: reaching_definitions(instructions, cfg, reg) for reg in
                   ("rax", "rbx", "rcx", "rdx", "r8", "rsi", "r15", "rbp", "rsp", "rdi")}
    current_index = start_index
    current_reg = canonical_reg(register)
    visited: set[tuple[int, str]] = set()
    unresolved = "definition not found within containing .pdata function"
    all_definition_indices: list[int] = []
    for _ in range(max_depth):
        reaching = defs_by_reg.setdefault(current_reg, reaching_definitions(instructions, cfg, current_reg)).get(current_index, set())
        if len(reaching) != 1:
            unresolved = "no in-function definition" if not reaching else "ambiguous reaching definitions at control-flow merge"
            rows.append({"instructionRva": None, "instruction": None,
                         "sourceExpression": current_reg.upper(), "destinationExpression": current_reg.upper(),
                         "evidenceStatus": "UNSOLVED", "detail": unresolved,
                         "candidateDefinitions": [hx(instructions[i].address) for i in sorted(reaching)]})
            break
        def_idx = next(iter(reaching))
        all_definition_indices.append(def_idx)
        key = (def_idx, current_reg)
        if key in visited:
            unresolved = "cyclic register dependency"
            break
        visited.add(key)
        ins = instructions[def_idx]
        dest = None
        if ins.operands and ins.operands[0].type == capstone.x86.X86_OP_REG:
            dest = canonical_reg(ins.reg_name(ins.operands[0].reg))
        source = "unknown instruction effect"
        status = "PROVEN_INSTRUCTION_EFFECT"
        next_reg: str | None = None
        detail = ""
        if ins.group(capstone.CS_GRP_CALL):
            target = None
            if ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
                target = int(ins.operands[0].imm)
            source = f"return value of direct call {hx(target)}" if target is not None and current_reg == "rax" else "volatile register clobbered/returned by call"
            status = "PROVEN_DIRECT_CALL_RETURN" if target is not None and current_reg == "rax" else "UNSOLVED_CALL_CLOBBER"
            unresolved = "call boundary: callee return/volatile state is not traced by this slice"
        elif ins.mnemonic.lower() == "mov" and len(ins.operands) >= 2:
            src = ins.operands[1]
            source = operand_text(ins, src)
            if src.type == capstone.x86.X86_OP_REG:
                next_reg = canonical_reg(ins.reg_name(src.reg))
                detail = "explicit register copy"
                if next_reg == "rax" and def_idx > 0 and instructions[def_idx - 1].group(capstone.CS_GRP_CALL):
                    call = instructions[def_idx - 1]
                    target = int(call.operands[0].imm) if call.operands and call.operands[0].type == capstone.x86.X86_OP_IMM else None
                    source = f"return RAX from call {hx(target)} immediately before this copy"
                    status = "PROVEN_DIRECT_CALL_RETURN"
                    call_row = instruction_row(call)
                    rows.append({"instructionRva": call_row["instructionRva"], "instruction": call_row["instruction"],
                                 "bytes": call_row["bytes"], "sourceExpression": f"callee {hx(target)} return RAX",
                                 "destinationExpression": "RAX return state", "evidenceStatus": "PROVEN_DIRECT_CALL_RETURN"})
                    unresolved = "lookup result/call boundary; do not infer owner semantics from the returned pointer"
                else:
                    unresolved = "register source requires another reaching-definition step"
            elif src.type == capstone.x86.X86_OP_MEM:
                mem = src.mem
                if mem.index:
                    unresolved = "indexed memory source; index/alias semantics not followed"
                    status = "UNSOLVED_ALIAS_OR_INDEX"
                elif mem.base:
                    next_reg = canonical_reg(ins.reg_name(mem.base))
                    detail = "direct memory load; base register is traced separately"
                    unresolved = "memory value itself is the nearest proven source; base ownership is unresolved unless traced"
            elif src.type == capstone.x86.X86_OP_IMM:
                unresolved = "immediate source is terminal"
        elif ins.mnemonic.lower() == "lea" and len(ins.operands) >= 2 and ins.operands[1].type == capstone.x86.X86_OP_MEM:
            mem = ins.operands[1].mem
            source = operand_text(ins, ins.operands[1])
            if mem.index:
                unresolved = "indexed address formation; index source not followed"
                status = "UNSOLVED_ALIAS_OR_INDEX"
            elif mem.base:
                next_reg = canonical_reg(ins.reg_name(mem.base))
                unresolved = "address base is traced separately; pointed-to object provenance may remain unknown"
        elif ins.mnemonic.lower() in {"xor", "sub", "and", "or", "add", "inc", "dec"}:
            unresolved = "arithmetic/flag-dependent definition is an explicit slice stop"
            status = "UNSOLVED_ARITHMETIC"
        ins_row = instruction_row(ins)
        rows.append({"instructionRva": ins_row["instructionRva"], "instruction": ins_row["instruction"],
                     "bytes": ins_row["bytes"], "sourceExpression": source,
                     "destinationExpression": (dest or current_reg).upper(), "evidenceStatus": status,
                     "detail": detail or unresolved})
        if next_reg is None:
            break
        current_index = def_idx
        current_reg = next_reg
    return rows, unresolved, all_definition_indices


def call_target(ins: Any) -> int | None:
    if ins.group(capstone.CS_GRP_CALL) and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
        return int(ins.operands[0].imm)
    return None


def memory_writes_to(ins: Any, base: str, displacement: int) -> bool:
    if not ins.operands:
        return False
    destination = ins.operands[0]
    if destination.type != capstone.x86.X86_OP_MEM:
        return False
    return canonical_reg(ins.reg_name(destination.mem.base)) == canonical_reg(base) and destination.mem.disp == displacement


def caller_snap_trace(image: StaticImage, snap: dict[str, Any]) -> dict[str, Any]:
    consumer_info = {
        "0x3E377D": {"local": "[RBP+0x190]", "range": (0x3E3A20, 0x3E3A45), "collectionCall": "0x3EB810", "otherCalls": []},
        "0x3E4347": {"local": "[RBP+0x1B0]", "range": (0x3E4537, 0x3E45D5), "collectionCall": "0x99F970", "otherCalls": ["0x3E5480"]},
        "0x3E6C9C": {"local": "[RBP+0xD0]", "range": (0x3E6CB8, 0x3E6D56), "collectionCall": "0x99F970", "otherCalls": ["0x3EAB80"]},
        "0x3EB297": {"local": "[RBP+0x3D0]", "range": (0x3EB588, 0x3EB5AD), "collectionCall": "0x3EB810", "otherCalls": []},
    }
    rows = {}
    for call_rva, spec in consumer_info.items():
        local = spec["local"]
        downstream = spec["collectionCall"]
        call = int(call_rva, 16)
        bounds, instructions = image.function_instructions(call)
        call_idx = find_instruction(instructions, call)
        return_rva = call + (instructions[call_idx].size if call_idx is not None else 5)
        return_idx = find_instruction(instructions, return_rva)
        post: list[dict[str, str]] = []
        if return_idx is not None:
            for ins in instructions[return_idx:min(len(instructions), return_idx + 48)]:
                post.append(instruction_row(ins))
                if ins.group(capstone.CS_GRP_CALL):
                    break
        use_start, use_end = spec["range"]
        collection_use = [instruction_row(ins) for ins in instructions if use_start <= ins.address < use_end]
        imported = (snap.get("callers") or {}).get(call_rva, {})
        downstream_dataflow = next((r for r in snap.get("consumerAnalysis", []) if r.get("caller") == call_rva), {})
        consumer_rva = int(downstream, 16)
        _, consumer_ins = image.function_instructions(consumer_rva)
        consumer_evidence = [instruction_row(i) for i in consumer_ins[:40]]
        rows[call_rva] = {
            "callerFunction": imported.get("function"),
            "callerPdata": bounds,
            "filterCall": call_rva,
            "returnRva": hx(return_rva),
            "acceptedCollectionLocal": local,
            "immediatePostReturnInstructions": post,
            "collectionPostReturnDataflow": collection_use,
            "collectionFirstConsumerCall": downstream,
            "otherPostReturnHelperCallsBeforeCollectionUse": spec["otherCalls"],
            "legacyMapClassification": downstream_dataflow.get("classification", "UNRESOLVED"),
            "existingStaticClassification": downstream_dataflow.get("classification", "UNRESOLVED"),
            "consumerFunctionRange": image.function_for(consumer_rva),
            "consumerEntryEvidence": consumer_evidence,
            "candidateSelection": "UNSOLVED",
            "firstForwardFrontier": f"{downstream}: accepted-collection local data reaches this call; callee selection/writeback semantics remain unresolved",
        }
    helper_calls = {}
    for rva in (0x3EB810, 0x3E5480, 0x3EAB80, 0x99F970):
        bounds, instructions = image.function_instructions(rva)
        selected = []
        for ins in instructions:
            if ins.address - rva > 0x200:
                break
            if call_target(ins) is not None or any(op.type == capstone.x86.X86_OP_MEM and ins.mnemonic.lower() in {"mov", "movups", "movsd"} and op is ins.operands[0] for op in ins.operands):
                selected.append(instruction_row(ins))
        helper_calls[hx(rva)] = {"pdata": bounds, "boundedInstructionEvidence": selected[:60]}
    return {
        "candidateFilterRva": "0x3E79C0",
        "acceptedRecordStride": "0x50",
        "callers": rows,
        "sharedHelperStaticEvidence": helper_calls,
        "winnerSelectionStatus": "UNSOLVED",
        "previewWritebackStatus": "PARTIAL_STATIC",
        "boundedConclusion": "Callers 0x3E377D and 0x3EB297 pass accepted-collection locals to 0x3EB810, whose loop walks 0x50-byte elements and calls 0x3E5480 per qualifying candidate. Callers 0x3E4347 and 0x3E6C9C copy collection-local header values into later argument frames and call 0x99F970; their nearby 0x3E5480/0x3EAB80 calls occur on separate paths/arguments and are not assumed to consume that collection. 0x3E5480 itself calls 0x3ED1A0 and writes candidate-derived values through the returned pointer. None proves a single persistent selected preview/blueprint owner.",
    }


def selection_candidates(create_map: dict[str, Any], dispatcher: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for row in create_map.get("completeFieldConsumerCandidates", []):
        writes = [field for field in row.get("fieldAccesses", []) if field.get("write")]
        candidates.append({
            "functionRva": row.get("functionStartRva"),
            "functionRange": {"startRva": row.get("functionStartRva"), "endRva": row.get("functionEndRva"), "unwindInfoRva": row.get("unwindInfoRva")},
            "whyConnected": "No action-specific connection: inherited generic +0/+4/+8 shape candidate only.",
            "actionPointerProvenance": row.get("actionPointerProvenance", "UNKNOWN"),
            "fieldCoverage": sorted({item.get("offset") for item in row.get("fieldAccesses", []) if item.get("offset")}),
            "consumedVersionRelation": row.get("consumedVersionFlow", "UNKNOWN"),
            "outboundCalls": row.get("directCallTargets", []),
            "candidatePersistentWrites": writes,
            "persistentWriteStatus": "UNSOLVED_NOT_PERSISTENCE_PROOF",
            "contradictions": ["No dispatch edge identifies the base as CreateBuildingItemAction.", "No complete action field flow or matching consumed-version update is proven.", "No connected transition to placement R8D or a preview/cache owner is proven."],
            "confidence": "UNSOLVED_GENERIC_SHAPE",
            "status": "UNSOLVED_GENERIC_SHAPE",
        })
    if not candidates and create_map.get("staticConclusion", {}).get("consumerFound") is False:
        candidates.append({"functionRva": None, "functionRange": None, "whyConnected": "No connected action-specific consumer was found in the imported map.",
                          "actionPointerProvenance": "UNKNOWN", "fieldCoverage": [], "consumedVersionRelation": "UNKNOWN",
                          "outboundCalls": [], "candidatePersistentWrites": [], "contradictions": ["Native consumer not found"],
                          "confidence": "UNSOLVED", "status": "UNSOLVED"})
    # Preserve the sole proven dispatcher comparison as context, not as a
    # create-action candidate.
    ref = dispatcher.get("inventoryWrapperArchitecture", {})
    candidates.append({"functionRva": "0x371810", "functionRange": {"startRva": "0x371810", "endRva": "0x37229F"},
                       "whyConnected": "Proven InventoryTransferAction dispatcher-family reference pattern only; unrelated action identity is not established.",
                       "actionPointerProvenance": "PROVEN_FOR_INVENTORY_ONLY", "fieldCoverage": ["InventoryTransferAction fields"],
                       "consumedVersionRelation": "inventory +0x20 only; create action +0x30 not tied to same owner",
                       "outboundCalls": ["0x385D80", "0x386180", "0x3883C0"], "candidatePersistentWrites": [],
                       "contradictions": [ref.get("unresolvedPointerTransition", "Inventory-only wrapper provenance"), "No CreateBuildingItemAction sibling dispatch proof."],
                       "confidence": "REFERENCE_PATTERN_ONLY", "status": "NOT_A_CREATE_ACTION_CANDIDATE"})
    return candidates


def build_backward_trace(image: StaticImage) -> dict[str, Any]:
    caller_bounds, instructions = image.function_instructions(0x280F86)
    if not caller_bounds:
        raise RuntimeError("0x280F86 is not covered by .pdata")
    cfg = build_basic_blocks(instructions)
    call_index = find_instruction(instructions, 0x280F86)
    if call_index is None or call_target(instructions[call_index]) != 0x3E2CD0:
        raise RuntimeError("placement call anchor mismatch at 0x280F86")
    r8_defs = reaching_definitions(instructions, cfg, "r8").get(call_index, set())
    steps: list[dict[str, Any]] = []
    if len(r8_defs) != 1:
        return {"functionRange": caller_bounds, "startCallRva": "0x280F86", "targetFunctionRva": "0x3E2CD0", "argument": "R8D",
                "steps": [], "nearestProvenSource": None, "firstUnresolvedBoundary": "R8D has multiple or no reaching definitions across direct CFG predecessors", "status": "UNSOLVED"}
    r8_def_idx = next(iter(r8_defs))
    r8_def = instructions[r8_def_idx]
    steps.append({**instruction_row(r8_def), "sourceExpression": operand_text(r8_def, r8_def.operands[1]) if len(r8_def.operands) > 1 else "?",
                  "destinationExpression": "R8D (zero-extended into R8)", "evidenceStatus": "PROVEN_STATIC_BUILD_1076226"})
    if not (r8_def.mnemonic.lower() == "mov" and len(r8_def.operands) > 1 and r8_def.operands[1].type == capstone.x86.X86_OP_MEM):
        return {"functionRange": caller_bounds, "startCallRva": "0x280F86", "targetFunctionRva": "0x3E2CD0", "argument": "R8D",
                "steps": steps, "nearestProvenSource": steps[0]["sourceExpression"], "firstUnresolvedBoundary": "nearest R8D definition is not a direct memory load supported by this narrow slice", "status": "PARTIAL_STATIC"}
    rbx_defs = reaching_definitions(instructions, cfg, "rbx").get(r8_def_idx, set())
    rbx_def_rows = [instruction_row(instructions[i]) for i in sorted(rbx_defs)]
    source_base_step: dict[str, Any] | None = None
    resolver_call_rva: int | None = None
    unresolved = "RBX provenance has multiple/no reaching definitions before [RBX] load"
    if len(rbx_defs) == 1:
        rbx_def_idx = next(iter(rbx_defs))
        rbx_def = instructions[rbx_def_idx]
        source_base_step = {**instruction_row(rbx_def), "sourceExpression": operand_text(rbx_def, rbx_def.operands[1]) if len(rbx_def.operands) > 1 else "?",
                            "destinationExpression": "RBX (record pointer candidate)", "evidenceStatus": "PROVEN_STATIC_BUILD_1076226"}
        if rbx_def.mnemonic.lower() == "mov" and len(rbx_def.operands) > 1 and rbx_def.operands[1].type == capstone.x86.X86_OP_REG and canonical_reg(rbx_def.reg_name(rbx_def.operands[1].reg)) == "rax":
            preceding = instructions[rbx_def_idx - 1] if rbx_def_idx > 0 else None
            resolver_call_rva = preceding.address if preceding and preceding.group(capstone.CS_GRP_CALL) else None
            if resolver_call_rva is not None and call_target(preceding) == 0xCB4B50:
                unresolved = "resolver return boundary: returned record depends on the resolver's container argument and runtime contents; the RDX frame-slot owner/value semantics and returned mapping are unresolved"
            else:
                unresolved = "RBX receives RAX, but the immediately preceding instruction is not the expected resolver call"
        else:
            unresolved = "RBX definition does not copy a direct call result"
    steps.append({"instructionRva": None, "instruction": "data dependency", "sourceExpression": "RBX+0x00",
                  "destinationExpression": "R8D", "evidenceStatus": "PROVEN_STATIC_BUILD_1076226",
                  "detail": "The value loaded from record-candidate offset +0 becomes the third argument to 0x3E2CD0."})
    if source_base_step:
        steps.append(source_base_step)
    resolver_arguments: dict[str, Any] = {}
    key_steps: list[dict[str, Any]] = []
    if resolver_call_rva is not None:
        resolver_index = find_instruction(instructions, resolver_call_rva)
        if resolver_index is not None:
            for reg in ("rcx", "rdx"):
                reg_defs = reaching_definitions(instructions, cfg, reg).get(resolver_index, set())
                if len(reg_defs) == 1:
                    def_idx = next(iter(reg_defs)); definition = instructions[def_idx]
                    source = operand_text(definition, definition.operands[1]) if len(definition.operands) > 1 else "unknown"
                    destination = operand_text(definition, definition.operands[0]) if definition.operands else reg.upper()
                    row = {**instruction_row(definition), "sourceExpression": source, "destinationExpression": destination, "evidenceStatus": "PROVEN_STATIC_BUILD_1076226"}
                    if reg == "rcx" and definition.mnemonic.lower() == "mov" and len(definition.operands) > 1 and definition.operands[1].type == capstone.x86.X86_OP_MEM:
                        key_steps.append(row)
                        base_reg = canonical_reg(definition.reg_name(definition.operands[1].mem.base)) if definition.operands[1].mem.base else None
                        if base_reg:
                            ptr_defs = reaching_definitions(instructions, cfg, base_reg).get(def_idx, set())
                            if len(ptr_defs) == 1:
                                ptr_def = instructions[next(iter(ptr_defs))]
                                key_steps.append({**instruction_row(ptr_def), "sourceExpression": operand_text(ptr_def, ptr_def.operands[1]) if len(ptr_def.operands) > 1 else "?",
                                                  "destinationExpression": base_reg.upper(), "evidenceStatus": "PROVEN_STATIC_BUILD_1076226"})
                    resolver_arguments[reg.upper()] = {"definitionRva": hx(definition.address), "expression": source,
                                                      "status": "PROVEN_VALUE_EXPRESSION_OWNER_UNRESOLVED" if reg == "rdx" else "PROVEN"}
                elif reg == "rdx":
                    resolver_arguments[reg.upper()] = {"definitionRva": None, "expression": None,
                                                      "status": "UNSOLVED_MULTIPLE_OR_CALL_CLOBBER"}
    steps.extend(key_steps)
    call_text = None
    if resolver_call_rva is not None:
        cidx = find_instruction(instructions, resolver_call_rva)
        if cidx is not None:
            call_text = instruction_row(instructions[cidx])
            steps.append({**call_text, "sourceExpression": "return value from resolver using ECX/RDX inputs",
                          "destinationExpression": "RAX (resolver return)",
                          "evidenceStatus": "PROVEN_CALL_SITE; RETURNED_RECORD_CONTENTS_UNRESOLVED"})
    branch_slice = [instruction_row(ins) for ins in instructions if 0x280F45 <= ins.address <= 0x280F86 and (ins.group(capstone.CS_GRP_JUMP) or ins.group(capstone.CS_GRP_CALL))]
    return {
        "functionRange": caller_bounds,
        "controlFlow": {"basicBlockCount": len(cfg["blocks"]), "reachableBlockCount": len(cfg["reachable"]),
                        "targetBlockStartRva": hx(cfg["blocks"][cfg["instructionToBlock"][call_index]]["start"]),
                        "nearCallBranches": branch_slice,
                        "uniqueR8ReachingDefinition": len(r8_defs) == 1,
                        "uniqueRbxReachingDefinition": len(rbx_defs) == 1,
                        "rbxCandidateDefinitions": rbx_def_rows},
        "startCallRva": "0x280F86", "targetFunctionRva": "0x3E2CD0", "argument": "R8D",
        "steps": steps,
        "resolverCall": {"call": call_text, "targetRva": "0xCB4B50" if resolver_call_rva is not None else None,
                         "arguments": resolver_arguments},
        "keySourceTrace": "uint32(*(uint64_t*)(RBP+0x08) + 0x30)" if key_steps else None,
        "nearestProvenSource": {"expression": "dword ptr [RBX+0x00]", "instructionRva": "0x280F75",
                                 "recordBaseDefinitionRva": hx(instructions[next(iter(rbx_defs))].address) if len(rbx_defs) == 1 else None,
                                 "recordBaseDefinition": "RBX = RAX from resolver call 0xCB4B50 at 0x28089E" if resolver_call_rva is not None else None,
                                 "semantics": "record first dword passed as R8D; item-ID meaning follows from the downstream resolver chain only where independently established"},
        "firstUnresolvedBoundary": unresolved,
        "additionalBoundary": "resolver ECX key is dword ptr [qword ptr [RBP+0x08] + 0x30], and resolver RDX is qword ptr [RBP+0x48]; the RBP-relative object owner/type and resolver container contents remain unidentified.",
        "status": "PARTIAL_STATIC" if resolver_call_rva is not None else "UNSOLVED",
    }


def create_markdown(report: dict[str, Any]) -> str:
    backward = report["placementBackwardSlice"]
    selection = report["selectionForwardTrace"]
    snap = report["snapPreviewWriteback"]
    convergence = report["convergence"]
    lines = [
        "# Blueprint Selection Authority — Static Map v1", "",
        f"**Scope / build:** Enshrouded revision {report['build']['revision']}, executable SHA-256 `{report['build']['sha256']}`.",
        "Static/offline only. No process access, runtime observer, native mutation, or deployed-DLL change.", "",
        "## Existing evidence carried forward", "",
        "CreateBuildingItemAction is PROVEN_STATIC (0x0C; selectedIndex +0x04, itemId +0x08), but its action-specific native consumer and UI event connection remain UNSOLVED. The downstream placement path starts at `0x280F86 -> 0x3E2CD0`; its local resolver result feeds R8D, then a separate resolver/cache/event chain. The late BuildingPlaceEvent argument is not geometry authority. `0xCA90E0` remains a placement/cache lookup, not selection authority.", "",
        "## Backward trace from placement R8D", "",
        f"Containing .pdata range: `{backward['functionRange']['startRva']}..{backward['functionRange']['endRva']}`. At `0x280F75`, `{backward['steps'][0].get('instruction','')}` loads the call argument from a record candidate at +0. RBX is defined at `0x2808A3` from RAX returned by `0xCB4B50` at `0x28089E`. The resolver ECX key comes from `[qword ptr [RBP+0x08] + 0x30]`; this does not identify the object semantically.", "",
        "Instruction-level slice:", "",
    ]
    for step in backward.get("steps", []):
        if step.get("instructionRva"):
            lines.append(f"- `{step['instructionRva']}` `{step['instruction']}` — source `{step.get('sourceExpression')}`, destination `{step.get('destinationExpression')}` ({step.get('evidenceStatus')}).")
    lines.extend(["", f"**First unresolved boundary:** {backward['firstUnresolvedBoundary']}", "", f"Additional unresolved input: {backward.get('additionalBoundary','')}", "",
                  "## Forward trace from CreateBuildingItemAction", "",
                  f"The imported map reports consumer status `{selection['consumerStatus']}` and {selection['genericShapeCandidateCount']} generic shape candidates. None has action-pointer provenance, complete field flow, a CreateBuilding consumed-version relation, or a proven placement connection. The InventoryTransferAction dispatcher remains a reference pattern only.", "",
                  f"**First unresolved boundary:** {selection['firstUnresolvedBoundary']}", "",
                  "## Snap/preview winner-writeback investigation", ""])
    for call_rva, row in snap["callers"].items():
        lines.append(f"### Filter caller `{call_rva}`")
        lines.append(f"Collection local `{row['acceptedCollectionLocal']}`; first collection-data call `{row['collectionFirstConsumerCall']}`; prior map classification `{row['legacyMapClassification']}`.")
        ins = row.get("immediatePostReturnInstructions", [])
        if ins:
            lines.append("Post-return: " + " → ".join(f"`{x['instructionRva']} {x['instruction']}`" for x in ins) + ".")
        collection_ins = row.get("collectionPostReturnDataflow", [])
        if collection_ins:
            lines.append("Accepted collection use: " + " → ".join(f"`{x['instructionRva']} {x['instruction']}`" for x in collection_ins) + ".")
        lines.append(f"Frontier: {row['firstForwardFrontier']}.")
        lines.append("")
    lines.extend(["The `0x3EB810` helper iterates accepted entries by stride `0x50` and forwards qualifying candidates to `0x3E5480`. `0x3E5480` invokes `0x3ED1A0`, then writes candidate-derived values through the returned pointer. The output owner/lifetime and relation to persistent preview or a single selected winner are not proven.", "",
                  "## Convergence result", "",
                  f"Status: **{convergence['status']}**. Common selection/placement owner proven: `{convergence['commonOwnerProven']}`. CreateBuilding item write to placement source proven: `{convergence['selectedItemWriteToPlacementSourceProven']}`. Blueprint-record connection proven: `{convergence['blueprintRecordConnectionProven']}`.", "",
                  "## PROVEN_STATIC / INFERRED / UNSOLVED", "",
                  "- **PROVEN_STATIC:** reflected action layout; `0x280F86` call; R8D load from `[RBX]`; RBX receives the result of the resolver call at `0x28089E`; snap accepted-record stride/caller set; per-candidate helper data flow noted above.",
                  "- **INFERRED:** R8D is a candidate item/record identity because its source is a resolver-returned record's first dword and downstream build analysis uses this argument as a placement resolver key. This does not prove selection-action origin.",
                  "- **UNSOLVED:** action consumer/owner; common selection-placement base; persistent selected blueprint/preview owner; winner selection from accepted snap candidates; target preview lifetime.", "",
                  "## Rejected interpretations", "",
                  "Numeric ItemId equality, generic +0/+4/+8 shape, proximity to snap/preview code, a call to `0xCA90E0`, or temporal ordering do not establish action identity or authority. `0xCB4B50`, `0xCA90E0`, `0x3E2CD0`, and the rejected selector detour are not observer candidates. The v0.31 late helper argument mutation remains disproven for geometry.", "",
                  "## Safe next experiment", "",
                  "Continue static analysis from the exact RBP-relative key source and the unknown resolver-container owner; separately inspect caller-specific consumers beginning at the frontiers above. Any runtime observer requires a separately reviewed change after a low-frequency writer, pointer provenance, and lifetime are established.", "",
                  "**No runtime hook, game-memory mutation, or native DLL change was added.**", ""])
    return "\n".join(lines)


def build_report(exe: Path, types_path: Path, repo: Path) -> dict[str, Any]:
    image = StaticImage(exe)
    required = {
        "create": repo / "bridge/create_building_item_static_map.json",
        "client": repo / "bridge/client_player_input_static_map.json",
        "dispatcher": repo / "bridge/semantic_action_dispatcher_static_map.json",
        "snap": repo / "bridge/snap_candidate_selection_static_map.json",
        "commit": repo / "bridge/building_commit_transform_static_map.json",
        "placement": repo / "bridge/placement_blueprint_authority_static_map.json",
    }
    for name, path in required.items():
        if not path.is_file():
            raise FileNotFoundError(f"required reviewed static map missing ({name}): {path}")
    if not types_path.is_file():
        raise FileNotFoundError(f"required reflection cache missing: {types_path}")
    imported = {name: json.loads(path.read_text(encoding="utf-8-sig")) for name, path in required.items()}
    reflection = json.loads(types_path.read_text(encoding="utf-8-sig"))
    type_rows = reflection.get("types") if isinstance(reflection, dict) else None
    if not isinstance(type_rows, list):
        raise RuntimeError("reflection input invalid: types list missing")
    by_name = {t.get("qualifiedName"): t for t in type_rows if isinstance(t, dict)}
    action = by_name.get("keen::ecs::CreateBuildingItemAction")
    if not action or action.get("size") != 12:
        raise RuntimeError("CreateBuildingItemAction reflected control is missing or has unexpected size")
    backward = build_backward_trace(image)
    create_map = imported["create"]
    dispatcher = imported["dispatcher"]
    client = imported["client"]
    snap = imported["snap"]
    commit = imported["commit"]
    placement = imported["placement"]
    candidates = selection_candidates(create_map, dispatcher)
    snap_trace = caller_snap_trace(image, snap)
    exec_rip_xrefs = (create_map.get("metadata") or {}).get("directExecutableRipXrefs", {})
    action_metadata_refs = {
        "createBuildingItemActionStringRvas": (create_map.get("metadata") or {}).get("stringRvas", {}).get("createBuildingItemAction", []),
        "createBuildingItemTypeStringRvas": (create_map.get("metadata") or {}).get("stringRvas", {}).get("CreateBuildingItemAction", []),
        "uiCreateBuildingItemEventStringRvas": (create_map.get("metadata") or {}).get("stringRvas", {}).get("UiCreateBuildingItemEvent", []),
        "consumedActionStringRvas": (create_map.get("metadata") or {}).get("stringRvas", {}).get("consumedCreateBuildingItemAction", []),
        "directExecutableRipXrefs": exec_rip_xrefs,
        "clientActionOffset": ((client.get("clientPlayerInputRelevantOffsets") or {}).get("createBuildingItemAction") or {}).get("offset"),
        "serverConsumedOffset": (client.get("serverConsumedInput") or {}).get("consumedCreateBuildingItemActionOffset"),
        "uiEventTypePresent": "keen::ecs::UiCreateBuildingItemEvent" in by_name,
        "inventoryDispatcherReferenceOnly": dispatcher.get("siblingActionCandidates", {}).get("CreateBuildingItemAction", {}).get("status") == "UNSOLVED",
    }
    backward_proven_record = backward.get("resolverCall", {}).get("targetRva") == "0xCB4B50"
    # Read the established permanent negative result without accepting a new
    # schema label as proof if the source map uses an older layout.
    negative_result = placement.get("v031LiveNegativeResult") or {}
    late_event_status = negative_result.get("trackingItemIdAloneControlsGeometry")
    if not late_event_status:
        placement_text = json.dumps(placement).lower()
        late_event_status = "DISPROVEN_BUILD_1076226" if "disproven" in placement_text and ("geometryauthority" in placement_text or "geometry authority" in placement_text or "helper argument" in placement_text) else "UNVERIFIED_IMPORT"
    convergence_status = "PARTIAL_STATIC" if backward_proven_record else "UNSOLVED"
    evidence = [
        "0x280F75 loads R8D from [RBX+0] and 0x280F86 calls 0x3E2CD0 (instruction evidence in placementBackwardSlice).",
        "RBX is set from RAX after 0xCB4B50 at 0x28089E; resolver ECX key is a dword load from [*([RBP+0x08])+0x30].",
        "CreateBuildingItemAction map reports no action-qualified consumer and no action-to-placement call/data-flow edge.",
        "Snap map proves 0x3E79C0 appends 0x50 records; caller paths reach different helpers, but no common selected-owner write is proven.",
    ]
    return {
        "schemaVersion": 1,
        "tool": "scan_blueprint_selection_authority_static.py",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "build": {"revision": REVISION, "sha256": image.digest, "supportedSha256": SUPPORTED_SHA256,
                  "fingerprintMatches": image.digest == SUPPORTED_SHA256, "imageBase": hx(image.base),
                  "imageSize": hx(image.pe.OPTIONAL_HEADER.SizeOfImage), "executablePath": str(image.path)},
        "safety": {"processAccess": False, "debugApis": False, "writesExecutable": False,
                   "writesGameMemory": False, "runtimeHooksInstalled": False},
        "knownEvidenceImported": {
            "createBuildingItemAction": {"status": "PROVEN_STATIC_BUILD_1076226", "size": "0x0C", "selectedIndexOffset": "0x04", "itemIdOffset": "0x08",
                                         "consumerStatus": create_map.get("staticConclusion", {}).get("status"), "consumerFound": create_map.get("staticConclusion", {}).get("consumerFound")},
            "clientPlayerInput": {"status": client.get("candidateClientPlayerInput", {}).get("status"), "createActionOffset": action_metadata_refs["clientActionOffset"],
                                  "liveIdentity": (client.get("statusModel") or {}).get("ClientPlayerInput_live_identity")},
            "dispatcher": {"createActionStatus": (dispatcher.get("siblingActionCandidates") or {}).get("CreateBuildingItemAction", {}).get("status"),
                           "inventoryReferenceRange": (dispatcher.get("dispatchGraph") or {}).get("consumer")},
            "placementLateEventGeometryAuthority": late_event_status,
            "placementBlueprintCache": "0xCA90E0 placement/cache use is not selection authority",
            "snapCandidateFilter": {"rva": "0x3E79C0", "outputStride": (snap.get("candidateFilter") or {}).get("outputRecordStride"),
                                    "callers": list((snap.get("callers") or {}).keys())},
            "reflectionRelationships": action_metadata_refs,
            "sourceMapPaths": {key: str(path) for key, path in required.items()},
            "placementCommitObserverDecision": commit.get("observerDecision"),
        },
        "placementBackwardSlice": backward,
        "selectionForwardTrace": {
            "reflectedActionStatus": "PROVEN_STATIC_BUILD_1076226",
            "consumerStatus": "UNSOLVED",
            "candidates": candidates,
            "candidateCount": len(candidates),
            "actionSpecificCandidateCount": 0,
            "genericShapeCandidateCount": len([c for c in candidates if c["status"] == "UNSOLVED_GENERIC_SHAPE"]),
            "metadataEvidence": action_metadata_refs,
            "firstUnresolvedBoundary": "CreateBuildingItemAction's transient/native dispatch consumer and action-pointer owner; the current evidence has no complete itemId/selectedIndex/version flow or write to the placement resolver source.",
            "status": "UNSOLVED",
        },
        "snapPreviewWriteback": snap_trace,
        "convergence": {
            "commonOwnerProven": False,
            "selectedItemWriteToPlacementSourceProven": False,
            "blueprintRecordConnectionProven": False,
            "status": convergence_status,
            "evidence": evidence,
            "contradictions": ["Placement R8D's current reaching definition is a dereference from RBX, not a proven CreateBuildingItemAction field.",
                               "The resolver key at 0x28089E is loaded from an unidentified RBP-relative base +0x30.",
                               "Resolver RDX/container provenance is not statically resolved in this caller.",
                               "Snap accepted arrays are caller-local and their per-caller downstream functions differ."],
            "firstCommonProducer": {"status": "UNSOLVED", "rva": None, "reason": "No shared structure/base/field receives CreateBuildingItemAction.itemId and later supplies placement R8D or the runtime blueprint record."},
        },
        "rejectedHookSites": [{"rva": "0xCB4B50", "status": "REJECTED_CRASH_HISTORY", "hookEligible": False},
                              {"rva": "0xCA90E0", "status": "LOOKUP_ONLY_NOT_SELECTION_AUTHORITY", "hookEligible": False},
                              {"rva": "0x3E2CD0", "status": "REJECTED_ENTRY_DETOUR", "hookEligible": False},
                              {"rva": "0x280F86", "status": "REJECTED_SELECTOR_DETOUR", "hookEligible": False},
                              {"rva": "0x280F8B", "status": "REJECTED_SELECTOR_CONTINUATION", "hookEligible": False}],
        "observerDecision": {"install": False, "failClosed": True,
                              "reason": "Static analysis narrows the placement source to a resolver-returned record first dword, but action ownership, resolver container input, and stable preview/selection state are unresolved. No runtime observer is justified in this delivery."},
        "nextEvidence": ["Identify the caller/object provenance of the pointer loaded from [RBP+0x08] in the 0x2807D5..0x2810E8 .pdata function, without assuming it is player or selection state.",
                         "Resolve the object/frame provenance and contents for the RBP-relative loads feeding ECX and RDX at 0x28089E, without naming the base prematurely.",
                         "Find an action-specific CreateBuildingItemAction consumer with a proven pointer and full version/index/itemId flow before seeking a persistent owner.",
                         "At snap callers, inspect the per-caller helper output lifetime and determine whether a 0x50 accepted candidate is chosen or all candidates are processed."],
    }


def main() -> int:
    game_root = Path(__file__).resolve().parents[4]
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=game_root / "enshrouded.exe")
    parser.add_argument("--types", type=Path, default=game_root / ".cache" / "types.json")
    parser.add_argument("--repo", type=Path, default=repo)
    parser.add_argument("--output", type=Path, default=repo / "bridge" / "blueprint_selection_authority_static_map.json")
    parser.add_argument("--doc", type=Path, default=repo / "docs" / "research" / "BlueprintSelectionAuthority-StaticMap-v1.md")
    args = parser.parse_args()
    report = build_report(args.exe.resolve(), args.types.resolve(), args.repo.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text(create_markdown(report), encoding="utf-8")
    print(json.dumps({"executableSha256": report["build"]["sha256"],
                      "backwardFrontier": report["placementBackwardSlice"]["firstUnresolvedBoundary"],
                      "forwardFrontier": report["selectionForwardTrace"]["firstUnresolvedBoundary"],
                      "snapFrontiers": {k: v["firstForwardFrontier"] for k, v in report["snapPreviewWriteback"]["callers"].items()},
                      "convergence": report["convergence"]["status"], "observerDecision": report["observerDecision"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
