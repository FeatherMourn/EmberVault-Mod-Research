#!/usr/bin/env python3
"""Deterministic, build-locked static map of the inventory transfer path.

This tool reads enshrouded.exe only.  Searches are restricted to PE exception
functions and the explicit RVAs connected to the validated inventory primitive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import capstone
import pefile
from capstone.x86 import X86_OP_IMM

EXPECTED_SHA256 = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
ACTION_CONSUMER = (0x371810, 0x37229F)
MOVE_HANDLER = (0x385D80, 0x386166)
SPECIAL_HANDLER = (0x386180, 0x3863B0)
TRANSFER_PRIMITIVE = (0x3883C0, 0x3885BC)
VALIDATED_CALLS = (0x3860A7, 0x38613A, 0x386365)


def hx(value: int) -> str:
    return f"0x{value:X}"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


class Image:
    def __init__(self, path: Path):
        self.path = path
        self.data = path.read_bytes()
        actual = sha256(self.data)
        if actual != EXPECTED_SHA256:
            raise SystemExit(f"BUILD_MISMATCH expected={EXPECTED_SHA256} actual={actual}")
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = [
            (s.Name.rstrip(b"\0").decode(), s.VirtualAddress, s.PointerToRawData,
             s.SizeOfRawData, s.Misc_VirtualSize)
            for s in self.pe.sections
        ]
        self.functions = self._functions()
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        self.md.detail = True

    def offset(self, rva: int) -> int:
        for _, va, raw, raw_size, virtual_size in self.sections:
            if va <= rva < va + max(raw_size, virtual_size):
                return raw + rva - va
        raise ValueError(f"RVA outside image: {hx(rva)}")

    def _functions(self) -> list[tuple[int, int, int]]:
        pdata = next(s for s in self.sections if s[0] == ".pdata")
        rows = []
        for pos in range(pdata[2], pdata[2] + pdata[3] - 11, 12):
            begin, end, unwind = struct.unpack_from("<III", self.data, pos)
            if begin and begin < end:
                rows.append((begin, end, unwind))
        return rows

    def disasm(self, begin: int, end: int):
        start = self.offset(begin)
        return list(self.md.disasm(self.data[start:start + end - begin], self.base + begin))

    def bytes_at(self, rva: int, size: int) -> bytes:
        start = self.offset(rva)
        return self.data[start:start + size]

    def direct_callers(self, targets: tuple[int, ...]) -> dict[int, list[dict]]:
        rows = {target: [] for target in targets}
        for begin, end, _ in self.functions:
            for ins in self.disasm(begin, end):
                if (ins.mnemonic == "call" and ins.operands and
                        ins.operands[0].type == X86_OP_IMM):
                    target = ins.operands[0].imm - self.base
                    if target in rows:
                        rows[target].append({"callRva": hx(ins.address - self.base),
                                             "functionBeginRva": hx(begin),
                                             "functionEndRva": hx(end)})
        return rows


def require(image: Image, rva: int, expected_hex: str, label: str) -> dict:
    expected = bytes.fromhex(expected_hex)
    actual = image.bytes_at(rva, len(expected))
    if actual != expected:
        raise SystemExit(f"EVIDENCE_MISMATCH {label} at {hx(rva)}")
    return {"rva": hx(rva), "bytes": actual.hex(" ").upper(), "label": label}


def build_report(image: Image) -> dict:
    # Independent byte checks keep prose conclusions coupled to this build.
    evidence = [
        require(image, 0x37182C, "48 8B 72 10", "envelope pointer loaded from context+0x10"),
        require(image, 0x371842, "8B 46 08", "version dword loaded from envelope+0x08"),
        require(image, 0x371869, "89 41 20", "version copied to candidate consumed record+0x20"),
        require(image, 0x371FEb, "80 7E 24 03", "action type compared with 3"),
        require(image, 0x371FFD, "0F B7 46 26", "uint16 action amount load"),
        require(image, 0x37200D, "E8 6E 41 01 00", "type-3 path call to special handler"),
        require(image, 0x372014, "48 8D 8D 68 72 00 00", "general path result setup"),
        require(image, 0x372020, "E8 5B 3D 01 00", "general path call to move handler"),
        require(image, 0xCB4B5C, "48 8D 4A 38", "resolver selects owner+0x38 table"),
    ]

    fields = [
        {"offset": "+0x00", "access": "dword [RSI+0x08]", "rva": "0x371842",
         "flow": "copied to dword [qword(context+0x38)+0x20]", "status": "PROVEN"},
        {"offset": "+0x04", "access": "dword [RSI+0x0C]", "rvas": ["0x3719EE", "0x371CC1"],
         "flow": "source-side identifier-like input and validity branches", "status": "PROVEN"},
        {"offset": "+0x08", "access": "dword [RSI+0x10]", "rvas": ["0x3719E9", "0x371D47"],
         "flow": "target-side identifier-like input and validity branches", "status": "PROVEN"},
        {"offset": "+0x0C", "access": "qword [RSI+0x14]", "rvas": ["0x371FF3", "0x37201B"],
         "flow": "passed as source packed slot to both connected handlers", "status": "PROVEN"},
        {"offset": "+0x14", "access": "qword [RSI+0x1C]", "rvas": ["0x371FF7", "0x372014"],
         "flow": "passed as destination packed slot to both connected handlers", "status": "PROVEN"},
        {"offset": "+0x1C", "access": "byte [RSI+0x24]", "rvas": ["0x371BBD", "0x371FEb"],
         "flow": "multiway behavior selection; value 3 selects special handler", "status": "PROVEN"},
        {"offset": "+0x1D", "access": "byte [RSI+0x25]", "rvas": ["0x37186C", "0x3719DB"],
         "flow": "bits gate early and later operation branches", "status": "PROVEN"},
        {"offset": "+0x1E", "access": "word [RSI+0x26]", "rvas": ["0x371F52", "0x371FFD"],
         "flow": "passed to special/general inventory operation paths and reaches proven amount", "status": "PROVEN"},
    ]

    functions = [
        {"name": "candidate_inventory_transfer_consumer", "beginRva": hx(ACTION_CONSUMER[0]),
         "endRva": hx(ACTION_CONSUMER[1]), "unwindFragments": [
             ["0x371810", "0x371925"], ["0x371925", "0x3719AD"], ["0x3719AD", "0x37229F"]],
         "arguments": {"RCX": "service/world-like context (neutral)",
                       "RDX": "dispatch context; +0x10 yields envelope, +0x38 yields consumed-record pointer"},
         "importantBranches": ["flags bits gate distinct paths", "type == 3 selects 0x386180",
                                "other accepted types select 0x385D80"],
         "directCallers": [], "directCallerStatus": "UNSOLVED_INDIRECT_OR_TABLE_DISPATCH"},
        {"name": "candidate_general_inventory_move_handler", "beginRva": hx(MOVE_HANDLER[0]),
         "endRva": hx(MOVE_HANDLER[1]), "unwindFragments": [
             ["0x385D80", "0x385E15"], ["0x385E15", "0x38602A"],
             ["0x386044", "0x386166"]], "validatedPrimitiveCallRvas": ["0x3860A7", "0x38613A"],
         "arguments": {"RCX": "result", "RDX": "inventory-access context",
                       "R8": "destination packed slot", "R9": "source packed slot",
                       "stack+0x20": "operation/type-dependent raw value"},
         "locals": {"RBP-0x30": "resolved source ItemStack candidate",
                    "RBP-0x40": "resolved destination ItemStack candidate",
                    "RBP-0x48": "primitive result"},
         "derivation": {"source": "R9 -> 0x386C00 -> [RBP-0x30]",
                        "destination": "R8 -> 0x386C00 -> [RBP-0x40]",
                        "amounts": "R12D/R13D/EBX selected by branches; EBX originates from action amount on the connected general route"}},
        {"name": "candidate_type3_inventory_handler", "beginRva": hx(SPECIAL_HANDLER[0]),
         "endRva": hx(SPECIAL_HANDLER[1]), "unwindFragments": [
             ["0x386180", "0x38620C"], ["0x38620C", "0x386264"], ["0x386264", "0x3863B0"]],
         "validatedPrimitiveCallRvas": ["0x386365"],
         "arguments": {"RCX": "result", "RDX": "inventory-access context",
                       "R8": "destination packed slot", "R9": "source packed slot",
                       "stack+0x20": "uint16 requested amount on connected type-3 route"},
         "locals": {"RSP+0x38/R15": "resolved source ItemStack candidate",
                    "RSP+0x50/R14": "resolved destination ItemStack candidate",
                    "RSP+0x30": "primitive result"},
         "derivation": {"source": "R9 -> 0x386C00 -> R15",
                        "destination": "R8 -> 0x386C00 -> R14",
                        "amount": "min(requested uint16, source/destination-derived limits) -> R13D"}},
        {"name": "proven_destination_itemstack_primitive", "beginRva": hx(TRANSFER_PRIMITIVE[0]),
         "endRva": hx(TRANSFER_PRIMITIVE[1]), "validatedCallRvas": [hx(x) for x in VALIDATED_CALLS],
         "status": "PROVEN_BUILD_1076226",
         "arguments": {"RCX": "result", "RDX": "inventory-access context",
                       "R8": "destination packed slot", "R9": "resolved item record",
                       "stack+0x20": "raw identifier-like value", "stack+0x28": "proven transfer amount"},
         "locals": {"R15": "proven destination ItemStack pointer", "R14": "resolved item record"},
         "branches": {"emptyDestination": "initializes ItemId/count/pide and bookkeeping",
                      "existingStack": "requires matching ItemId and adds bounded amount"},
         "slotDerivation": "0x387830 decodes R8 and returns inventoryBase + slotIndex*0x0C"},
        {"name": "item_id_record_resolver", "beginRva": "0xCB4B50", "endRva": "0xCB4B7E",
         "flow": "nonzero dword key -> owner+0x38 container lookup -> dereferenced record pointer"},
    ]

    callers = image.direct_callers((0x385D80, 0x386180, 0x3883C0))
    return {
        "schemaVersion": 1,
        "tool": "scan_inventory_transfer_static_map.py",
        "safety": {"mode": "OFFLINE_ONLY", "inputs": [str(image.path)],
                   "processAccess": False, "writesExecutable": False, "searchBounded": True},
        "build": {"revision": 1076226, "sha256": sha256(image.data),
                  "imageBase": hx(image.base)},
        "strongestConclusion": {
            "status": "PROVEN",
            "text": "RSI+0x08 in 0x371810 is an action-shaped payload matching all InventoryTransferAction fields; its slots and uint16 amount flow into the handlers that reach the validated ItemStack primitive."
        },
        "actionCandidate": {"payloadBase": "RSI+0x08", "size": "0x20", "fields": fields,
                            "identity": "InventoryTransferAction", "identityStatus": "PROVEN"},
        "versionConsumption": {
            "status": "INFERRED",
            "evidence": "payload +0x00 is copied at entry to [qword(context+0x38)+0x20]",
            "limitation": "static code proves a version copy to a consumed-record-like location, but not the concrete enclosing ClientPlayerInput/ServerConsumedPlayerInput runtime types"
        },
        "functions": functions,
        "callEdges": [
            {"from": "0x371810", "at": "0x37200D", "to": "0x386180", "condition": "type == 3"},
            {"from": "0x371810", "at": "0x372020", "to": "0x385D80", "condition": "accepted non-3 path"},
            {"from": "0x385D80 logical handler", "at": "0x3860A7", "to": "0x3883C0"},
            {"from": "0x385D80 logical handler", "at": "0x38613A", "to": "0x3883C0"},
            {"from": "0x386180 logical handler", "at": "0x386365", "to": "0x3883C0"},
        ],
        "directCallerInventory": {
            "0x385D80": callers[0x385D80],
            "0x386180": callers[0x386180],
            "0x3883C0": callers[0x3883C0],
        },
        "callerRoleDifferentiation": {
            "type3": "0x386180 is selected by action type byte == 3 and contains the validated split-observed 0x386365 call",
            "general": "0x385D80 is selected on another accepted type path and contains both empty-move and merge-observed calls",
            "exclusivity": "UNSOLVED; runtime observations do not prove the call sites are exclusive to those user operations"
        },
        "r14Provenance": {
            "status": "INFERRED",
            "chain": ["caller loads ItemId-like dword from resolved source stack",
                      "0xCB4B50 looks up that key in contextOwner+0x38",
                      "the returned pointer becomes target R14",
                      "existing registry-population analysis shows owner+0x38 values are typed-resolved ItemInfo record pointers"],
            "supportedType": "ItemInfo-compatible resolved record pointer",
            "limitation": "the exact runtime owner instance passed by these handlers is not statically tied to a specific 0xCE79C0 population invocation"
        },
        "rejectedCandidates": [
            {"range": "0x8FA60..0x8FB30", "status": "DISPROVEN",
             "reason": "+0x1E is byte-sized and unrelated extra offsets dominate; no flow to the proven primitive"},
            {"range": "0xC9609..0xC96FE", "status": "DISPROVEN",
             "reason": "generic field-address/reflection traversal with no argument flow to inventory mechanics"},
            {"range": "0x389136..0x389222", "status": "DISPROVEN",
             "reason": "stack-deletion logging/error path, not the action consumer"},
            {"range": "metadata clusters at 0x19ECB30 and 0x1A13580", "status": "EXPERIMENTAL",
             "reason": "support reflected identity but still have no direct executable xref or handler pointer"},
        ],
        "checkedInstructionEvidence": evidence,
        "unresolved": [
            "concrete runtime types of the consumer's RCX/RDX context objects",
            "indirect registration/dispatch edge into 0x371810",
            "exact field name and owner type of context+0x38 / pointee+0x20",
            "exclusive semantic names for the three primitive call sites",
            "live validation that v0.18 source/destination slot labels match the action fields",
        ],
        "hookReadiness": "NOT_EVALUATED_OFFLINE_REPORT_ONLY",
    }


def main() -> None:
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=root / "enshrouded.exe")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parents[2] / "bridge" / "inventory_transfer_static_map.json")
    args = parser.parse_args()
    report = build_report(Image(args.exe.resolve()))
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"consumer={ACTION_CONSUMER[0]:#x} action=RSI+0x08 output={args.output.resolve()}")


if __name__ == "__main__":
    main()
