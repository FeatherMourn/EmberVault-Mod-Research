"""Read-only Cheat Engine table inventory."""
from __future__ import annotations
import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Record:
    record_id: str
    description: str
    variable_type: str
    address: str
    script: bool
    group: bool
    depth: int

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest().upper()

def inventory(path: Path) -> list[Record]:
    root = ET.parse(path).getroot()
    out: list[Record] = []
    def walk(parent: ET.Element, depth: int) -> None:
        for e in parent.findall('CheatEntry'):
            out.append(Record(
                e.findtext('ID', ''), e.findtext('Description', '').strip().strip('"'),
                e.findtext('VariableType', ''), e.findtext('Address', ''),
                e.find('AssemblerScript') is not None, e.findtext('GroupHeader') == '1', depth))
            children = e.find('CheatEntries')
            if children is not None:
                walk(children, depth + 1)
    entries = root.find('CheatEntries')
    if entries is not None:
        walk(entries, 0)
    return out
