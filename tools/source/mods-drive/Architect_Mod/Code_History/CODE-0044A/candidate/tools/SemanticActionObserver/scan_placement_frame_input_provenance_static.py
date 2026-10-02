#!/usr/bin/env python3
"""Offline, build-locked provenance map for the 0x28089E frame inputs.

This scanner consumes the on-disk PE and reviewed static maps only. It never
opens the game process, installs hooks, writes game memory, or patches files
other than its requested JSON/research outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import capstone
import pefile

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.SemanticActionObserver.scan_blueprint_selection_authority_static import (
    ALIASES,
    StaticImage,
    build_basic_blocks,
    call_target,
    canonical_reg,
    hx,
    instruction_row,
    operand_text,
    reaching_definitions,
)

SUPPORTED_SHA256 = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
REVISION = 1076226
TARGET_CALL = 0x28089E
RESOLVER = 0xCB4B50
PLACEMENT_LOAD = 0x280F75
PLACEMENT_CALL = 0x280F86
PLACEMENT_TARGET = 0x3E2CD0
VOLATILE = {"rax", "rcx", "rdx", "r8", "r9", "r10", "r11"}
READ_ONLY_MNEMONICS = {"cmp", "test", "bt", "bts", "btr", "btc", "push", "call", "lea"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"required static/reflection input is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_unwind_info(image: StaticImage, unwind_rva: int) -> dict[str, Any]:
    """Decode the Windows x64 UNWIND_INFO fields used for frame recovery."""
    raw = image.pe.get_data(unwind_rva, 256)
    if len(raw) < 4:
        raise RuntimeError(f"truncated UNWIND_INFO at {hx(unwind_rva)}")
    first, prolog_size, code_count, frame_byte = raw[:4]
    version, flags = first & 0x7, first >> 3
    frame_register = frame_byte & 0x0F
    frame_offset = (frame_byte >> 4) * 16
    codes: list[dict[str, Any]] = []
    cursor = 4
    slot = 0
    allocation_size = 0
    while slot < code_count:
        if cursor + 2 > len(raw):
            raise RuntimeError(f"truncated unwind-code array at {hx(unwind_rva)}")
        code_offset, opbyte = raw[cursor], raw[cursor + 1]
        op, info = opbyte & 0x0F, opbyte >> 4
        record: dict[str, Any] = {"codeOffset": hx(code_offset), "operation": op,
                                  "operationInfo": info, "raw": raw[cursor:cursor + 2].hex(" ").upper()}
        consumed = 1
        if op == 0:  # UWOP_PUSH_NONVOL
            record["name"] = "UWOP_PUSH_NONVOL"
            record["register"] = unwind_register(info)
        elif op == 1:  # UWOP_ALLOC_LARGE
            record["name"] = "UWOP_ALLOC_LARGE"
            if info == 0 and slot + 1 < code_count:
                extra = struct.unpack_from("<H", raw, cursor + 2)[0]
                allocation_size = extra * 8
                record["allocationBytes"] = allocation_size
                record["extraRaw"] = raw[cursor + 2:cursor + 4].hex(" ").upper()
                consumed = 2
            elif info == 1 and slot + 2 < code_count:
                allocation_size = struct.unpack_from("<I", raw, cursor + 2)[0]
                record["allocationBytes"] = allocation_size
                record["extraRaw"] = raw[cursor + 2:cursor + 6].hex(" ").upper()
                consumed = 3
            else:
                record["decodeStatus"] = "UNKNOWN_OR_TRUNCATED"
        elif op == 2:  # UWOP_ALLOC_SMALL
            allocation_size = info * 8 + 8
            record["name"] = "UWOP_ALLOC_SMALL"
            record["allocationBytes"] = allocation_size
        elif op == 3:
            record["name"] = "UWOP_SET_FPREG"
        elif op in (4, 5):
            record["name"] = "UWOP_SAVE_NONVOL" if op == 4 else "UWOP_SAVE_NONVOL_FAR"
            record["register"] = unwind_register(info)
            consumed = 2 if op == 4 else 3
            extra_size = 2 if op == 4 else 4
            if slot + consumed - 1 < code_count and cursor + 2 + extra_size <= len(raw):
                extra = int.from_bytes(raw[cursor + 2:cursor + 2 + extra_size], "little")
                record["savedRegisterOffsetBytes"] = extra * 8 if op == 4 else extra
                record["extraRaw"] = raw[cursor + 2:cursor + 2 + extra_size].hex(" ").upper()
            else:
                record["decodeStatus"] = "UNKNOWN_OR_TRUNCATED"
        elif op in (8, 9):
            record["name"] = "UWOP_SAVE_XMM128" if op == 8 else "UWOP_SAVE_XMM128_FAR"
            consumed = 2 if op == 8 else 3
            extra_size = 2 if op == 8 else 4
            if slot + consumed - 1 < code_count and cursor + 2 + extra_size <= len(raw):
                extra = int.from_bytes(raw[cursor + 2:cursor + 2 + extra_size], "little")
                record["savedXmmOffsetBytes"] = extra * 16 if op == 8 else extra
                record["extraRaw"] = raw[cursor + 2:cursor + 2 + extra_size].hex(" ").upper()
            else:
                record["decodeStatus"] = "UNKNOWN_OR_TRUNCATED"
        elif op == 10:
            record["name"] = "UWOP_PUSH_MACHFRAME"
        else:
            record["name"] = "UNKNOWN_UNWIND_OPCODE"
        codes.append(record)
        cursor += consumed * 2
        slot += consumed
    chain: dict[str, Any] | None = None
    if flags & 0x4:
        trailer = 4 + ((code_count + 1) & ~1) * 2
        if trailer + 12 > len(raw):
            raise RuntimeError(f"truncated chained RUNTIME_FUNCTION at {hx(unwind_rva)}")
        begin, end, unwind = struct.unpack_from("<III", raw, trailer)
        chain = {"startRva": hx(begin), "endRva": hx(end), "unwindInfoRva": hx(unwind)}
    return {"unwindInfoRva": hx(unwind_rva), "version": version, "flags": flags,
            "flagsNames": [name for bit, name in ((1, "EHANDLER"), (2, "UHANDLER"), (4, "CHAININFO")) if flags & bit],
            "prologueSize": prolog_size, "codeCount": code_count,
            "frameRegisterNumber": frame_register, "frameRegister": unwind_register(frame_register) if frame_register else None,
            "frameOffsetBytes": frame_offset, "codes": codes,
            "stackAllocationBytes": allocation_size, "chainedRuntimeFunction": chain,
            "headerAndCodesHex": raw[:4 + ((code_count + 1) & ~1) * 2].hex(" ").upper()}


def unwind_register(index: int) -> str:
    # Windows x64 UNWIND_INFO register numbers.
    names = {0: "RAX", 1: "RCX", 2: "RDX", 3: "RBX", 4: "RSP", 5: "RBP",
             6: "RSI", 7: "RDI", 8: "R8", 9: "R9", 10: "R10", 11: "R11",
             12: "R12", 13: "R13", 14: "R14", 15: "R15"}
    return names.get(index, f"REG_{index}")


def simulate_prologue(instructions: list[Any], unwind_allocation: int | None = None) -> dict[str, Any]:
    """Normalize a small decoded prologue to offsets from entry RSP.

    The unwind allocation is used only for `sub rsp, reg` when unwind metadata
    independently encodes a fixed allocation. Calls do not imply register
    preservation; the unwind fact supplies the allocation size.
    """
    rsp_delta = 0
    regs: dict[str, int] = {"rsp": 0}
    pushes: list[dict[str, Any]] = []
    allocations: list[dict[str, Any]] = []
    rbp_set: dict[str, Any] | None = None
    allocation_used = False
    for ins in instructions:
        mnem = ins.mnemonic.lower()
        if mnem == "push" and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_REG:
            rsp_delta -= 8
            regs["rsp"] = rsp_delta
            pushes.append({**instruction_row(ins), "register": ins.reg_name(ins.operands[0].reg).upper(),
                           "rspOffsetAfterFromEntry": rsp_delta})
            continue
        if mnem == "lea" and len(ins.operands) >= 2 and ins.operands[0].type == capstone.x86.X86_OP_REG and ins.operands[1].type == capstone.x86.X86_OP_MEM:
            dest = canonical_reg(ins.reg_name(ins.operands[0].reg))
            mem = ins.operands[1].mem
            base_name = canonical_reg(ins.reg_name(mem.base)) if mem.base else None
            if base_name in regs and not mem.index:
                regs[dest] = regs[base_name] + mem.disp
                if dest == "rbp":
                    rbp_set = {**instruction_row(ins), "rbpOffsetFromEntryRsp": regs[dest]}
            continue
        if mnem == "mov" and len(ins.operands) >= 2 and ins.operands[0].type == capstone.x86.X86_OP_REG:
            dest = canonical_reg(ins.reg_name(ins.operands[0].reg))
            src = ins.operands[1]
            if src.type == capstone.x86.X86_OP_REG:
                source = canonical_reg(ins.reg_name(src.reg))
                if source in regs:
                    regs[dest] = regs[source]
                else:
                    regs.pop(dest, None)
            elif src.type == capstone.x86.X86_OP_IMM:
                regs.pop(dest, None)
            continue
        if mnem == "sub" and len(ins.operands) >= 2 and ins.operands[0].type == capstone.x86.X86_OP_REG and canonical_reg(ins.reg_name(ins.operands[0].reg)) == "rsp":
            src = ins.operands[1]
            if src.type == capstone.x86.X86_OP_IMM:
                amount = int(src.imm)
                evidence = "decoded immediate"
            elif src.type == capstone.x86.X86_OP_REG and unwind_allocation is not None and not allocation_used:
                amount = unwind_allocation
                allocation_used = True
                evidence = "fixed allocation encoded by UNWIND_INFO"
            else:
                return {"status": "UNSOLVED_DYNAMIC_RSP_ADJUSTMENT", "rspOffsetFromEntry": rsp_delta,
                        "rbpOffsetFromEntry": regs.get("rbp"), "pushes": pushes, "allocations": allocations,
                        "rbpSet": rbp_set, "unresolvedInstruction": instruction_row(ins)}
            rsp_delta -= amount
            regs["rsp"] = rsp_delta
            allocations.append({**instruction_row(ins), "allocationBytes": amount, "evidence": evidence,
                                "rspOffsetAfterFromEntry": rsp_delta})
    return {"status": "PROVEN_STATIC" if rbp_set else "RBP_NOT_ESTABLISHED",
            "rspOffsetFromEntry": rsp_delta, "rbpOffsetFromEntry": regs.get("rbp"),
            "pushes": pushes, "allocations": allocations, "rbpSet": rbp_set}


def classify_frame_location(rbp_disp: int, frame_model: dict[str, Any],
                            callsite_stack_argument_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    rbp_entry = frame_model.get("rbpOffsetFromEntry")
    rsp_entry = frame_model.get("rspOffsetFromEntry")
    if rbp_entry is None or rsp_entry is None:
        return {"classification": "UNRESOLVED_FRAME_RELATIVE_LOCATION", "status": "UNSOLVED"}
    entry_offset = rbp_entry + rbp_disp
    # Locals occupy the allocation below the post-push stack pointer.
    post_push = min((row["rspOffsetAfterFromEntry"] for row in frame_model.get("pushes", [])), default=0)
    if rsp_entry <= entry_offset < post_push:
        return {"classification": "FUNCTION_LOCAL_STACK_SLOT", "entryRspOffset": entry_offset,
                "currentRspOffset": entry_offset - rsp_entry,
                "normalizedExpression": f"entryRSP{entry_offset:+#x} = currentRSP+0x{entry_offset-rsp_entry:X}",
                "status": "PROVEN_STATIC"}
    # Win64 arg5 begins at entry RSP+0x28. Do not label such a slot without
    # specific callsite evidence that the caller supplied that stack argument.
    evidence = callsite_stack_argument_evidence or {}
    if entry_offset >= 0x28 and evidence.get("proven") is True:
        arg_index = 5 + (entry_offset - 0x28) // 8
        return {"classification": "INCOMING_STACK_ARGUMENT", "entryRspOffset": entry_offset,
                "argumentIndex": arg_index, "callsiteEvidence": evidence,
                "normalizedExpression": f"entryRSP+0x{entry_offset:X}", "status": "PROVEN_STATIC"}
    return {"classification": "UNRESOLVED_FRAME_RELATIVE_LOCATION", "entryRspOffset": entry_offset,
            "normalizedExpression": f"entryRSP{entry_offset:+#x}", "status": "UNSOLVED",
            "reason": "not within proven local allocation; incoming-argument classification requires concrete caller stack-argument evidence"}


def classify_incoming_register(register: str, callsite_evidence: dict[str, Any] | None) -> dict[str, Any]:
    if not callsite_evidence or callsite_evidence.get("proven") is not True:
        return {"register": register.upper(), "classification": "ENTRY_REGISTER_SOURCE_UNRESOLVED",
                "status": "UNSOLVED", "reason": "no direct caller instruction evidence maps a value into this entry register"}
    return {"register": register.upper(), "classification": "INCOMING_REGISTER_VALUE",
            "status": "PROVEN_STATIC", "callsiteEvidence": callsite_evidence}


def stack_address_offset(ins: Any, operand: Any, frame_model: dict[str, Any], aliases: dict[str, int]) -> int | None:
    if operand.type != capstone.x86.X86_OP_MEM:
        return None
    mem = operand.mem
    if mem.index:
        return None
    base = canonical_reg(ins.reg_name(mem.base)) if mem.base else None
    if base == "rbp":
        return mem.disp
    if base == "rsp":
        rbp_delta = frame_model.get("rbpOffsetFromEntry")
        rsp_delta = frame_model.get("rspOffsetFromEntry")
        if rbp_delta is None or rsp_delta is None:
            return None
        return mem.disp + rsp_delta - rbp_delta
    if base in aliases:
        return aliases[base] + mem.disp
    return None


def memory_operand_is_write(ins: Any, operand: Any) -> bool:
    if operand.type != capstone.x86.X86_OP_MEM:
        return False
    try:
        return bool(operand.access & capstone.CS_AC_WRITE)
    except Exception:
        return bool(ins.operands and ins.operands[0] is operand and ins.mnemonic.lower() not in READ_ONLY_MNEMONICS)


def frame_slot_events(instructions: list[Any], frame_model: dict[str, Any], target_disp: int,
                      buffer_builder_ranges: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Find direct stores and conservative helper-call may-writes to a frame slot."""
    buffer_builder_ranges = buffer_builder_ranges or []
    aliases: dict[str, int] = {}
    events: list[dict[str, Any]] = []
    for idx, ins in enumerate(instructions):
        if ins.group(capstone.CS_GRP_CALL):
            call_target_rva = call_target(ins)
            for reg in ("rcx", "rdx", "r8", "r9"):
                off = aliases.get(reg)
                if off == target_disp:
                    events.append({**instruction_row(ins), "instructionIndex": idx,
                                   "kind": "UNKNOWN_CALL_MAY_WRITE_EXACT_SLOT",
                                   "sourceExpression": f"address of [RBP{target_disp:+#x}] passed in {reg.upper()}",
                                   "destinationExpression": f"[RBP{target_disp:+#x}]", "mustWrite": False,
                                   "evidenceStatus": "UNSOLVED_OPAQUE_CALL_CLOBBER"})
                for descriptor in buffer_builder_ranges:
                    if call_target_rva != descriptor["targetRva"] or off != descriptor["baseDisp"]:
                        continue
                    if descriptor["baseDisp"] <= target_disp < descriptor["baseDisp"] + descriptor["length"]:
                        events.append({**instruction_row(ins), "instructionIndex": idx,
                                       "kind": "UNKNOWN_CALL_MAY_WRITE_BUFFER_FIELD",
                                       "sourceExpression": f"{reg.upper()} points to RBP{off:+#x}; target is buffer+0x{target_disp-off:X}",
                                       "destinationExpression": f"possible [RBP{target_disp:+#x}] via helper output buffer",
                                       "bufferLength": descriptor["length"], "mustWrite": False,
                                       "evidenceStatus": "OPAQUE_HELPER_RECEIVES_TARGET_CONTAINING_OUTPUT_BUFFER"})
            for reg in VOLATILE:
                aliases.pop(reg, None)
            continue
        if ins.mnemonic.lower() == "lea" and len(ins.operands) >= 2 and ins.operands[0].type == capstone.x86.X86_OP_REG:
            dest = canonical_reg(ins.reg_name(ins.operands[0].reg))
            source = stack_address_offset(ins, ins.operands[1], frame_model, aliases)
            if source is not None:
                aliases[dest] = source
            else:
                aliases.pop(dest, None)
            continue
        for op_idx, operand in enumerate(ins.operands):
            if operand.type != capstone.x86.X86_OP_MEM or not memory_operand_is_write(ins, operand):
                continue
            off = stack_address_offset(ins, operand, frame_model, aliases)
            if off is None:
                continue
            size = max(1, int(operand.size or 1))
            if off < target_disp + 8 and off + size > target_disp:
                events.append({**instruction_row(ins), "instructionIndex": idx,
                               "kind": "DIRECT_FRAME_STORE", "destinationFrameOffset": hx(off),
                               "accessSize": size, "targetOffset": hx(target_disp),
                               "sourceExpression": operand_text(ins, ins.operands[1]) if len(ins.operands) > 1 else "instruction effect",
                               "destinationExpression": operand_text(ins, operand),
                               "mustWrite": off == target_disp and size >= 8,
                               "evidenceStatus": "PROVEN_STATIC" if off == target_disp and size >= 8 else "PROVEN_OVERLAPPING_STORE"})
        if ins.operands and ins.operands[0].type == capstone.x86.X86_OP_REG:
            dest = canonical_reg(ins.reg_name(ins.operands[0].reg))
            if ins.mnemonic.lower() == "mov" and len(ins.operands) > 1 and ins.operands[1].type == capstone.x86.X86_OP_REG:
                source = canonical_reg(ins.reg_name(ins.operands[1].reg))
                if source in aliases:
                    aliases[dest] = aliases[source]
                else:
                    aliases.pop(dest, None)
            else:
                aliases.pop(dest, None)
        if ins.group(capstone.CS_GRP_JUMP):
            # Do not carry address aliases across a branch with another predecessor.
            aliases.clear()
    return events


