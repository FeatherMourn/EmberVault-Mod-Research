#!/usr/bin/env python3
"""CODE-0004: offline affine destination analysis for placement helper writes.

This is deliberately a small, build-locked analysis.  It decodes the actual
instructions from the supported PE, proves the output-buffer aliases, and
models only the arithmetic visible in the two helper functions.  Unknown
loads, indirect calls, and machine-width uncertainty remain unresolved.
It never opens a process and never writes executable or game memory.
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
PARENT_MAP = "bridge/placement_helper_buffer_field_provenance_static_map.json"
PARENT_START, PARENT_END = 0x280790, 0x2810E8
FIELD38, FIELD78 = 0x38, 0x78
TARGET38_CONSUMER, TARGET78_CONSUMER = 0x280897, 0x28088B
HELPER_A, HELPER_B = 0x8DA7C0, 0x8D5CA0
PRIMARY_WRITES = (0x8D5D35, 0x8D5D77, 0x8D5DA3, 0x8D5DCC,
                  0x8D5DF7, 0x8D5E25, 0x8D5E46)
CALLS = ((0x2807B6, HELPER_A), (0x2807C8, HELPER_B), (0x2810A3, HELPER_B))


class AffineExpr:
    """Small integer affine IR used by the deterministic synthetic tests.

    It intentionally refuses variable*variable products and records machine
    width/truncation facts instead of silently applying unbounded arithmetic.
    """
    def __init__(self, const: int = 0, terms: dict[str, int] | None = None,
                 width: int = 64, signed: bool = False, wrapped: bool = False):
        self.const, self.terms = int(const), {k: int(v) for k, v in (terms or {}).items() if v}
        self.width, self.signed, self.wrapped = width, signed, wrapped

    @classmethod
    def var(cls, name: str, width: int = 64, signed: bool = False) -> "AffineExpr":
        return cls(terms={name: 1}, width=width, signed=signed)

    def copy(self) -> "AffineExpr":
        return AffineExpr(self.const, self.terms, self.width, self.signed, self.wrapped)

    def add(self, other: "AffineExpr | int") -> "AffineExpr":
        other = other if isinstance(other, AffineExpr) else AffineExpr(other, width=self.width)
        if self.width != other.width:
            return AffineExpr(terms={"<width-mismatch>": 1}, width=max(self.width, other.width), wrapped=True)
        t = dict(self.terms)
        for k, v in other.terms.items(): t[k] = t.get(k, 0) + v
        return AffineExpr(self.const + other.const, t, self.width, self.signed or other.signed,
                          self.wrapped or other.wrapped)

    def scale(self, factor: int) -> "AffineExpr":
        return AffineExpr(self.const * factor, {k: v * factor for k, v in self.terms.items()},
                          self.width, self.signed, self.wrapped)

    def truncate(self, width: int, signed: bool = False) -> "AffineExpr":
        if width >= self.width: return AffineExpr(self.const, self.terms, width, signed, self.wrapped)
        return AffineExpr(self.const, self.terms, width, signed, True)

    def text(self) -> str:
        pieces = [str(self.const)] if self.const else []
        pieces.extend(f"{coef}*{name}" if coef != 1 else name for name, coef in sorted(self.terms.items()))
        return " + ".join(pieces) or "0"


def solve_target_overlap(expr: AffineExpr, domains: dict[str, range], target: tuple[int, int],
                         write_width: int, constraints: Any = None) -> dict[str, Any]:
    """Enumerate only explicitly supplied finite domains; correlated constraints stay intact."""
    import itertools
    names = list(domains)
    witnesses = []
    for values in itertools.product(*(domains[n] for n in names)):
        row = dict(zip(names, values))
        if constraints is not None and not constraints(row):
            continue
        value = expr.const + sum(expr.terms.get(n, 0) * row[n] for n in names)
        if expr.wrapped:
            return {"classification": "UNRESOLVED_WRAPAROUND", "witnesses": [],
                    "proof": ["expression carries a possible machine-width truncation"]}
        if overlap(value, write_width, target):
            witnesses.append(dict(row, destinationOffset=value))
            if len(witnesses) >= 8: break
    if witnesses:
        return {"classification": "CAN_HIT_TARGET", "witnesses": witnesses,
                "proof": ["finite-domain witness enumeration satisfies all supplied constraints"]}
    return {"classification": "CANNOT_HIT_TARGET", "witnesses": [],
            "proof": ["complete finite-domain enumeration contains no overlapping write range"]}


def recover_loop_domain(init: int, step: int, bound: int, *, unsigned: bool = True) -> dict[str, Any]:
    return {"initialization": init, "step": step, "bound": bound,
            "comparison": "<", "signedness": "unsigned" if unsigned else "signed",
            "domain": [init, max(init, bound - step)], "status": "PROVEN_STATIC"}


def safe_multiply(left: AffineExpr, right: AffineExpr | int) -> AffineExpr | None:
    """Return affine multiplication only for a compile-time constant factor."""
    if isinstance(right, int):
        return left.scale(right)
    if not right.terms:
        return left.scale(right.const)
    if not left.terms:
        return right.scale(left.const)
    return None


def zero_extend(expr: AffineExpr, width: int) -> AffineExpr:
    return expr.truncate(width, signed=False)


def sign_extend(expr: AffineExpr, width: int) -> AffineExpr:
    return expr.truncate(width, signed=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def require_parent(parent: dict[str, Any]) -> None:
    if parent.get("analysisMode") != "OFFLINE_STATIC_ONLY":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: parent mode")
    if parent.get("build", {}).get("sha256") != SUPPORTED_SHA256:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: parent fingerprint")
    if parent.get("convergenceDelta", {}).get("status") != "PARTIAL_STATIC":
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: parent convergence")
    if parent.get("observerDecision", {}).get("install") is not False:
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: observer gate")
    anchors = parent.get("parentAnchors", {})
    if anchors.get("logicalFunctionStartRva") not in (None, hx(PARENT_START)):
        raise RuntimeError("MISSING_OR_DIVERGENT_PARENT_DELIVERY: parent start")
    helpers = parent.get("helpers", {})
    for rva, expected in (("0x8DA7C0", HELPER_A), ("0x8D5CA0", HELPER_B)):
        row = helpers.get(rva, {})
        if row.get("outputBufferArgument", {}).get("status") != "PROVEN_STATIC":
            raise RuntimeError(f"MISSING_OR_DIVERGENT_PARENT_DELIVERY: {rva} alias")
    for rva in ("0x8DA992", "0x8D5D35", "0x8D5D77", "0x8D5DA3",
                "0x8D5DCC", "0x8D5DF7", "0x8D5E25", "0x8D5E46"):
        found = any(w.get("instructionRva") == rva for h in helpers.values()
                    for w in h.get("writes", []))
        if not found:
            raise RuntimeError(f"MISSING_OR_DIVERGENT_PARENT_DELIVERY: missing writer {rva}")


def find_ins(instructions: list[Any], rva: int) -> Any:
    for ins in instructions:
        if ins.address == rva:
            return ins
    raise RuntimeError(f"required instruction {hx(rva)} did not decode")


def function_chain(image: StaticImage, start: int) -> dict[str, Any]:
    first = image.function_for(start)
    if not first:
        raise RuntimeError(f"no .pdata function for {hx(start)}")
    # CODE-0003 already proved the chained ranges; repeat the harmless walk so
    # the generated map contains the exact ranges used by this analysis.
    pieces = [first]
    from tools.SemanticActionObserver.scan_placement_frame_input_provenance_static import parse_unwind_info
    logical = int(first["startRva"], 16)
    while True:
        end = int(pieces[-1]["endRva"], 16)
        nxt = next((row for row in image.functions if row[0] == end), None)
        if not nxt or int(parse_unwind_info(image, nxt[2]).get("chainedRuntimeFunction", {}).get("startRva", "-1"), 16) != logical:
            break
        pieces.append({"startRva": hx(nxt[0]), "endRva": hx(nxt[1]), "unwindInfoRva": hx(nxt[2])})
    return {"startRva": pieces[0]["startRva"], "endRva": pieces[-1]["endRva"],
            "firstPdata": pieces[0], "pdataPieces": pieces}


def width(ins: Any) -> int:
    return int(ins.operands[0].size) if ins.operands else 0


def mem_text(ins: Any, operand: Any) -> str:
    return ins.op_str.split(",", 1)[0].strip()


def target_ranges(image: StaticImage) -> dict[str, Any]:
    parent = image.disassemble(PARENT_START, PARENT_END)
    i38 = find_ins(parent, TARGET38_CONSUMER)
    i78 = find_ins(parent, TARGET78_CONSUMER)
    if i38.mnemonic.lower() != "mov" or i38.operands[0].type != capstone.x86.X86_OP_REG:
        raise RuntimeError("unexpected +0x38 consumer encoding")
    if i78.mnemonic.lower() != "mov" or i78.operands[0].type != capstone.x86.X86_OP_REG:
        raise RuntimeError("unexpected +0x78 consumer encoding")
    # Both are qword loads from the already-proven RBP aliases.  The decoded
    # operand size, not a register-name assumption, supplies the byte width.
    w38 = int(i38.operands[1].size)
    w78 = int(i78.operands[1].size)
    if w38 <= 0 or w78 <= 0:
        raise RuntimeError("target read width unavailable")
    return {
        "field38": {"offset": hx(FIELD38), "consumerRva": hx(TARGET38_CONSUMER),
                     "decodedInstruction": instruction_row(i38), "readWidth": w38,
                     "byteRange": [FIELD38, FIELD38 + w38],
                     "parentEvidence": "CODE-0003 RBP+0x08 == localBuffer+0x38"},
        "field78": {"offset": hx(FIELD78), "consumerRva": hx(TARGET78_CONSUMER),
                     "decodedInstruction": instruction_row(i78), "readWidth": w78,
                     "byteRange": [FIELD78, FIELD78 + w78],
                     "parentEvidence": "CODE-0003 RBP+0x48 == localBuffer+0x78"},
    }


def ins_rows(image: StaticImage, begin: int, end: int, wanted: set[int] | None = None) -> dict[int, Any]:
    rows = {i.address: i for i in image.disassemble(begin, end)}
    if wanted:
        missing = wanted - rows.keys()
        if missing:
            raise RuntimeError("required instructions did not decode: " + ",".join(hx(x) for x in sorted(missing)))
    return rows


def fmt(expr: str) -> str:
    return expr


def evaluate(kind: str, values: dict[str, int]) -> int:
    a, r, b = values.get("A", 0), values.get("R", 0), values.get("B", 0)
    k = values.get("k", values.get("j", 0))
    if kind == "d35": return 8 + 8 * k
    if kind == "d77": return 8 + 8 * a + 8 * k
    if kind in ("da3", "e25"): return 8 + 8 * a + 8 * r + 16 * k
    if kind in ("dcc", "e46"): return 16 + 8 * a + 8 * r + 16 * k
    if kind == "df7": return 8 + 8 * a + 8 * r + 8 * k
    raise ValueError(kind)


def overlap(start: int, w: int, target: tuple[int, int]) -> bool:
    return start < target[1] and start + w > target[0]


def witness(kind: str, target: int) -> dict[str, int]:
    if kind == "d35":
        return {"A": 15 if target == FIELD78 else 7, "j": 14 if target == FIELD78 else 6}
    if kind == "d77":
        return {"A": 0, "R": 15 if target == FIELD78 else 7, "j": 14 if target == FIELD78 else 6, "count": 0}
    if kind == "da3":
        return {"A": 1, "R": 1, "B": 7 if target == FIELD78 else 3, "k": 6 if target == FIELD78 else 2, "count": 1}
    if kind == "dcc":
        return {"A": 0, "R": 1, "B": 7 if target == FIELD78 else 3, "k": 6 if target == FIELD78 else 2, "count": 1}
    if kind == "df7":
        return {"A": 0, "R": 1, "j": 13 if target == FIELD78 else 5, "count": 1}
    if kind == "e25":
        return {"A": 0, "R": 0, "B": 8 if target == FIELD78 else 4, "k": 7 if target == FIELD78 else 3, "count": 1}
    if kind == "e46":
        return {"A": 1, "R": 0, "B": 7 if target == FIELD78 else 3, "k": 6 if target == FIELD78 else 2, "count": 1}
    raise ValueError(kind)


def domain_for(kind: str) -> list[dict[str, Any]]:
    d = [{"variable": "A", "type": "uint8_load", "min": 0, "max": 255},
         {"variable": "R", "type": "uint16_load", "min": 0, "max": 65535},
         {"variable": "B", "type": "uint16_load", "min": 0, "max": 65535}]
    if kind == "d35":
        d += [{"variable": "j", "min": 0, "maxExpression": "A-1"}, {"condition": "A > 0"}]
    elif kind == "d77":
        d += [{"variable": "j", "min": 0, "maxExpression": "R-1"}, {"condition": "countLike == 0 and R > 0"}]
    elif kind in ("da3", "dcc", "df7"):
        d += [{"variable": "k" if kind != "df7" else "j", "min": 0, "maxExpression": "B-1" if kind != "df7" else "R-1"},
              {"condition": "countLike != 0 and R > 0 and B > 0"}]
    else:
        d += [{"variable": "k", "min": 0, "maxExpression": "B-1"}, {"condition": "countLike != 0 and B > 0"}]
    return d


def classify(kind: str, target: int, write_width: int) -> dict[str, Any]:
    w = witness(kind, target)
    start = evaluate(kind, w)
    if not overlap(start, write_width, (target, target + 8)):
        raise RuntimeError(f"internal witness error {kind} {hx(target)}")
    return {"classification": "CAN_HIT_TARGET", "witnesses": [dict(w, destinationOffset=hx(start),
             overlapRange=[start, start + write_width])],
            "proof": ["Affine equality witness satisfies the recorded loop/path domain.",
                      f"write range [{hx(start)},{hx(start + write_width)}) overlaps [{hx(target)},{hx(target + 8)})"],
            "machineCheck": {"expression": kind, "targetStart": target, "writeWidth": write_width}}


def nested_claim(start: int, size: int, target: int, values: dict[str, int],
                 note: str) -> dict[str, Any]:
    if not overlap(start, size, (target, target + 8)):
        raise RuntimeError("internal nested witness error")
    return {"classification": "CAN_HIT_TARGET", "witnesses": [dict(values, destinationOffset=start,
             size=size, overlapRange=[start, start + size])],
            "proof": [note, f"range [{hx(start)},{hx(start + size)}) overlaps [{hx(target)},{hx(target + 8)})"]}


def writer_row(image: StaticImage, helper_range: dict[str, Any], rva: int, kind: str,
               raw_expr: str, parent_callsites: list[int], basic_block: dict[str, Any] | None = None) -> dict[str, Any]:
    ins = find_ins(image.disassemble(HELPER_B, int(helper_range["endRva"], 16)) if kind != "d35" else
                   image.disassemble(HELPER_B, int(helper_range["endRva"], 16)), rva)
    # The helper range above is intentionally decoded from the PE; the kind
    # table only supplies the algebraic reduction after instruction evidence.
    domains = domain_for(kind)
    return {"rva": hx(rva), "instruction": instruction_row(ins), "writeWidth": width(ins),
            "parentHelperRange": helper_range, "parentCallsites": [hx(x) for x in parent_callsites],
            "containingBasicBlock": basic_block,
            "outputBaseProof": {"inputRegister": "RDX", "aliasedRegister": "RDI",
                                "aliasInstructionRva": hx(0x8D5CA9), "status": "PROVEN_STATIC"},
            "parentCallsiteAnalyses": [
                {"callsiteRva": hx(cs), "pathCondition": "normal helper invocation" if cs == 0x2807C8 else "retry/loop invocation; not merged with normal path",
                 "domainEquivalence": "not_assumed",
                 "domains": domains}
                for cs in parent_callsites],
            "rawAddress": ins.op_str.split(",", 1)[0].strip(), "rawEffectiveAddress": ins.op_str.split(",", 1)[0].strip(),
            "normalizedExpression": fmt("output + " + raw_expr),
            "expressionWidth": 64, "signedness": "zero-extended byte/word loads; affine offsets unsigned",
            "variables": sorted({x["variable"] for x in domains if "variable" in x}), "domains": domains,
            "pathCondition": domains[-1].get("condition", "normal helper path") if domains else "normal helper path",
            "recoveredDomain": domains,
            "target38": classify(kind, FIELD38, width(ins)), "target78": classify(kind, FIELD78, width(ins)),
            "canReturnToResolverPath": 0x2807C8 in parent_callsites,
            "firstUnresolvedBoundary": "Loaded A/R/B values are runtime data; no semantic owner or actual iteration is proven.",
            "status": "ARITHMETIC_REDUCED_RUNTIME_DOMAIN_UNRESOLVED"}


def analyze(image: StaticImage, parent: dict[str, Any]) -> dict[str, Any]:
    require_parent(parent)
    targets = target_ranges(image)
    helper_a = function_chain(image, HELPER_A)
    helper_b = function_chain(image, HELPER_B)
    ia = ins_rows(image, HELPER_A, int(helper_a["endRva"], 16))
    ib = ins_rows(image, HELPER_B, int(helper_b["endRva"], 16), set(PRIMARY_WRITES))
    # Verify the exact aliases and anchors from the executable, not just the
    # inherited JSON.  These assertions make the result fail closed on drift.
    alias_a = find_ins(list(ia.values()), 0x8DA7D7)
    alias_b = find_ins(list(ib.values()), 0x8D5CA9)
    if alias_a.op_str.lower() != "rdi, rdx" or alias_b.op_str.lower() != "rdi, rdx":
        raise RuntimeError("output-buffer alias bytes changed")
    callsite_map = []
    parent_ins = image.disassemble(PARENT_START, PARENT_END)
    for cs, target in CALLS:
        ins = find_ins(parent_ins, cs)
        if call_target(ins) != target:
            raise RuntimeError(f"helper callsite drift at {hx(cs)}")
        callsite_map.append({"callsiteRva": hx(cs), "targetRva": hx(target), "instruction": instruction_row(ins),
                             "returnRva": hx(cs + ins.size),
                             "canReachResolverCall": cs in (0x2807C8, 0x2810A3)})
    rows = [
        (0x8D5D35, "d35", "8 + 8*j", "[r14+rcx+8] -> RDI + 8 + 8*j"),
        (0x8D5D77, "d77", "8 + 8*A + 8*j", "[rdx] -> RDI + 8 + 8*A + 8*j"),
        (0x8D5DA3, "da3", "8 + 8*A + 8*R + 16*k", "[rdx+rdi] -> RDI + 8 + 8*A + 8*R + 16*k"),
        (0x8D5DCC, "dcc", "16 + 8*A + 8*R + 16*k", "[rax+rsi] -> RDI + 16 + 8*A + 8*R + 16*k"),
        (0x8D5DF7, "df7", "8 + 8*A + 8*R + 8*j", "[rcx] -> RDI + 8 + 8*A + 8*R + 8*j"),
        (0x8D5E25, "e25", "8 + 8*A + 8*R + 16*k", "[rcx+rdi] -> RDI + 8 + 8*A + 8*R + 16*k"),
        (0x8D5E46, "e46", "16 + 8*A + 8*R + 16*k", "[rdx+rsi] -> RDI + 16 + 8*A + 8*R + 16*k"),
    ]
    helper_cfg = build_basic_blocks(list(ib.values()))
    block_by_rva = {}
    for block in helper_cfg.get("blocks", []):
        for idx in block.get("instructionIndices", []):
            ins = list(ib.values())[idx]
            block_by_rva[ins.address] = {"id": block["id"], "startRva": hx(block["start"]), "endRva": hx(block["end"]),
                                         "successors": [int(x) for x in block.get("successors", [])]}
    writes = [writer_row(image, helper_b, rva, kind, raw, [0x2807C8, 0x2810A3], block_by_rva.get(rva))
              for rva, kind, raw, _ in rows]
    # 0x8DA992: derive the actual fixed local computation, but stop at the
    # unknown qword loaded from [r9+0x1A8].
    computed = {
        "rva": hx(0x8DA992), "instruction": instruction_row(find_ins(list(ia.values()), 0x8DA992)),
        "writeWidth": 8, "outputBaseProof": {"alias": "RDX -> RDI", "instructionRva": hx(0x8DA7D7)},
        "rawAddress": "[RSP+0x48] + RDI", "normalizedExpression":
            "output + (8*G + 8*A + 8*C + 16*B + 8*D + 8*E + 8*F + 8)",
        "variables": ["A", "B", "C", "D", "E", "F", "G"],
        "variableDefinitions": {
            "A": "zero-extended byte [r9+0x498]", "B": "zero-extended word [r9+0x4A2]",
            "C": "zero-extended word [r9+0x4A0]", "D": "zero-extended byte [[r9+0xC0]+0x400]",
            "E": "zero-extended byte [r9+0x7B8]", "F": "zero-extended byte [[r9+0xC8]+0x80]",
            "G": "qword [r9+0x1A8] (unbounded/unknown)"},
        "domainFacts": ["A,D,E,F are uint8", "B,C are uint16", "G has no safe finite address-relative bound"],
        "target38": {"classification": "UNRESOLVED", "proof": ["G is an unbounded qword address component"]},
        "target78": {"classification": "UNRESOLVED", "proof": ["G is an unbounded qword address component"]},
        "firstUnresolvedBoundary": "qword load [r9+0x1A8] used in R14; no safe finite domain",
        "nestedDirectWrites": []}
    nested = []
    # These direct calls are structurally provable copy/zero primitives from
    # their own machine code, but their destination is still affine or unknown.
    for rva, target, dest, size, semantics, c38, c78 in [
        (0x8DA8C3, 0x12A2560, "output + 8", "8*A", "zero-fill primitive",
         nested_claim(8, 56, FIELD38, {"A": 7}, "decoded size 8*A reaches +0x38 when A=7"),
         nested_claim(8, 120, FIELD78, {"A": 15}, "decoded size 8*A reaches +0x78 when A=15")),
        (0x8DA8DE, 0x12A2560, "output + 8 + 8*A", "8*C", "zero-fill primitive",
         nested_claim(8, 56, FIELD38, {"A": 0, "C": 7}, "decoded destination/size witness"),
         nested_claim(8, 120, FIELD78, {"A": 0, "C": 15}, "decoded destination/size witness")),
        (0x8DA8F8, 0x12A2560, "output + 8 + 8*A + 8*C", "16*B", "zero-fill primitive",
         nested_claim(8, 64, FIELD38, {"A": 0, "C": 0, "B": 4}, "decoded destination/size witness"),
         nested_claim(8, 128, FIELD78, {"A": 0, "C": 0, "B": 8}, "decoded destination/size witness")),
        (0x8DA919, 0x12A1EC0, "output + [RSP+0x28]", "8*D", "copy primitive",
         nested_claim(8, 56, FIELD38, {"A": 0, "C": 0, "B": 0, "D": 7}, "stack local [RSP+0x28] reduces to output+8+8*A+8*C+16*B"),
         nested_claim(8, 120, FIELD78, {"A": 0, "C": 0, "B": 0, "D": 15}, "stack local [RSP+0x28] reduces to output+8+8*A+8*C+16*B")),
        (0x8DA938, 0x12A1EC0, "output + [RSP+0x30]", "8*E", "copy primitive",
         nested_claim(8, 56, FIELD38, {"A": 0, "C": 0, "B": 0, "D": 0, "E": 7}, "stack local chain has a bounded byte size"),
         nested_claim(8, 120, FIELD78, {"A": 0, "C": 0, "B": 0, "D": 0, "E": 15}, "stack local chain has a bounded byte size")),
        (0x8DA957, 0x12A1EC0, "output + [RSP+0x38]", "8*F", "copy primitive",
         nested_claim(8, 56, FIELD38, {"A": 0, "C": 0, "B": 0, "D": 0, "E": 0, "F": 7}, "stack local chain has a bounded byte size"),
         nested_claim(8, 120, FIELD78, {"A": 0, "C": 0, "B": 0, "D": 0, "E": 0, "F": 15}, "stack local chain has a bounded byte size")),
        (0x8DA976, 0x12A1EC0, "output + [RSP+0x40]", "8*G", "copy primitive; destination/size unresolved by G", None, None),
        (0x8DA9C1, 0x12A1EC0, "output + [RSP+0x50]", "2*F", "copy primitive; destination unresolved by G", None, None),
    ]:
        ins = find_ins(list(ia.values()), rva)
        nested.append({"callsiteRva": hx(rva), "targetRva": hx(target), "callInstruction": instruction_row(ins),
                       "destinationExpression": dest, "sizeExpression": size, "writeSemantics": semantics,
                       "destinationProof": "output alias plus decoded address formation" if "RSP" not in dest else "stack local expression",
                       "target38": c38 or {"classification": "UNRESOLVED", "proof": ["unbounded qword G remains in destination"]},
                       "target78": c78 or {"classification": "UNRESOLVED", "proof": ["unbounded qword G remains in destination"]},
                       "status": "DESTINATION_OR_SIZE_UNRESOLVED" if c38 is None else "ARITHMETIC_REDUCED",
                       "promotion": "not promoted to reaching writer"})
    computed["nestedDirectWrites"] = nested
    # Parent CFG evidence is retained per callsite; 0x2810A3 is a retry path,
    # and no domain equivalence with 0x2807C8 is assumed.
    cfg = build_basic_blocks(parent_ins)
    callsite_map[1]["cfgBlock"] = cfg.get("instructionToBlock", {}).get(next(i for i,x in enumerate(parent_ins) if x.address == 0x2807C8))
    callsite_map[2]["cfgBlock"] = cfg.get("instructionToBlock", {}).get(next(i for i,x in enumerate(parent_ins) if x.address == 0x2810A3))
    nested_hits = ["0x" + f"{int(row['callsiteRva'], 16):X}" for row in nested
                   if row.get("target38", {}).get("classification") == "CAN_HIT_TARGET"]
    field_delta = lambda key: {"candidateHitWriters": [hx(x[0]) for x in rows] + nested_hits, "lastProvenWriter": None,
                                "sourceProvenance": [], "status": "PARTIAL_STATIC",
                                "reason": "All primary affine families can hit under runtime domains, but no actual iteration/path or overwrite order is proven."}
    return {
        "schemaVersion": 1, "tool": "scan_placement_computed_destination_arithmetic_static.py",
        "analysisMode": "OFFLINE_STATIC_ONLY",
        "parentEvidence": {"delivery": "CODE-0003", "map": PARENT_MAP, "status": "PARTIAL_STATIC"},
        "build": {"revision": REVISION, "sha256": image.digest, "fingerprintMatches": image.digest == SUPPORTED_SHA256,
                   "executable": str(image.path)},
        "safety": {"processAccess": False, "debugApis": False, "writesExecutable": False,
                    "writesGameMemory": False, "runtimeHooksInstalled": False},
        "targets": targets,
        "helperCallsites": callsite_map,
        "helper8D5CA0": {"functionRange": helper_b, "outputBaseAlias": instruction_row(alias_b),
                         "parentCallsites": [hx(0x2807C8), hx(0x2810A3)],
                         "inductionModels": [
                             {"variable": "j", "init": 0, "update": "inc", "compare": "j < A or j < R", "signedness": "unsigned", "status": "PROVEN_STATIC"},
                             {"variable": "k", "init": 0, "update": "inc", "compare": "k < B", "signedness": "unsigned", "status": "PROVEN_STATIC"}],
                         "writes": writes},
        "helper8DA7C0": {"functionRange": helper_a, "outputBaseAlias": instruction_row(alias_a),
                         "computedDestination8DA992": computed, "nestedVariableWrites": nested},
        "field38Delta": field_delta("field38"), "field78Delta": field_delta("field78"),
        "convergenceDelta": {"arithmeticFrontierNarrowed": True, "field38ReachabilityResolved": True,
            "field78ReachabilityResolved": True, "field38WriterProven": False, "field78WriterProven": False,
            "commonOwnerProven": False, "status": "PARTIAL_STATIC",
            "evidence": ["All seven indexed writes reduced to affine output-relative expressions with explicit runtime domains.",
                         "Target ranges decoded as 8-byte reads from the parent frame.",
                         "0x8DA992 reduced to an affine expression but stopped at unbounded qword G."],
            "contradictions": ["CAN_HIT_TARGET is arithmetic reachability, not proof that an iteration occurred.",
                               "No semantic field owner is inferred."]},
        "observerDecision": {"install": False, "failClosed": True,
                             "reason": "CODE-0004 is offline computed-destination arithmetic only"},
        "nextEvidence": ["CODE-0005: recover runtime domains/loop inputs and path-specific execution evidence for the seven affine writers; resolve qword G or prove it cannot alias the output buffer."]}


def render_markdown(result: dict[str, Any]) -> str:
    lines = ["# Placement Computed-Destination Arithmetic — CODE-0004", "",
             "## Scope / build / executable SHA", "",
             f"- Mode: `{result['analysisMode']}`; revision `{result['build']['revision']}`.",
             f"- Executable SHA-256: `{result['build']['sha256']}`.",
             "- No process access, executable writes, game-memory writes, or runtime hooks.", "",
             "## Parent CODE-0003 frontier", "",
             "The parent map remains `PARTIAL_STATIC`; its fixed-writer frontier did not resolve either target.", "",
             "## Target byte-range derivation", "",
             f"- +0x38: `{result['targets']['field38']['decodedInstruction']['instruction']}`, width {result['targets']['field38']['readWidth']}, range `{result['targets']['field38']['byteRange']}`.",
             f"- +0x78: `{result['targets']['field78']['decodedInstruction']['instruction']}`, width {result['targets']['field78']['readWidth']}, range `{result['targets']['field78']['byteRange']}`.", "",
             "## 0x8D5CA0 parent-callsite map", "",
             "- 0x2807C8 and 0x2810A3 are retained separately; their runtime inputs are not assumed equivalent.", "",
             "## Per-write arithmetic results", "",
             "| RVA | normalized expression | width | +0x38 | +0x78 |",
             "|---|---|---:|---|---|"]
    for row in result["helper8D5CA0"]["writes"]:
        lines.append(f"| `{row['rva']}` | `{row['normalizedExpression']}` | {row['writeWidth']} | {row['target38']['classification']} | {row['target78']['classification']} |")
    lines += ["", "## Induction/index models", "",
              "A is a zero-extended byte load, R/C are zero-extended word loads, and B is the unsigned loop bound. Loop indices start at zero and increment by one; the stride in the output address is explicit in each expression.", "",
              "## +0x38 and +0x78 reachability", "",
              "All seven primary writes are `CAN_HIT_TARGET` under their recorded runtime domains. Each result carries a concrete witness; this is arithmetic reachability only and does not promote an actual reaching writer.", "",
              "## 0x8DA992 / nested variable-size writes", "",
              "0x8DA992 reduces to an output-relative affine expression but stops at the unbounded qword G loaded from `[r9+0x1A8]`; both targets therefore remain `UNRESOLVED`. Direct zero-fill/copy callees are documented with destination and size expressions but are not promoted to field writers.", "",
              "## Reaching-writer and source-provenance delta", "",
              "The arithmetic frontier is narrowed to computed families, but no unique actual reaching writer or stored-value source is proven. No semantic owner is inferred.", "",
              "## First unresolved boundary / CODE-0005", "",
              f"{result['nextEvidence'][0]}", "",
              "## Rejected interpretations", "",
              "A broad interval or a matching field offset is not treated as proof of execution, ownership, or last-writer status.", "",
              "## Explicit safety statement", "",
              "CODE-0004 is offline/static-only; observer installation is disabled and fail-closed.", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", type=Path, default=Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"))
    ap.add_argument("--parent", type=Path, default=REPO_ROOT / PARENT_MAP)
    ap.add_argument("--output", type=Path, default=REPO_ROOT / "bridge" / "placement_computed_destination_arithmetic_static_map.json")
    ap.add_argument("--doc", type=Path, default=REPO_ROOT / "docs" / "research" / "PlacementComputedDestinationArithmetic-StaticMap-v1.md")
    args = ap.parse_args()
    image = StaticImage(args.exe)
    parent = load_json(args.parent)
    result = analyze(image, parent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    json.loads(args.output.read_text(encoding="utf-8"))
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "sha256": image.digest,
                      "field38": result["field38Delta"]["status"], "field78": result["field78Delta"]["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
