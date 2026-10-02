"""Offline, read-only inventory xref/call-graph research for Enshrouded.

Requires the already-installed ``capstone`` and ``pefile`` modules. This tool
reads the executable file only; it never opens a game process or produces a
hook address. Function ranges come from x64 .pdata runtime-function entries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from bisect import bisect_right
from pathlib import Path

import capstone
import pefile
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

TARGETS = (
    "backpackSplitStack",
    "consumedInventoryTransferAction",
    "[inventory] Deleted %k items from stack of %k.",
)
RELATED_STRINGS = ("backpackDropItemIntoSlot", "doSplitStackWidget", "sortItemCollections", "takeItemStack", "putStack")


def hex_rva(value: int | None) -> str | None:
    return None if value is None else f"0x{value:X}"


class PeImage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = path.read_bytes()
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.image_base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for section in self.pe.sections:
            self.sections.append(
                {
                    "name": section.Name.rstrip(b"\0").decode("ascii", "replace"),
                    "rva": section.VirtualAddress,
                    "raw_offset": section.PointerToRawData,
                    "raw_size": section.SizeOfRawData,
                    "virtual_size": section.Misc_VirtualSize,
                    "characteristics": section.Characteristics,
                }
            )

    def section_for_rva(self, rva: int) -> dict | None:
        for section in self.sections:
            end = section["rva"] + max(section["raw_size"], section["virtual_size"])
            if section["rva"] <= rva < end:
                return section
        return None

    def is_executable_rva(self, rva: int) -> bool:
        section = self.section_for_rva(rva)
        return bool(section and section["characteristics"] & 0x20000000)

    def rva_to_offset(self, rva: int) -> int | None:
        section = self.section_for_rva(rva)
        if not section:
            return None
        delta = rva - section["rva"]
        if delta >= section["raw_size"]:
            return None
        return section["raw_offset"] + delta

    def offset_to_rva(self, offset: int) -> int | None:
        for section in self.sections:
            if section["raw_offset"] <= offset < section["raw_offset"] + section["raw_size"]:
                return section["rva"] + offset - section["raw_offset"]
        return None

    def find_ascii(self, text: str) -> list[int]:
        needle = text.encode("ascii")
        offsets, at = [], 0
        while (found := self.data.find(needle, at)) >= 0:
            offsets.append(found)
            at = found + 1
        return offsets

    def runtime_functions(self) -> list[tuple[int, int]]:
        section = next((s for s in self.sections if s["name"] == ".pdata"), None)
        if not section:
            return []
        result = []
        raw_start, raw_end = section["raw_offset"], section["raw_offset"] + section["raw_size"]
        for at in range(raw_start, raw_end - 11, 12):
            begin, end, _ = struct.unpack_from("<III", self.data, at)
            if begin and begin < end and self.is_executable_rva(begin) and self.is_executable_rva(end - 1):
                result.append((begin, end))
        return sorted(set(result))


def function_containing(ranges: list[tuple[int, int]], starts: list[int], rva: int) -> dict:
    index = bisect_right(starts, rva) - 1
    if index >= 0:
        begin, end = ranges[index]
        if begin <= rva < end:
            return {"startRva": hex_rva(begin), "endRva": hex_rva(end), "confidence": "PROVEN_BOUNDARY", "reason": ".pdata runtime-function entry"}
    return {"startRva": None, "endRva": None, "confidence": "UNKNOWN", "reason": "outside parsed .pdata function range"}


def decoded_reference_at(md: capstone.Cs, image: PeImage, raw_offset: int) -> dict | None:
    """Decode one potential reference; reject it unless Capstone confirms RIP addressing."""
    rva = image.offset_to_rva(raw_offset)
    if rva is None:
        return None
    decoded = next(md.disasm(image.data[raw_offset:raw_offset + 15], image.image_base + rva, count=1), None)
    if not decoded or decoded.id == 0:
        return None
    for operand in decoded.operands:
        if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
            target = decoded.address + decoded.size + operand.mem.disp - image.image_base
            return {"instructionRva": rva, "instructionBytes": bytes(decoded.bytes).hex().upper(), "decodedInstruction": f"{decoded.mnemonic} {decoded.op_str}".strip(), "targetRva": target}
    return None


def code_references_to(image: PeImage, wanted_rvas: set[int]) -> dict[int, list[dict]]:
    """Find validated RIP-relative references to a bounded set of data RVAs.

    The byte prefilter only finds possible REX+RIP forms; Capstone performs the
    actual decode and target calculation before a result is emitted.
    """
    text = next(section for section in image.sections if section["name"] == ".text")
    start, end = text["raw_offset"], text["raw_offset"] + text["raw_size"]
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    results = {rva: [] for rva in wanted_rvas}
    for at in range(start, end - 7):
        if not (0x40 <= image.data[at] <= 0x4F and image.data[at + 1] in (0x8B, 0x8D)):
            continue
        if image.data[at + 2] & 0xC7 != 0x05:
            continue
        reference = decoded_reference_at(md, image, at)
        if reference and reference["targetRva"] in results:
            results[reference["targetRva"]].append(reference)
    return results


def direct_callers_to(image: PeImage, callee_rva: int) -> list[dict]:
    text = next(section for section in image.sections if section["name"] == ".text")
    start, end = text["raw_offset"], text["raw_offset"] + text["raw_size"]
    hits = []
    for at in range(start, end - 5):
        if image.data[at] != 0xE8:
            continue
        source = image.offset_to_rva(at)
        target = source + 5 + struct.unpack_from("<i", image.data, at + 1)[0]
        if target == callee_rva:
            hits.append({"callSiteRva": hex_rva(source), "calleeRva": hex_rva(target), "confidence": "validated_rel32_encoding"})
    return hits


def direct_callees_in_range(image: PeImage, begin: int, end: int) -> list[dict]:
    results = []
    for rva in range(begin, end - 5):
        offset = image.rva_to_offset(rva)
        if offset is None or image.data[offset] != 0xE8:
            continue
        target = rva + 5 + struct.unpack_from("<i", image.data, offset + 1)[0]
        if image.is_executable_rva(target):
            results.append({"callSiteRva": hex_rva(rva), "calleeRva": hex_rva(target), "confidence": "validated_rel32_encoding"})
    return results


def data_references(image: PeImage, target_rva: int) -> list[dict]:
    """Locate valid stored RVA/VA/relative values that resolve to target_rva."""
    hits = []
    target_va = image.image_base + target_rva
    for section in image.sections:
        if section["name"] == ".text":
            continue
        start, end = section["raw_offset"], section["raw_offset"] + section["raw_size"]
        for at in range(start, end - 3, 4):
            value = struct.unpack_from("<I", image.data, at)[0]
            forms = []
            if value == target_rva:
                forms.append("stored_rva32")
            if image.offset_to_rva(at) is not None and image.offset_to_rva(at) + 4 + struct.unpack_from("<i", image.data, at)[0] == target_rva:
                forms.append("relative_offset32")
            if forms:
                hits.append({"objectRva": image.offset_to_rva(at), "section": section["name"], "forms": forms})
        for at in range(start, end - 7, 8):
            if struct.unpack_from("<Q", image.data, at)[0] == target_va:
                hits.append({"objectRva": image.offset_to_rva(at), "section": section["name"], "forms": ["stored_va64"]})
    unique = {(entry["objectRva"], tuple(entry["forms"])): entry for entry in hits}
    return list(unique.values())


def data_object_context(image: PeImage, object_rva: int) -> list[dict]:
    """Describe nearby aligned qwords without assigning table-field semantics."""
    object_offset = image.rva_to_offset(object_rva)
    if object_offset is None:
        return []
    row = []
    for delta in range(-16, 25, 8):
        offset = object_offset + delta
        if offset < 0 or offset + 8 > len(image.data):
            continue
        value = struct.unpack_from("<Q", image.data, offset)[0]
        target_rva = value - image.image_base if image.image_base <= value < image.image_base + image.pe.OPTIONAL_HEADER.SizeOfImage else None
        target_section = image.section_for_rva(target_rva) if target_rva is not None else None
        row.append({"relativeOffset": f"{delta:+#x}", "rawQword": hex_rva(value), "resolvedRva": hex_rva(target_rva), "resolvedSection": target_section["name"] if target_section else None, "pointsIntoExecutableSection": bool(target_rva is not None and image.is_executable_rva(target_rva))})
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=Path(__file__).resolve().parents[4] / "enshrouded.exe")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[2] / "bridge" / "item_observer_callgraph_scan.json")
    args = parser.parse_args()
    image = PeImage(args.exe.resolve())
    ranges = image.runtime_functions()
    starts = [start for start, _ in ranges]
    targets, candidates, graph = [], [], []
    target_locations = {image.offset_to_rva(offset) for text in TARGETS for offset in image.find_ascii(text)}
    data_objects_by_target = {rva: data_references(image, rva) for rva in target_locations}
    direct_by_target = code_references_to(image, target_locations)
    indirect_object_rvas = {obj["objectRva"] for objects in data_objects_by_target.values() for obj in objects}
    indirect_code_by_object = code_references_to(image, indirect_object_rvas)
    for text in TARGETS:
        occurrences = image.find_ascii(text)
        target_rows = []
        for offset in occurrences:
            rva = image.offset_to_rva(offset)
            direct = direct_by_target.get(rva, [])
            indirect = data_objects_by_target[rva]
            for obj in indirect:
                obj["contextQwords"] = data_object_context(image, obj["objectRva"])
            indirect_code = []
            for obj in indirect:
                for xref in indirect_code_by_object.get(obj["objectRva"], []):
                    row = dict(xref)
                    row["dataObjectRva"] = obj["objectRva"]
                    indirect_code.append(row)
            target_rows.append({"fileOffset": hex_rva(offset), "rva": hex_rva(rva), "section": image.section_for_rva(rva)["name"], "directCodeReferences": direct, "indirectDataObjects": indirect, "codeReferencesToIndirectObjects": indirect_code})
            for xref in direct + indirect_code:
                fn = function_containing(ranges, starts, xref["instructionRva"])
                if not fn["startRva"]:
                    continue
                score = 20 if "dataObjectRva" in xref else 10
                candidates.append({"function": fn, "score": score, "confidence": "CANDIDATE", "evidence": ["references target data indirectly" if "dataObjectRva" in xref else "direct string xref"], "notApprovedForHook": True})
        targets.append({"text": text, "occurrences": target_rows})

    # Revisit the known log reference and expose its immediate callers/callee.
    log_rva = 0x389161
    log_fn = function_containing(ranges, starts, log_rva)
    if log_fn["startRva"]:
        start_value = int(log_fn["startRva"], 16)
        end_value = int(log_fn["endRva"], 16)
        local_calls = direct_callees_in_range(image, start_value, end_value)
        callers = direct_callers_to(image, start_value)
        graph.append({"subject": "stack_deletion_logging_reference", "referenceRva": hex_rva(log_rva), "function": log_fn, "directCallers": callers[:32], "directCallees": local_calls[:32], "conclusion": "logging-context-only_not_hook_candidate"})

    report = {
        "schemaVersion": 1,
        "tool": {"name": "scan_item_observer_callgraph.py", "capstone": capstone.__version__, "pefile": getattr(pefile, "__version__", "unknown")},
        "executable": str(image.path),
        "executableSha256": hashlib.sha256(image.data).hexdigest().upper(),
        "functionBoundarySource": ".pdata x64 runtime-function entries",
        "targets": targets,
        "candidateFunctions": candidates,
        "callGraph": graph,
        "relatedStrings": [
            {"text": text, "occurrenceRvas": [hex_rva(image.offset_to_rva(offset)) for offset in image.find_ascii(text)]}
            for text in RELATED_STRINGS
        ],
        "researchConclusions": ["No candidate in this report is approved for an observe-only hook.", "The split-stack and transfer-action target strings require an indirect metadata/registration tracing method if no data object is found."],
        "safety": "Offline file analysis only; no process, injection, hook, or mutation operation was performed.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for target in targets:
        occurrences = target["occurrences"]
        direct = sum(len(row["directCodeReferences"]) for row in occurrences)
        indirect = sum(len(row["indirectDataObjects"]) for row in occurrences)
        print(f"{target['text']}: direct={direct} indirect-data={indirect}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