def reaching_memory_definitions(instructions: list[Any], cfg: dict[str, Any], events: list[dict[str, Any]]) -> dict[int, set[int]]:
    """Memory-slot reaching definitions with conservative CFG union at merges."""
    blocks = cfg["blocks"]
    preds = cfg["predecessors"]
    reachable = set(cfg["reachable"])
    by_index: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        if event["kind"] in {"DIRECT_FRAME_STORE", "UNKNOWN_CALL_MAY_WRITE_EXACT_SLOT", "UNKNOWN_CALL_MAY_WRITE_BUFFER_FIELD"}:
            by_index[event["instructionIndex"]].append(event)
    ins_in = {b["id"]: set() for b in blocks}
    ins_out = {b["id"]: set() for b in blocks}

    def transfer(block: dict[str, Any], incoming: set[int]) -> set[int]:
        current = set(incoming)
        for idx in block["instructionIndices"]:
            idx_events = by_index.get(idx, [])
            if not idx_events:
                continue
            must_write = any(event.get("mustWrite") is True for event in idx_events)
            if must_write:
                current = {idx}
            else:
                # Unknown/overlapping writes are may-defs, not strong updates.
                current.add(idx)
        return current

    changed = True
    while changed:
        changed = False
        for block in blocks:
            bid = block["id"]
            if bid not in reachable:
                continue
            incoming = set().union(*(ins_out[p] for p in preds[bid] if p in reachable)) if preds[bid] else set()
            outgoing = transfer(block, incoming)
            if incoming != ins_in[bid] or outgoing != ins_out[bid]:
                ins_in[bid], ins_out[bid] = incoming, outgoing
                changed = True
    result: dict[int, set[int]] = {}
    for block in blocks:
        bid = block["id"]
        current = set(ins_in[bid])
        for idx in block["instructionIndices"]:
            result[idx] = set(current)
            if idx in by_index:
                must_write = any(event.get("mustWrite") is True for event in by_index[idx])
                if must_write:
                    current = {idx}
                else:
                    current.add(idx)
    return result


