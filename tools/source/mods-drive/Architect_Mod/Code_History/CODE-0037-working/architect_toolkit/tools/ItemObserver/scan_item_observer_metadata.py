"""Offline metadata/hash inspection for the Item Observer research targets.

Consumes the call-graph scan and emits raw candidate-entry fields. It never
assigns handler semantics and never accesses a live process.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path


def load_callgraph_module():
    path = Path(__file__).with_name("scan_item_observer_callgraph.py")
    spec = importlib.util.spec_from_file_location("item_callgraph", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def fnv1a32(text: str) -> int:
    value = 0x811C9DC5
    for byte in text.encode("utf-8"):
        value = ((value ^ byte) * 0x01000193) & 0xFFFFFFFF
    return value


def ascii_at(image, rva: int | None) -> str | None:
    if rva is None:
        return None
    offset = image.rva_to_offset(rva)
    if offset is None:
        return None
    end = image.data.find(b"\0", offset, min(len(image.data), offset + 160))
    if end < offset:
        return None
    raw = image.data[offset:end]
    if len(raw) < 2 or any(byte < 32 or byte > 126 for byte in raw):
        return None
    return raw.decode("ascii")


def field_rows(image, entry_rva: int) -> list[dict]:
    offset = image.rva_to_offset(entry_rva)
    if offset is None:
        return []
    rows = []
    for relative in range(0, 40, 8):
        if offset + relative + 8 > len(image.data):
            continue
        value = struct.unpack_from("<Q", image.data, offset + relative)[0]
        resolved = value - image.image_base if image.image_base <= value < image.image_base + image.pe.OPTIONAL_HEADER.SizeOfImage else None
        section = image.section_for_rva(resolved) if resolved is not None else None
        rows.append({"offset": f"0x{relative:X}", "rawQword": f"0x{value:X}", "resolvedRva": f"0x{resolved:X}" if resolved is not None else None, "resolvedSection": section["name"] if section else None, "candidateAscii": ascii_at(image, resolved), "candidateCodePointer": bool(resolved is not None and image.is_executable_rva(resolved))})
    return rows


def binary_matches_u32(data: bytes, value: int, maximum: int = 64) -> list[int]:
    needle = struct.pack("<I", value)
    matches, at = [], 0
    while len(matches) < maximum and (found := data.find(needle, at)) >= 0:
        matches.append(found)
        at = found + 1
    return matches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[2]
    parser.add_argument("--exe", type=Path, default=Path(__file__).resolve().parents[4] / "enshrouded.exe")
    parser.add_argument("--callgraph", type=Path, default=root / "bridge" / "item_observer_callgraph_scan.json")
    parser.add_argument("--output", type=Path, default=root / "bridge" / "item_observer_metadata_scan.json")
    args = parser.parse_args()
    callgraph = json.loads(args.callgraph.read_text(encoding="utf-8"))
    module = load_callgraph_module()
    image = module.PeImage(args.exe.resolve())
    entries, hashes = [], []
    for target in callgraph["targets"][:2]:
        text = target["text"]
        hash_value = fnv1a32(text)
        raw_matches = binary_matches_u32(image.data, hash_value)
        hashes.append({"algorithm": "FNV-1a-32", "input": text, "value": f"0x{hash_value:08X}", "fileOffsetMatches": [f"0x{value:X}" for value in raw_matches], "conclusion": "candidate_only_numeric_match_does_not_establish_action_hash"})
        for occurrence in target["occurrences"]:
            for obj in occurrence["indirectDataObjects"]:
                entry_rva = obj["objectRva"]
                fields = field_rows(image, entry_rva)
                entries.append({"target": text, "candidateEntryRva": f"0x{entry_rva:X}", "sourceForms": obj["forms"], "fields": fields, "candidateCodePointerCount": sum(field["candidateCodePointer"] for field in fields), "conclusion": "candidate_metadata_entry_only"})
    report = {"schemaVersion": 1, "tool": "scan_item_observer_metadata.py", "executableSha256": hashlib.sha256(image.data).hexdigest().upper(), "inputCallgraphSha256": hashlib.sha256(args.callgraph.read_bytes()).hexdigest().upper(), "candidateEntries": entries, "candidateHashes": hashes, "candidateStructures": {"observedStride": None, "conclusion": "No repeated entry stride or code-pointer field was established."}, "hookReadiness": "NOT_READY", "safety": "Offline file analysis only; no process, hook, injection, or mutation was used."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"candidate entries={len(entries)}; candidate code pointers={sum(entry['candidateCodePointerCount'] for entry in entries)}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
