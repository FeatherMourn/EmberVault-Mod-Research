#!/usr/bin/env python3
"""Offline, fail-closed x64 whole-instruction relocation planner.

This module deliberately plans bytes only.  It never opens a process, allocates
executable memory, or patches an image.  A caller may provide a PE and RVA, or
an explicit synthetic byte stream for tests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import capstone
from capstone.x86 import X86_OP_MEM, X86_OP_IMM


@dataclass(frozen=True)
class InstructionPlan:
    rva: int
    size: int
    bytes_hex: str
    mnemonic: str
    operands: str
    relocation: str
    target_rva: int | None = None
    rip_disp_offset: int | None = None
    rip_disp_size: int | None = None


def _md() -> capstone.Cs:
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    return md


def decode(data: bytes, base_rva: int = 0, max_instructions: int = 64) -> list[Any]:
    return list(_md().disasm(data, base_rva, count=max_instructions))


def _relative(ins: Any) -> tuple[str, int | None] | None:
    if not ins.operands:
        return None
    # x86 direct branch/call targets are represented as immediate operands.
    if ins.mnemonic.lower() in {"call", "jmp"} or ins.mnemonic.lower().startswith("j"):
        op = ins.operands[0]
        if op.type == X86_OP_IMM:
            return ins.mnemonic.upper(), int(op.imm)
    return None


def _rip_operand(ins: Any) -> tuple[int, int] | None:
    for op in ins.operands:
        if op.type == X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_RIP:
            # displacement position/width are exposed by Capstone's encoding.
            enc = getattr(ins, "encoding", None)
            if enc is not None:
                return int(enc.disp_offset), int(enc.disp_size)
            return (0, 4)
    return None


def _classify(ins: Any, selected_start: int, selected_end: int) -> tuple[str, int | None, int | None, int | None]:
    rel = _relative(ins)
    if rel:
        kind, target = rel
        # Direct control flow is intentionally fail-closed in this first
        # capability: preserving CALL/Jcc semantics requires a reviewed
        # emitter, not a raw byte copy.
        return "REWRITE_REQUIRED", target, None, None
    rip = _rip_operand(ins)
    if rip:
        return "REWRITE_REQUIRED", None, rip[0], rip[1]
    return "ORDINARY_COPY", None, None, None


def plan_from_bytes(data: bytes, *, site_rva: int = 0, minimum_patch_bytes: int = 12,
                    external_targets: list[int] | None = None) -> dict[str, Any]:
    if minimum_patch_bytes <= 0:
        raise ValueError("minimum_patch_bytes must be positive")
    instructions = decode(data, site_rva)
    if not instructions or instructions[0].address != site_rva:
        return {"status": "REJECTED", "reason": "decodeFailed", "siteRva": site_rva}
    chosen: list[Any] = []
    total = 0
    for ins in instructions:
        chosen.append(ins)
        total += ins.size
        if total >= minimum_patch_bytes:
            break
    if total < minimum_patch_bytes:
        return {"status": "REJECTED", "reason": "insufficientDecodedBytes", "siteRva": site_rva}
    start, end = site_rva, site_rva + total
    rows: list[InstructionPlan] = []
    unsupported: list[str] = []
    for ins in chosen:
        cls, target, disp_off, disp_size = _classify(ins, start, end)
        if cls != "ORDINARY_COPY":
            unsupported.append(cls)
        rows.append(InstructionPlan(ins.address, ins.size, bytes(ins.bytes).hex(), ins.mnemonic,
                                    ins.op_str, cls, target, disp_off, disp_size))
    # Caller-supplied CFG edges allow rejection of an external branch landing
    # inside a displaced instruction span; no heuristic memory scan is used.
    # Inspect the supplied surrounding instruction stream as a bounded CFG
    # witness.  Additional caller-provided edges are accepted, but no memory
    # outside the supplied bytes is searched.
    edge_targets = set(external_targets or [])
    chosen_addresses = {ins.address for ins in chosen}
    for ins in instructions:
        if ins.address in chosen_addresses:
            continue
        rel = _relative(ins)
        if rel and rel[1] is not None:
            edge_targets.add(rel[1])
    inner_targets = sorted({t for t in edge_targets if start < t < end})
    identity = {"siteRva": site_rva, "originalBytes": "".join(r.bytes_hex for r in rows),
                "instructions": [asdict(r) for r in rows], "continuationRva": end}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    reason = None
    status = "PLANNED"
    if inner_targets:
        status, reason = "REJECTED", "externalBranchIntoDisplacedSpan"
    elif unsupported:
        status, reason = "REJECTED", "relocationRequiresReviewedRewrite"
    identity.update({"status": status, "reason": reason, "planHash": digest,
                     "siteRva": site_rva, "spanBytes": total, "minimumPatchBytes": minimum_patch_bytes,
                     "continuationRva": end, "branchTargetsIntoSpan": inner_targets})
    return identity


def plan_from_pe(path: Path, site_rva: int, minimum_patch_bytes: int = 12) -> dict[str, Any]:
    import pefile
    pe = pefile.PE(str(path), fast_load=True)
    raw = pe.get_data(site_rva, 96)
    return plan_from_bytes(raw, site_rva=site_rva, minimum_patch_bytes=minimum_patch_bytes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", type=Path)
    ap.add_argument("--rva", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--minimum", type=int, default=12)
    ap.add_argument("--bytes", dest="hex_bytes")
    ap.add_argument("--external-target", action="append", default=[])
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if bool(args.exe) == bool(args.hex_bytes):
        ap.error("provide exactly one of --exe or --bytes")
    if args.hex_bytes:
        data = bytes.fromhex(args.hex_bytes.replace(" ", ""))
        result = plan_from_bytes(data, site_rva=args.rva, minimum_patch_bytes=args.minimum,
                                 external_targets=[int(x, 0) for x in args.external_target])
    else:
        result = plan_from_pe(args.exe, args.rva, args.minimum)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result.get("status") == "PLANNED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