def preserve_caller_callsite_separation(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep each direct caller edge distinct, even when source expressions match."""
    return sorted((dict(row) for row in rows), key=lambda row: (row.get("callsiteRva") or "", row.get("callerFunctionStartRva") or ""))


def direct_callers(image: StaticImage, target_rva: int) -> list[dict[str, Any]]:
    """Find verified direct rel32 CALL sites targeting an RVA in executable sections."""
    raw_hits: list[int] = []
    for section in image.pe.sections:
        if not (section.Characteristics & 0x20000000):
            continue
        data = section.get_data()
        base = int(section.VirtualAddress)
        pos = 0
        while True:
            offset = data.find(b"\xE8", pos)
            if offset < 0 or offset + 5 > len(data):
                break
            displacement = struct.unpack_from("<i", data, offset + 1)[0]
            if base + offset + 5 + displacement == target_rva:
                raw_hits.append(base + offset)
            pos = offset + 1
    results: list[dict[str, Any]] = []
    decoded_functions: dict[tuple[int, int], list[Any]] = {}
    for site in sorted(set(raw_hits)):
        bounds = image.function_for(site)
        if not bounds:
            continue
        key = (int(bounds["startRva"], 16), int(bounds["endRva"], 16))
        instructions = decoded_functions.setdefault(key, image.disassemble(*key))
        ins = next((row for row in instructions if row.address == site), None)
        if ins is None or call_target(ins) != target_rva:
            continue
        idx = next((i for i, row in enumerate(instructions) if row.address == site), None)
        preceding = instructions[max(0, (idx or 0) - 8):(idx or 0)]
        results.append({"callsiteRva": hx(site), "callerFunctionStartRva": bounds["startRva"],
                        "callerFunctionEndRva": bounds["endRva"], "callInstruction": instruction_row(ins),
                        "precedingInstructions": [instruction_row(row) for row in preceding],
                        "argumentSourceStatus": "REQUIRES_CALLSITE_SLICE"})
    return results


def stack_slot_reads(instructions: list[Any], target_disp: int, frame_model: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    aliases: dict[str, int] = {}
    for ins in instructions:
        for operand in ins.operands:
            if operand.type != capstone.x86.X86_OP_MEM:
                continue
            off = stack_address_offset(ins, operand, frame_model, aliases)
            if off != target_disp:
                continue
            if memory_operand_is_write(ins, operand):
                continue
            rows.append({**instruction_row(ins), "frameOffset": hx(off), "accessSize": int(operand.size or 0),
                         "sourceExpression": operand_text(ins, operand), "evidenceStatus": "PROVEN_STATIC_READ"})
        if ins.mnemonic.lower() == "lea" and len(ins.operands) >= 2 and ins.operands[0].type == capstone.x86.X86_OP_REG:
            dest = canonical_reg(ins.reg_name(ins.operands[0].reg))
            source = stack_address_offset(ins, ins.operands[1], frame_model, aliases)
            if source is None:
                aliases.pop(dest, None)
            else:
                aliases[dest] = source
        elif ins.group(capstone.CS_GRP_CALL):
            for reg in VOLATILE:
                aliases.pop(reg, None)
        elif ins.operands and ins.operands[0].type == capstone.x86.X86_OP_REG:
            dest = canonical_reg(ins.reg_name(ins.operands[0].reg))
            if ins.mnemonic.lower() == "mov" and len(ins.operands) > 1 and ins.operands[1].type == capstone.x86.X86_OP_REG:
                source = canonical_reg(ins.reg_name(ins.operands[1].reg))
                if source in aliases:
                    aliases[dest] = aliases[source]
                else:
                    aliases.pop(dest, None)
            else:
                aliases.pop(dest, None)
        if ins.group(capstone.CS_GRP_JUMP):
            aliases.clear()
    return rows


def stack_pointer_writes_between(instructions: list[Any], begin_rva: int, end_rva: int) -> list[dict[str, Any]]:
    """List persistent RSP updates in a code interval; ordinary CALL/RET pairs net to zero."""
    rows = []
    for ins in instructions:
        if not (begin_rva <= ins.address < end_rva) or ins.group(capstone.CS_GRP_CALL):
            continue
        explicit_rsp = bool(ins.operands and ins.operands[0].type == capstone.x86.X86_OP_REG
                            and canonical_reg(ins.reg_name(ins.operands[0].reg)) == "rsp")
        stack_op = ins.mnemonic.lower() in {"push", "pop", "enter", "leave"}
        if explicit_rsp or stack_op:
            rows.append(instruction_row(ins))
    return rows


def unwind_chained_logical_function(image: StaticImage, target_rva: int) -> dict[str, Any]:
    target = image.function_for(target_rva)
    if not target:
        raise RuntimeError(f"target {hx(target_rva)} is not covered by .pdata")
    leaf_unwind = parse_unwind_info(image, int(target["unwindInfoRva"], 16))
    chain = leaf_unwind.get("chainedRuntimeFunction")
    if not chain:
        primary = target
    else:
        primary = chain
    if int(primary["endRva"], 16) != int(target["startRva"], 16):
        raise RuntimeError("chained .pdata ranges are not adjacent; refusing to synthesize a logical function range")
    primary_unwind = parse_unwind_info(image, int(primary["unwindInfoRva"], 16))
    return {"leafPdata": target, "leafUnwind": leaf_unwind, "primaryPdata": primary,
            "primaryUnwind": primary_unwind,
            "logicalRange": {"startRva": primary["startRva"], "endRva": target["endRva"],
                             "unwindInfoRva": primary["unwindInfoRva"]}}


def derive_frame_model(image: StaticImage, logical: dict[str, Any]) -> tuple[dict[str, Any], list[Any]]:
    primary = logical["primaryPdata"]
    unwind = logical["primaryUnwind"]
    begin = int(primary["startRva"], 16)
    prologue_end = begin + int(unwind["prologueSize"])
    prologue = image.disassemble(begin, prologue_end)
    sim = simulate_prologue(prologue, unwind.get("stackAllocationBytes") or None)
    frame_register = unwind.get("frameRegister")
    if sim.get("rbpOffsetFromEntry") is None:
        status = "UNSOLVED_RBP_MODEL"
    elif frame_register is None and sim.get("rbpSet"):
        status = "PROVEN_MANUAL_STACK_ANCHOR_NOT_UNWIND_FRAME_REGISTER"
    elif frame_register == "RBP":
        status = "PROVEN_UNWIND_FRAME_REGISTER"
    else:
        status = "PROVEN_RBP_STACK_ANCHOR_OTHER_UNWIND_FRAME_REGISTER"
    sim.update({"rbpModelStatus": status,
                "unwindFrameRegister": frame_register,
                "unwindFrameOffsetBytes": unwind.get("frameOffsetBytes"),
                "entryRspExpression": "RBP + 0x76D8" if sim.get("rbpOffsetFromEntry") == -0x76D8 else None,
                "currentRspExpression": "RBP - 0x100" if sim.get("rspOffsetFromEntry") == -0x77D8 and sim.get("rbpOffsetFromEntry") == -0x76D8 else None,
                "localStackRangeFromEntryRsp": {"lowInclusive": sim.get("rspOffsetFromEntry"),
                                                 "highExclusive": min((row["rspOffsetAfterFromEntry"] for row in sim.get("pushes", [])), default=0)}})
    return sim, prologue


def make_slot_provenance(image: StaticImage, instructions: list[Any], cfg: dict[str, Any],
                         frame_model: dict[str, Any], displacement: int,
                         buffer_base_disp: int, buffer_calls: list[dict[str, Any]]) -> dict[str, Any]:
    classification = classify_frame_location(displacement, frame_model)
    reads = stack_slot_reads(instructions, displacement, frame_model)
    helper_ranges = [{"targetRva": int(row["targetRva"], 16), "baseDisp": buffer_base_disp,
                      "length": 0x100} for row in buffer_calls]
    events = frame_slot_events(instructions, frame_model, displacement, helper_ranges)
    blocks_by_id = {block["id"]: block for block in cfg["blocks"]}
    events = [event for event in events
              if cfg.get("instructionToBlock", {}).get(event["instructionIndex"]) in set(cfg.get("reachable", []))]
    for event in events:
        block_id = cfg.get("instructionToBlock", {}).get(event["instructionIndex"])
        block = blocks_by_id.get(block_id)
        if block is not None:
            event["basicBlock"] = {"id": block_id, "startRva": hx(block["start"]),
                                   "endRva": hx(block["end"])}
            event["predecessorBlocks"] = cfg["predecessors"].get(block_id, [])
            event["predecessorRelationship"] = "basic-block CFG relation recorded; resolver reachability is evaluated separately"
    reaching = reaching_memory_definitions(instructions, cfg, events)
    target_index = next((idx for idx, ins in enumerate(instructions) if ins.address == TARGET_CALL), None)
    reaching_at_resolver = sorted(reaching.get(target_index, set())) if target_index is not None else []
    event_by_index = {e["instructionIndex"]: e for e in events}
    target_block = cfg.get("instructionToBlock", {}).get(target_index)
    reaching_rows = []
    for index in reaching_at_resolver:
        if index not in event_by_index:
            continue
        row = dict(event_by_index[index])
        row["reachesResolverCall"] = True
        row["resolverCallRva"] = hx(TARGET_CALL)
        row["predecessorRelationship"] = ("same basic block, earlier instruction" if
                                          cfg.get("instructionToBlock", {}).get(index) == target_block and index < target_index else
                                          ("later-address candidate reaches resolver only through a CFG backedge/loop path"
                                           if index > target_index else
                                           "earlier CFG instruction reaches resolver through successor/predecessor path"))
        reaching_rows.append(row)
    buffer_offset = displacement - buffer_base_disp
    last_producer = {
        "status": "POTENTIAL_DYNAMIC_BUFFER_PRODUCERS_FIELD_SPECIFIC_STORE_UNRESOLVED",
        "bufferBaseExpression": "RBP-0x30",
        "bufferFieldOffset": hx(buffer_offset),
        "callSites": buffer_calls,
        "detail": "The helpers write into this stack-local output buffer through data-dependent offsets. No fixed-offset store to this exact field was found, so the exact field writer/source is not promoted."
    }
    return {"normalizedLocation": {**classification, "rbpDisplacement": hx(displacement),
                                    "bufferBaseExpression": "RBP-0x30", "bufferFieldOffset": hx(buffer_offset)},
            "classification": classification["classification"],
            "reachingDefinitions": reaching_rows,
            "directOrAliasedStoreCandidates": events,
            "readEvidence": reads,
            "lastProvenProducer": last_producer,
            "valueOrigin": {"status": "UNSOLVED_FIELD_WITHIN_HELPER_BUILT_LOCAL_BUFFER",
                            "candidateInputExpression": "entry RCX copied to R15 at 0x2807B3 and passed to buffer builders",
                            "fieldSpecificOriginProven": False},
            "callerTraces": [],
            "callerFrontier": {"directCallers": [], "status": "NO_DIRECT_REL32_CALLS_TO_LOGICAL_FUNCTION_ENTRY",
                               "note": "The function may be entered via indirect dispatch; no indirect caller/dispatch owner is inferred."},
            "firstUnresolvedBoundary": f"{hx(TARGET_CALL)} reads the field from the function-local buffer, but the exact byte/field producer inside the variable-offset helper output at RBP-0x30 is not statically isolated; caller/dispatcher provenance is not established.",
            "status": "PARTIAL_STATIC" if classification.get("status") == "PROVEN_STATIC" else "UNSOLVED"}


def extract_buffer_producer_evidence(image: StaticImage, instructions: list[Any], frame_model: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sites = ((0x2807B6, 0x8DA7C0), (0x2807C8, 0x8D5CA0))
    rows = []
    for call_site, target in sites:
        ins = next((i for i in instructions if i.address == call_site), None)
        if ins is None or call_target(ins) != target:
            raise RuntimeError(f"expected local-buffer producer call missing at {hx(call_site)}")
        previous = [instruction_row(i) for i in instructions if call_site - 0x20 <= i.address < call_site]
        rows.append({"callsiteRva": hx(call_site), "targetRva": hx(target), "callInstruction": instruction_row(ins),
                     "preCallArgumentSetup": previous[-5:], "destinationPointerExpression": "RDX = RBP-0x30",
                     "inputPointerExpression": "RCX = entry RCX / R15", "staticRole": "writes or builds variable-offset data into caller-provided local buffer",
                     "fieldOffsetsWrittenProven": [], "fieldSpecificTargetWrite": False,
                     "evidenceStatus": "BUFFER_DESTINATION_CONFIRMED; EXACT +0x38/+0x78 FIELD ORIGIN UNRESOLVED"})
    builder_a, a_ins = image.function_instructions(0x8DA7C0)
    builder_b, b_ins = image.function_instructions(0x8D5CA0)
    continuation_bounds = image.function_for(0x8D5D56)
    continuation = image.disassemble(int(continuation_bounds["startRva"], 16), int(continuation_bounds["endRva"], 16)) if continuation_bounds else []
    writer_evidence = {
        "0x8DA7C0": {"pdata": builder_a, "destinationRegisterSetup": next((instruction_row(i) for i in a_ins if i.address == 0x8DA7D7), None),
                      "fixedDestinationStore": next((instruction_row(i) for i in a_ins if i.address == 0x8DA8AC), None),
                      "variableDestinationCalls": [instruction_row(i) for i in a_ins if call_target(i) in {0x12A2560, 0x12A1EC0}]},
        "0x8D5CA0": {"pdata": builder_b, "destinationRegisterSetup": next((instruction_row(i) for i in b_ins if i.address == 0x8D5CA9), None),
                      "variableDestinationStoreEvidence": [instruction_row(i) for i in continuation if i.address in {0x8D5D77, 0x8D5DA3, 0x8D5DCC, 0x8D5DF7, 0x8D5E25, 0x8D5E46}],
                      "continuationPdata": continuation_bounds},
    }
    return rows, writer_evidence


def verify_parent(parent: dict[str, Any], required_maps: dict[str, dict[str, Any]]) -> None:
    if parent.get("analysisMode") != "OFFLINE_STATIC_ONLY" or not parent.get("build", {}).get("fingerprintMatches"):
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: CODE-0001 map is not the supported offline map")
    if parent.get("convergence", {}).get("status") != "PARTIAL_STATIC":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: CODE-0001 convergence status is not PARTIAL_STATIC")
    back = parent.get("placementBackwardSlice", {})
    if back.get("resolverCall", {}).get("call", {}).get("instructionRva") != hx(TARGET_CALL) or back.get("resolverCall", {}).get("targetRva") != hx(RESOLVER):
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: resolver anchor differs")
    if not any(row.get("instructionRva") == hx(PLACEMENT_LOAD) and row.get("instruction") == "mov r8d, dword ptr [rbx]" for row in back.get("steps", [])):
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: placement R8D load differs")
    if back.get("startCallRva") != hx(PLACEMENT_CALL) or back.get("targetFunctionRva") != hx(PLACEMENT_TARGET):
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: placement call anchor differs")
    convergence = parent.get("convergence", {})
    if convergence.get("commonOwnerProven") is not False or convergence.get("selectedItemWriteToPlacementSourceProven") is not False or convergence.get("blueprintRecordConnectionProven") is not False:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: CODE-0001 negative claims changed")
    if parent.get("observerDecision", {}).get("install") is not False:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: observer gate changed")
    for name, report in required_maps.items():
        build = report.get("build") or report.get("executable") or {}
        digest = build.get("sha256")
        if digest and digest.upper() != SUPPORTED_SHA256:
            raise RuntimeError(f"required static map {name} has a mismatched executable fingerprint")


def correlation(status: str, source: str, target: str, instructions: list[dict[str, Any]], contradictions: list[str], pointer_identity: str = "NOT_ESTABLISHED") -> dict[str, Any]:
    return {"status": status, "sourceEvidence": source, "targetEvidence": target,
            "connectingInstructions": instructions, "pointerIdentity": pointer_identity,
            "contradictions": contradictions}


def build_report(exe: Path, repo: Path, types_path: Path) -> dict[str, Any]:
    if not types_path.is_file():
        raise FileNotFoundError(f"required reflection cache is missing: {types_path}")
    parent_path = repo / "bridge" / "blueprint_selection_authority_static_map.json"
    parent = load_json(parent_path)
    static_paths = {
        "createBuildingItem": repo / "bridge" / "create_building_item_static_map.json",
        "clientPlayerInput": repo / "bridge" / "client_player_input_static_map.json",
        "dispatcher": repo / "bridge" / "semantic_action_dispatcher_static_map.json",
        "snap": repo / "bridge" / "snap_candidate_selection_static_map.json",
        "commit": repo / "bridge" / "building_commit_transform_static_map.json",
        "placement": repo / "bridge" / "placement_blueprint_authority_static_map.json",
    }
    required_maps = {name: load_json(path) for name, path in static_paths.items()}
    verify_parent(parent, required_maps)
    image = StaticImage(exe.resolve())
    logical = unwind_chained_logical_function(image, TARGET_CALL)
    logical_start = int(logical["logicalRange"]["startRva"], 16)
    logical_end = int(logical["logicalRange"]["endRva"], 16)
    instructions = image.disassemble(logical_start, logical_end)
    frame_model, prologue = derive_frame_model(image, logical)
    cfg = build_basic_blocks(instructions)
    by_addr = {ins.address: idx for idx, ins in enumerate(instructions)}
    call_index = by_addr.get(TARGET_CALL)
    if call_index is None or call_target(instructions[call_index]) != RESOLVER:
        raise RuntimeError("resolver call anchor does not decode as 0x28089E -> 0xCB4B50")
    frame_loads = {"rbp08LoadRva": 0x280897, "rbp48LoadRva": 0x28088B,
                   "keyDereferenceRva": 0x28089B}
    for rva in frame_loads.values():
        if rva not in by_addr:
            raise RuntimeError(f"expected frame-input instruction missing at {hx(rva)}")
    r8_call_index = by_addr.get(PLACEMENT_CALL)
    if r8_call_index is None or call_target(instructions[r8_call_index]) != PLACEMENT_TARGET:
        raise RuntimeError("placement call anchor differs from supported build")
    leaf_unwind = logical["leafUnwind"]
    primary_unwind = logical["primaryUnwind"]
    if frame_model.get("rbpOffsetFromEntry") is None:
        raise RuntimeError("RBP stack anchor could not be normalized safely")
    prologue_end = int(logical["primaryPdata"]["startRva"], 16) + int(primary_unwind["prologueSize"])
    rsp_writes_before_resolver = stack_pointer_writes_between(instructions, prologue_end, TARGET_CALL)
    frame_model["rspWritesBetweenPrologueAndResolver"] = rsp_writes_before_resolver
    frame_model["rspStableFromPrologueToResolver"] = not rsp_writes_before_resolver
    frame_model["rspStabilityEvidence"] = {
        "interval": [hx(prologue_end), hx(TARGET_CALL)],
        "persistentWritesFound": rsp_writes_before_resolver,
        "ordinaryCallsExcluded": "CALL/RET pairs are treated as net-zero stack movement; explicit RSP updates and push/pop/enter/leave remain listed."
    }
    local_buffer_base = -0x30
    buffer_calls, writer_evidence = extract_buffer_producer_evidence(image, instructions, frame_model)
    calls_to_entry = direct_callers(image, logical_start)
    caller_inputs = preserve_caller_callsite_separation(calls_to_entry)
    rbp08 = make_slot_provenance(image, instructions, cfg, frame_model, 0x08, local_buffer_base, buffer_calls)
    rbp48 = make_slot_provenance(image, instructions, cfg, frame_model, 0x48, local_buffer_base, buffer_calls)
    # The return boundary from 0xCB4B50 is linked by instructions, while its
    # relation to the placement VoxelBlueprint cache remains unproven.
    resolver_bounds, resolver_ins = image.function_instructions(RESOLVER)
    resolver_rows = [instruction_row(i) for i in resolver_ins]
    resolver_selected = [row for row in resolver_rows if int(row["instructionRva"], 16) in {0xCB4B50, 0xCB4B58, 0xCB4B5A, 0xCB4B5C, 0xCB4B60, 0xCB4B65, 0xCB4B6A, 0xCB4B6F, 0xCB4B72, 0xCB4B77, 0xCB4B79, 0xCB4B7D}]
    return_use = [instruction_row(ins) for ins in instructions if ins.address in {0x28089E, 0x2808A3, PLACEMENT_LOAD, PLACEMENT_CALL}]
    def step_with_cfg(rva: int, source: str, destination: str) -> dict[str, Any]:
        index = by_addr[rva]
        block_id = cfg.get("instructionToBlock", {}).get(index)
        block = next((row for row in cfg["blocks"] if row["id"] == block_id), None)
        return {**instruction_row(instructions[index]), "sourceExpression": source,
                "destinationExpression": destination,
                "basicBlock": ({"id": block_id, "startRva": hx(block["start"]), "endRva": hx(block["end"])}
                               if block else None),
                "predecessorBlocks": cfg["predecessors"].get(block_id, []) if block_id is not None else [],
                "evidenceStatus": "PROVEN_STATIC_INSTRUCTION"}

    args = [
        {"register": "ECX", "definition": step_with_cfg(0x280897, "qword ptr [RBP+0x08]", "RCX"),
         "derivation": [step_with_cfg(0x280897, "localBuffer+0x38", "RCX"),
                        step_with_cfg(0x28089B, "dword ptr [*(RBP+0x08)+0x30]", "ECX")],
         "role": "KEY_LIKE_SCALAR", "roleEvidence": "CB4B50 tests ECX for zero and passes its saved address to CA5BC0", "ownerSemantics": "UNKNOWN"},
        {"register": "RDX", "definition": step_with_cfg(0x28088B, "qword ptr [RBP+0x48]", "RDX"),
         "derivation": [step_with_cfg(0x28088B, "localBuffer+0x78", "RDX")],
         "role": "LOOKUP_CONTAINER_OR_OWNER_LIKE_INPUT", "roleEvidence": "CB4B50 forms RCX=RDX+0x38 and passes it as CA5BC0 lookup container", "ownerSemantics": "UNKNOWN"},
    ]
    correlated = {
        "createBuildingItem": correlation("NOT_CONNECTED", "CODE-0001 frame-local fields produced by a helper-built buffer", "CreateBuildingItemAction reflection/action maps report no action-specific consumer or complete field flow", [], ["No connected pointer/dataflow edge from this stack buffer to CreateBuildingItemAction.itemId or selectedIndex." ]),
        "clientPlayerInput": correlation("NOT_CONNECTED", "The frame values are local-buffer fields; entry RCX's caller is unresolved", "ClientPlayerInput reflected +0x1B0 CreateBuildingItemAction member and live identity remain unresolved", [], ["No pointer identity or caller producer connects the local buffer to ClientPlayerInput.data." ]),
        "serverConsumedPlayerInput": correlation("NOT_CONNECTED", "Frame-local buffer has no identified input owner", "ServerConsumedPlayerInput consumed action offsets are layout-only evidence", [], ["No common base accesses the relevant consumed version and these frame slots." ]),
        "semanticActionDispatcher": correlation("NOT_CONNECTED", "No dispatcher pointer is present in the connected frame slice", "InventoryTransferAction envelope is a reference pattern only", [], ["No CreateBuildingItemAction dispatch edge reaches this function or its input buffer." ]),
        "snapPreview": correlation("NOT_CONNECTED", "Resolver inputs are local-buffer-derived", "Snap accepted collections remain caller-local with separate 0x3EB810/0x99F970 frontiers", [], ["No register/base identity links either local-buffer field to the accepted snap arrays or preview writeback." ]),
        "blueprintCache": {"status": "RESOLVER_RETURN_CONNECTED_CACHE_OWNERSHIP_UNPROVEN",
                           "sourceEvidence": "RBP+0x48 -> RDX at 0x28089E; resolver uses input RDX+0x38 for its lookup root",
                           "targetEvidence": "RAX return -> RBX at 0x2808A3 -> dword [RBX] at 0x280F75 -> R8D to 0x3E2CD0",
                           "connectingInstructions": [instruction_row(instructions[by_addr[a]]) for a in (0x28088B, 0x28089E, 0x2808A3, 0x280F75, 0x280F86)],
                           "resolverRecordPointerConnection": "PROVEN_STATIC_BUILD_1076226",
                           "VoxelBlueprintOrCA90E0CacheOwnership": "NOT_ESTABLISHED",
                           "pointerIdentity": "INPUT_CONTAINER_TO_LOOKUP_RESULT_RELATION_ONLY; NO_SINGLE_OWNER_IDENTITY",
                           "contradictions": ["CB4B50 is an Item-ID lookup helper and its returned record's semantic type is not proven to be VoxelBlueprintItem or the CA90E0 placement cache.", "The known placement cache family uses RSI+0xF0/CA90E0 in separate consumers; no pointer-identity chain connects it to these local stack fields."]},
    }
    evidence = [
        {"claim": "RBP is a manually established stack anchor and target displacements are inside the local allocation", "instructionEvidence": [instruction_row(i) for i in prologue], "unwindEvidence": primary_unwind},
        {"claim": "Both slots alias fields of the local buffer passed to helpers", "instructionEvidence": [instruction_row(instructions[by_addr[a]]) for a in (0x2807AF, 0x2807B6, 0x2807C1, 0x2807C8, 0x28088B, 0x280897, 0x28089B)]},
        {"claim": "RBP+0x48-derived input participates in resolver result path to RBX/R8D", "instructionEvidence": correlated["blueprintCache"]["connectingInstructions"]},
    ]
    status = "PARTIAL_STATIC"
    return {
        "schemaVersion": 1, "tool": "scan_placement_frame_input_provenance_static.py",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "parentEvidence": {"delivery": "CODE-0001", "map": "bridge/blueprint_selection_authority_static_map.json",
                           "status": parent["convergence"]["status"], "mapFingerprintMatches": parent["build"]["fingerprintMatches"],
                           "preservedAnchors": [hx(TARGET_CALL), hx(RESOLVER), hx(PLACEMENT_LOAD), hx(PLACEMENT_CALL), hx(PLACEMENT_TARGET)]},
        "build": {"revision": REVISION, "sha256": image.digest, "supportedSha256": SUPPORTED_SHA256,
                  "fingerprintMatches": image.digest == SUPPORTED_SHA256, "imageBase": hx(image.base),
                  "imageSize": hx(image.pe.OPTIONAL_HEADER.SizeOfImage), "executablePath": str(image.path),
                  "reflectionCachePath": str(types_path.resolve())},
        "safety": {"processAccess": False, "debugApis": False, "writesExecutable": False,
                   "writesGameMemory": False, "runtimeHooksInstalled": False, "usesStagingObjectAsEvidence": False},
        "anchor": {"resolverCallRva": hx(TARGET_CALL), "resolverTargetRva": hx(RESOLVER),
                   "itemLoadRva": hx(PLACEMENT_LOAD), "placementCallRva": hx(PLACEMENT_CALL), "placementTargetRva": hx(PLACEMENT_TARGET)},
        "frameModel": {"functionStartRva": logical["logicalRange"]["startRva"], "functionEndRva": logical["logicalRange"]["endRva"],
                       "containingPdataEntry": logical["leafPdata"], "primaryPdataEntry": logical["primaryPdata"],
                       "rbpModelStatus": frame_model["rbpModelStatus"], "rbpOffsetFromEntryRsp": frame_model["rbpOffsetFromEntry"],
                       "rspOffsetFromEntryRspAtResolver": frame_model["rspOffsetFromEntry"],
                       "normalizedRspAtEntryExpression": frame_model["entryRspExpression"],
                       "normalizedCurrentRspExpression": frame_model["currentRspExpression"],
                       "rspStableFromPrologueToResolver": frame_model["rspStableFromPrologueToResolver"],
                       "rspStabilityEvidence": frame_model["rspStabilityEvidence"],
                       "localStackRangeFromEntryRsp": frame_model["localStackRangeFromEntryRsp"],
                       "normalizedRbpPlus08": rbp08["normalizedLocation"], "normalizedRbpPlus48": rbp48["normalizedLocation"],
                       "prologueEvidence": [instruction_row(i) for i in prologue],
                       "unwindEvidence": {"primary": primary_unwind, "chainedContinuation": leaf_unwind},
                       "contradictionsOrAmbiguities": ["UNWIND_INFO frame-register nibble is zero; RBP is not declared as an unwind frame register.",
                                                        "The decoded primary prologue nevertheless explicitly establishes RBP as a stack-relative anchor.",
                                                        "RBP+0x08/+0x48 would look like positive RBP offsets in isolation, but normalize within the allocated local frame, not to Win64 incoming stack arguments."]},
        "resolverCallsite": {"call": instruction_row(instructions[call_index]), "arguments": args,
                             "resolverFunction": {"range": resolver_bounds, "bodyEvidence": resolver_selected,
                                                  "classifications": {"ECX": "KEY_LIKE_SCALAR", "RDX": "LOOKUP_CONTAINER_OR_OWNER_LIKE_INPUT"}},
                             "returnUse": return_use,
                             "directCallerScan": {"functionEntryRva": logical["logicalRange"]["startRva"],
                                                  "directRelativeCallers": caller_inputs,
                                                  "status": "NO_DIRECT_REL32_CALLERS_FOUND" if not caller_inputs else "DIRECT_CALLERS_FOUND",
                                                  "indirectDispatch": "NOT_FOLLOWED"}},
        "localBufferConstruction": {"baseExpression": "RBP-0x30", "bufferCallSites": buffer_calls,
                                    "writerFunctionEvidence": writer_evidence,
                                    "laterReadOnlyOrReadUseEvidence": [
                                        {"callsiteRva": "0x280826", "targetRva": "0x1DFA50", "classification": "READ_ONLY_QUERY_FROM_LOCAL_BUFFER+0x08",
                                         "instructionEvidence": [instruction_row(i) for i in image.disassemble(0x1DFA50, 0x1DFA90)]},
                                        {"callsiteRva": "0x280882", "targetRva": "0x1D92D0", "classification": "CONSUMES_BUFFER+0x08_AS_SOURCE; OUTPUT_COLLECTION_IS_A_SEPARATE_ARGUMENT",
                                         "instructionEvidence": [instruction_row(i) for i in image.disassemble(0x1D92D0, 0x1D92F9)]}],
                                    "fixedOffsetWriteToTargetSlotsFound": False,
                                    "interpretation": "The two resolver inputs are fields within a helper-built stack-local buffer. Helpers write/copy through data-dependent offsets; no exact field-level source or semantic owner is proven."},
        "rbp08Provenance": rbp08,
        "rbp48Provenance": rbp48,
        "crossSystemCorrelation": correlated,
        "convergenceDelta": {"rbp08NormalizedToConcreteLocalOrIncoming": "LOCAL_STACK_SLOT",
                             "rbp48NormalizedToConcreteLocalOrIncoming": "LOCAL_STACK_SLOT",
                             "rbp08OwnerProven": False, "rbp48OwnerProven": False,
                             "selectionConnectionProven": False, "previewConnectionProven": False,
                             "blueprintRecordConnectionProven": False,
                             "resolverReturnedRecordPointerConnectionProven": True,
                             "commonOwnerProven": False, "status": status,
                             "evidence": evidence,
                             "contradictions": ["Local storage and helper-buffer provenance do not identify the longer-lived object/configuration owner.",
                                                "The resolver's lookup return is connected to RBX, but that does not identify it as the VoxelBlueprint or CA90E0 cache record.",
                                                "No direct relative-call site to the logical function entry was found; an indirect dispatch path remains possible."]},
        "observerDecision": {"install": False, "failClosed": True, "reason": "CODE-0002 is static provenance only; local field writers and caller/dispatcher ownership remain unresolved."},
        "nextEvidence": [
            "CODE-0003 should statically map the data-dependent output layout written by 0x8DA7C0 and 0x8D5CA0, then prove or reject which source writes localBuffer+0x38 and localBuffer+0x78.",
            "Find the indirect entry/dispatch reference to the logical function 0x280790..0x2810E8 and recover its RCX source without assuming a semantic type.",
            "Only after a concrete owner/base is recovered, compare instruction-connected edges against CreateBuildingItemAction, ClientPlayerInput, preview/snap, and CA90E0 consumers.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    frame = report["frameModel"]
    a, b = report["rbp08Provenance"], report["rbp48Provenance"]
    corr = report["crossSystemCorrelation"]
    conv = report["convergenceDelta"]
    lines = [
        "# Placement Frame-Input Provenance — Static Map v1", "",
        f"**Scope:** Enshrouded revision {report['build']['revision']}; executable SHA-256 `{report['build']['sha256']}`.",
        "Static/offline only. No process access, runtime observer, game-memory mutation, executable patch, or deployed-DLL change.", "",
        "## Parent CODE-0001 frontier", "",
        "CODE-0001 remains PARTIAL_STATIC: `0x28089E -> 0xCB4B50`, `0x280F75` loads R8D from `[RBX]`, and `0x280F86 -> 0x3E2CD0`. Common owner, action-item write into the placement source, and VoxelBlueprint/cache connection remain unproven. The observer gate remains disabled.", "",
        "## Containing function and RBP/frame model", "",
        f"Logical chained function range: `{frame['functionStartRva']}..{frame['functionEndRva']}`. RBP model: **{frame['rbpModelStatus']}**. The primary prologue and unwind data show `RBP = entryRSP - 0x76D8`; after the fixed `0x77C8` allocation, current RSP is `RBP-0x100`. Thus `RBP+0x08` is `currentRSP+0x108` and `RBP+0x48` is `currentRSP+0x148`, both inside the local allocation. These are not incoming stack arguments.", "",
        "Prologue/unwind evidence:", "",
    ]
    for row in frame["prologueEvidence"]:
        lines.append(f"- `{row['instructionRva']}` `{row['instruction']}` (`{row['bytes']}`).")
    lines.extend(["", "## RBP+0x08 provenance", "",
                  f"Classification: **{a['classification']}**; normalized as `{a['normalizedLocation']['normalizedExpression']}`. It aliases `localBuffer+0x38` where the local buffer base is `[RBP-0x30]`. The resolver path loads this qword at `0x280897`, then reads dword `[RCX+0x30]` at `0x28089B` into ECX.",
                  f"Last field-specific producer: unresolved. CFG may-reaching helper calls: {', '.join(row['instructionRva'] for row in a['reachingDefinitions'])}. These are possible writes through a target-containing output buffer, not proven field-level stores; no fixed store to this exact field is proven.",
                  f"First unresolved boundary: {a['firstUnresolvedBoundary']}", "",
                  "## RBP+0x48 provenance", "",
                  f"Classification: **{b['classification']}**; normalized as `{b['normalizedLocation']['normalizedExpression']}`. It aliases `localBuffer+0x78`; `0x28088B` loads it into RDX for the resolver call.",
                  f"Last field-specific producer: unresolved. CFG may-reaching helper calls: {', '.join(row['instructionRva'] for row in b['reachingDefinitions'])}. These are possible writes through a target-containing output buffer, not proven field-level stores; exact field offset/value source is not isolated.",
                  f"First unresolved boundary: {b['firstUnresolvedBoundary']}", "",
                  "## Direct caller traces", "",
                  f"No direct relative-call references to the logical function entry `{frame['functionStartRva']}` were found. The incoming register value copied from RCX to R15 at `0x2807B3` is passed to the helper builders, but its caller/indirect dispatcher is unresolved. No incoming stack-argument mapping was claimed.", "",
                  "## Resolver call contract at 0x28089E", "",
                  "- ECX is a key-like scalar: `[RBP+0x08]` is dereferenced at `+0x30`; `0xCB4B50` saves/tests ECX and passes its address to `0xCA5BC0`.",
                  "- RDX is a container/owner-like input: `0xCB4B50` derives a lookup root at `RDX+0x38` and passes it to `0xCA5BC0`.",
                  "- The resolver result flows RAX → RBX (`0x2808A3`) → `[RBX]` to R8D (`0x280F75`) → placement call `0x280F86`.",
                  "These roles do not establish semantic ownership or identify the returned record as a VoxelBlueprint/cache record.", "",
                  "## Cross-system correlation", ""])
    for name, row in corr.items():
        lines.append(f"- **{name}:** {row.get('status')}. {row.get('contradictions', [''])[0] if row.get('contradictions') else ''}")
    lines.extend(["", "## Convergence delta versus CODE-0001", "",
                  f"Both frame locations normalize to local stack slots; neither longer-lived owner is proven. Selection connection: `{conv['selectionConnectionProven']}`. Preview/snap connection: `{conv['previewConnectionProven']}`. VoxelBlueprint/cache connection: `{conv['blueprintRecordConnectionProven']}`. The separate resolver-return pointer connection to RBX is proven. Common owner: `{conv['commonOwnerProven']}`. Overall: **{conv['status']}**.", "",
                  "## PROVEN_STATIC / INFERRED / UNSOLVED", "",
                  "- **PROVEN_STATIC:** chained `.pdata` relationship; unwind/prologue stack arithmetic; both RBP displacements lie in the local frame; both locations alias offsets `+0x38/+0x78` in the local buffer; RCX/RDX expressions at the resolver; resolver return path to RBX and R8D.",
                  "- **INFERRED:** the local buffer is populated from the entry RCX/R15 source by helper routines, based on their argument setup and destination writes. This does not prove which source member writes either target field.",
                  "- **UNSOLVED:** exact field writers and source members; indirect function-entry caller; semantic owner; action/player-input/preview/cache identity.", "",
                  "## Rejected interpretations", "",
                  "Positive RBP displacements are not treated as incoming arguments: unwind/prologue arithmetic places them inside the local frame. Similar offsets, resolver use, or a connected resolver-return pointer do not prove player, selection, preview, or VoxelBlueprint ownership. The staging object is not used as evidence.", "",
                  "## Exact next static boundary", "",
                  *[f"- {item}" for item in report["nextEvidence"]], "",
                  "**No runtime hook, game-memory mutation, executable patch, or native DLL change was added.**", ""])
    return "\n".join(lines)


def main() -> int:
    game_root = Path(__file__).resolve().parents[4]
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=game_root / "enshrouded.exe")
    parser.add_argument("--types", type=Path, default=game_root / ".cache" / "types.json")
    parser.add_argument("--repo", type=Path, default=repo)
    parser.add_argument("--output", type=Path, default=repo / "bridge" / "placement_frame_input_provenance_static_map.json")
    parser.add_argument("--doc", type=Path, default=repo / "docs" / "research" / "PlacementFrameInputProvenance-StaticMap-v1.md")
    args = parser.parse_args()
    report = build_report(args.exe.resolve(), args.repo.resolve(), args.types.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"executableSha256": report["build"]["sha256"],
                      "functionRange": [report["frameModel"]["functionStartRva"], report["frameModel"]["functionEndRva"]],
                      "rbpModel": report["frameModel"]["rbpModelStatus"],
                      "rbp08": {"classification": report["rbp08Provenance"]["classification"], "status": report["rbp08Provenance"]["status"]},
                      "rbp48": {"classification": report["rbp48Provenance"]["classification"], "status": report["rbp48Provenance"]["status"]},
                      "convergenceDelta": report["convergenceDelta"]["status"],
                      "observerDecision": report["observerDecision"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
