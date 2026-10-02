"""Read-only inspection helpers for the supplied Cheat Engine table.

This module deliberately does not write to, launch scripts from, or mutate a
CT file.  It exists so the GUI can identify the exact table it is opening and
show an honest inventory of records.
"""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrainerRecord:
    record_id: str
    description: str
    variable_type: str | None
    address: str | None
    has_script: bool
    group_header: bool
    depth: int


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _description(entry: ET.Element) -> str:
    value = entry.findtext("Description", default="").strip()
    return value.strip('"')


def inventory(path: Path) -> list[TrainerRecord]:
    root = ET.parse(path).getroot()
    records: list[TrainerRecord] = []

    def visit(parent: ET.Element, depth: int) -> None:
        for entry in parent.findall("CheatEntry"):
            records.append(TrainerRecord(
                record_id=entry.findtext("ID", default=""),
                description=_description(entry),
                variable_type=entry.findtext("VariableType"),
                address=entry.findtext("Address"),
                has_script=entry.find("AssemblerScript") is not None,
                group_header=entry.findtext("GroupHeader") == "1",
                depth=depth,
            ))
            children = entry.find("CheatEntries")
            if children is not None:
                visit(children, depth + 1)

    entries = root.find("CheatEntries")
    if entries is not None:
        visit(entries, 0)
    return records


def describe(path: Path) -> dict[str, object]:
    records = inventory(path)
    return {
        "path": str(path),
        "sha256": sha256(path),
        "record_count": len(records),
        "script_count": sum(record.has_script for record in records),
        "value_count": sum(bool(record.address) for record in records),
        "group_count": sum(record.group_header for record in records),
    }
