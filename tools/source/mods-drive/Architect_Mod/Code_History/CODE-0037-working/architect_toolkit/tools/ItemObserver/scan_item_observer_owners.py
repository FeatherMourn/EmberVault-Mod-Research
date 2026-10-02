"""Offline owner/relocation analysis for Item Observer metadata candidates."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

import pefile


def load_module(name: str):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def hexv(value):
    return None if value is None else f"0x{value:X}"


def all_reverse_refs(image, target_rva: int) -> list[dict]:
    """Valid stored VA/RVA references only; arbitrary values are excluded."""
    target_va = image.image_base + target_rva
    rows = []
    for section in image.sections:
        if section["name"] == ".text":
            continue
        start, end = section["raw_offset"], section["raw_offset"] + section["raw_size"]
        for offset in range(start, end - 7, 8):
            value = struct.unpack_from("<Q", image.data, offset)[0]
            if value == target_va:
                rows.append({"sourceRva": image.offset_to_rva(offset), "targetRva": target_rva, "sourceSection": section["name"], "targetSection": image.section_for_rva(target_rva)["name"], "referenceType": "absolute_va64", "width": 8, "rawValue": hexv(value), "confidence": "PROVEN"})
        for offset in range(start, end - 3, 4):
            value = struct.unpack_from("<I", image.data, offset)[0]
            source_rva = image.offset_to_rva(offset)
            if value == target_rva:
                rows.append({"sourceRva": source_rva, "targetRva": target_rva, "sourceSection": section["name"], "targetSection": image.section_for_rva(target_rva)["name"], "referenceType": "rva32", "width": 4, "rawValue": hexv(value), "confidence": "PROVEN"})
            elif source_rva + 4 + struct.unpack_from("<i", image.data, offset)[0] == target_rva:
                rows.append({"sourceRva": source_rva, "targetRva": target_rva, "sourceSection": section["name"], "targetSection": image.section_for_rva(target_rva)["name"], "referenceType": "relative_offset32", "width": 4, "rawValue": hexv(value), "confidence": "CANDIDATE"})
    return rows


def relocation_rows(path: Path, image, candidate_rvas: set[int]) -> list[dict]:
    pe = pefile.PE(str(path), fast_load=False)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_BASERELOC"]])
    rows = []
    for block in getattr(pe, "DIRECTORY_ENTRY_BASERELOC", []):
        for entry in block.entries:
            rva = entry.rva
            # A relocation is relevant when it lands on or close to a known
            # candidate entry; owner bounds remain explicitly heuristic.
            owner = next((candidate for candidate in candidate_rvas if candidate - 0x40 <= rva <= candidate + 0x80), None)
            if owner is None:
                continue
            offset = image.rva_to_offset(rva)
            if offset is None:
                continue
            width = 8 if entry.type == pefile.RELOCATION_TYPE["IMAGE_REL_BASED_DIR64"] else 4
            raw = int.from_bytes(image.data[offset:offset + width], "little")
            target = raw - image.image_base if width == 8 and image.image_base <= raw < image.image_base + image.pe.OPTIONAL_HEADER.SizeOfImage else None
            section = image.section_for_rva(rva)
            target_section = image.section_for_rva(target) if target is not None else None
            rows.append({"ownerCandidateRva": hexv(owner), "relocationRva": hexv(rva), "relocationType": entry.type, "containingSection": section["name"] if section else None, "rawFieldValue": hexv(raw), "resolvedTargetRva": hexv(target), "targetSection": target_section["name"] if target_section else None})
    return rows


def owner_window(image, entry_rva: int) -> dict:
    start = entry_rva - 0x40
    fields = []
    for relative in range(-0x40, 0x81, 8):
        rva = entry_rva + relative
        offset = image.rva_to_offset(rva)
        if offset is None or offset + 8 > len(image.data):
            continue
        raw = struct.unpack_from("<Q", image.data, offset)[0]
        target = raw - image.image_base if image.image_base <= raw < image.image_base + image.pe.OPTIONAL_HEADER.SizeOfImage else None
        section = image.section_for_rva(target) if target is not None else None
        fields.append({"relativeOffset": f"{relative:+#x}", "fieldRva": hexv(rva), "rawQword": hexv(raw), "resolvedRva": hexv(target), "resolvedSection": section["name"] if section else None, "candidateCodePointer": bool(target is not None and image.is_executable_rva(target))})
    return {"candidateEntryRva": hexv(entry_rva), "windowStartRva": hexv(start), "boundaryConfidence": "HEURISTIC", "fields": fields}


def qword_target(image, rva: int):
    offset = image.rva_to_offset(rva)
    if offset is None or offset + 8 > len(image.data):
        return None, None
    raw = struct.unpack_from("<Q", image.data, offset)[0]
    target = raw - image.image_base if image.image_base <= raw < image.image_base + image.pe.OPTIONAL_HEADER.SizeOfImage else None
    return raw, target


def ascii_target(image, rva: int | None):
    if rva is None:
        return None
    offset = image.rva_to_offset(rva)
    if offset is None:
        return None
    end = image.data.find(b"\0", offset, min(offset + 128, len(image.data)))
    raw = image.data[offset:end] if end >= 0 else b""
    return raw.decode("ascii") if len(raw) > 1 and all(32 <= byte <= 126 for byte in raw) else None


def repeated_entry_cluster(image, entry_rva: int) -> dict:
    """Compare a bounded 0x30-stride hypothesis; never claim it as proven."""
    rows = []
    for candidate in range(entry_rva - 0x30, entry_rva + 0x61, 0x30):
        raw0, target0 = qword_target(image, candidate)
        raw10, target10 = qword_target(image, candidate + 0x10)
        if raw0 is None:
            continue
        rows.append({"entryRva": hexv(candidate), "field00TargetRva": hexv(target0), "field00Ascii": ascii_target(image, target0), "field10TargetRva": hexv(target10), "field10Section": image.section_for_rva(target10)["name"] if target10 is not None and image.section_for_rva(target10) else None})
    return {"anchorEntryRva": hexv(entry_rva), "candidateStride": "0x30", "confidence": "HEURISTIC", "reason": "relocation-backed pointer fields recur at 0x30 intervals around the target entry", "entries": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument("--exe", type=Path, default=Path(__file__).resolve().parents[4] / "enshrouded.exe")
    parser.add_argument("--metadata", type=Path, default=root / "bridge" / "item_observer_metadata_scan.json")
    parser.add_argument("--output", type=Path, default=root / "bridge" / "item_observer_owner_scan.json")
    args = parser.parse_args()
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    module = load_module("scan_item_observer_callgraph.py")
    image = module.PeImage(args.exe.resolve())
    entries = [int(row["candidateEntryRva"], 16) for row in metadata["candidateEntries"]]
    reverse = {rva: all_reverse_refs(image, rva) for rva in entries}
    relocations = relocation_rows(args.exe.resolve(), image, set(entries))
    code_by_owner = module.code_references_to(image, set(entries))
    owners = [owner_window(image, rva) for rva in entries]
    clusters = [repeated_entry_cluster(image, rva) for rva in entries if rva in (0x1663D60, 0x19CF130, 0x19ECB30, 0x1A13580)]
    pointer_chains = []
    for entry in entries:
        for ref in reverse[entry]:
            pointer_chains.append({"targetEntryRva": hexv(entry), "nodes": [{"rva": hexv(entry), "section": image.section_for_rva(entry)["name"], "relationship": "metadata_entry"}, {"rva": hexv(ref["sourceRva"]), "section": ref["sourceSection"], "relationship": ref["referenceType"]}], "depth": 1})
    report = {"schemaVersion": 1, "tool": "scan_item_observer_owners.py", "executableSha256": hashlib.sha256(image.data).hexdigest().upper(), "metadataInputSha256": hashlib.sha256(args.metadata.read_bytes()).hexdigest().upper(), "metadataEntries": [hexv(rva) for rva in entries], "reverseReferences": [ref for rows in reverse.values() for ref in rows], "relocations": relocations, "ownerCandidates": owners, "pointerChains": pointer_chains, "codeReferences": {hexv(rva): code_by_owner.get(rva, []) for rva in entries}, "structuralClusters": clusters, "candidateFunctions": [], "conclusions": ["Relocation-backed .rdata pointer fields reveal a repeated 0x30-stride candidate layout around several target entries; its owner semantics remain unknown.", "No candidate entry has a decoded .text reference or validated executable pointer.", "No candidate is approved for observe-only validation."], "hookReadiness": "NOT_READY", "safety": "Offline PE-file analysis only; no game process, hook, injection, or mutation was used."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"entries={len(entries)} reverse-references={len(report['reverseReferences'])} relocations={len(relocations)} code-xrefs={sum(len(x) for x in code_by_owner.values())}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
