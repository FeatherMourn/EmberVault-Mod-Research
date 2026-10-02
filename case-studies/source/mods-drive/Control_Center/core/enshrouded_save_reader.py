"""Read-only, bounds-checked helpers for Enshrouded character saves.

This module intentionally does not write or mutate save files.  It implements
the small KSC1/KNOW surface documented by EnshroudedSaveExplorer so Control
Center can inventory progression evidence without claiming world-save support.
"""
from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path


class SaveFormatError(ValueError):
    """Raised when a save does not match the supported read-only surface."""


@dataclass(frozen=True)
class SaveBlob:
    owner_id: int
    blob_type: bytes
    compressed_size: int
    payload_offset: int


@dataclass(frozen=True)
class Ksc1Header:
    blob_count: int
    save_id: bytes
    blobs: tuple[SaveBlob, ...]


@dataclass(frozen=True)
class KnowEntry:
    knowledge_id: int
    value: int


def candidate_save_directories(user_home: Path | None = None) -> tuple[Path, ...]:
    """Return the standard Windows save locations, without touching files."""
    home = Path(user_home or Path.home()).expanduser().resolve()
    candidates = (
        home / "Saved Games" / "Enshrouded",
        home / "AppData" / "Roaming" / "Enshrouded",
        home / "AppData" / "Local" / "Enshrouded",
        home / "AppData" / "Local" / "Enshrouded" / "savegame",
        home / "AppData" / "LocalLow" / "Keen Games" / "Enshrouded",
    )
    return tuple(dict.fromkeys(candidates))


def discover_save_directories(user_home: Path | None = None) -> dict[str, object]:
    """Describe standard save candidates; never creates, copies, or edits them."""
    candidates = candidate_save_directories(user_home)
    return {
        "schema": "control_center.save_discovery.v1",
        "read_only": True,
        "candidates": [
            {
                "path": str(path),
                "exists": path.is_dir(),
                "has_character_index": (path / "characters-index").is_file(),
            }
            for path in candidates
        ],
    }


def parse_ksc1_header(data: bytes) -> Ksc1Header:
    """Parse the KSC1 table without decompressing or modifying payloads."""
    if len(data) < 24 or data[:4] != b"KSC1":
        raise SaveFormatError("not a KSC1 character save")
    blob_count = struct.unpack_from("<I", data, 4)[0]
    table_end = 24 + blob_count * 12
    if table_end > len(data):
        raise SaveFormatError("KSC1 blob table exceeds file bounds")
    blobs: list[SaveBlob] = []
    payload_offset = table_end
    for index in range(blob_count):
        offset = 24 + index * 12
        owner_id, blob_type, compressed_size = struct.unpack_from("<I4sI", data, offset)
        if compressed_size > len(data) - payload_offset:
            raise SaveFormatError("KSC1 blob payload exceeds file bounds")
        blobs.append(SaveBlob(owner_id, blob_type, compressed_size, payload_offset))
        payload_offset += compressed_size
    return Ksc1Header(blob_count, data[8:24], tuple(blobs))


def decode_know(data: bytes) -> tuple[KnowEntry, ...]:
    """Decode an already-decompressed KNOW blob."""
    if len(data) < 12:
        raise SaveFormatError("KNOW blob is truncated")
    version, unknown, count = struct.unpack_from("<III", data, 0)
    expected = 12 + count * 8
    if expected != len(data):
        raise SaveFormatError("KNOW blob size does not match entry count")
    if version != 2 or unknown != 1:
        raise SaveFormatError("unsupported KNOW header")
    ids = struct.unpack_from(f"<{count}I", data, 12) if count else ()
    values = struct.unpack_from(f"<{count}I", data, 12 + count * 4) if count else ()
    return tuple(KnowEntry(knowledge_id, value) for knowledge_id, value in zip(ids, values))


def active_character_path(save_dir: Path) -> Path:
    """Resolve the active rolling character save using characters-index."""
    save_dir = Path(save_dir)
    index_path = save_dir / "characters-index"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8-sig"))
        latest = index["latest"]
    except (OSError, ValueError, KeyError, TypeError):
        raise SaveFormatError("invalid characters-index") from None
    if isinstance(latest, bool) or not isinstance(latest, int) or not 0 <= latest <= 9:
        raise SaveFormatError("characters-index latest must be an integer from 0 through 9")
    return save_dir / ("characters" if latest == 0 else f"characters-{latest}")


def inspect_save_directory(save_dir: Path) -> dict[str, object]:
    """Return a non-mutating inventory of the supported character-save surface."""
    save_dir = Path(save_dir).expanduser().resolve()
    character = active_character_path(save_dir)
    if not character.is_file():
        raise SaveFormatError(f"active character save is missing: {character.name}")
    header = parse_ksc1_header(character.read_bytes())
    return {
        "schema": "control_center.save_inspection.v1",
        "save_directory": str(save_dir),
        "active_character": character.name,
        "save_id_hex": header.save_id.hex(),
        "blob_count": header.blob_count,
        "blob_types": [blob.blob_type.decode("ascii", errors="replace") for blob in header.blobs],
        "read_only": True,
        "world_save_supported": False,
    }
