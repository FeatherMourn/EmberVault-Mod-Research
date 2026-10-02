from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DonorRecord:
    index: int
    guid: str
    item_id: int
    debug_name: str
    category: str


class DonorIndex:
    def __init__(self, records: Iterable[DonorRecord]):
        self.records = tuple(records)

    @classmethod
    def from_json(cls, path: str | Path) -> "DonorIndex":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("donor catalog must be a JSON list")
        records = [DonorRecord(int(item["index"]), str(item["guid"]), int(item["item_id"]),
                              str(item["debug_name"]), str(item["category"])) for item in raw]
        return cls(records)

    def search(self, query: str = "", *, category: str | None = None) -> list[DonorRecord]:
        needle = query.casefold().strip()
        return [record for record in self.records
                if (category is None or record.category.casefold() == category.casefold())
                and (not needle or needle in record.debug_name.casefold()
                     or needle in record.guid.casefold()
                     or needle == str(record.item_id))]


def parse_content_probe_lines(lines: Iterable[str]) -> list[DonorRecord]:
    records: list[DonorRecord] = []
    marker = "[CC-CONTENT-PROBE] ITEM|"
    for line in lines:
        if marker not in line:
            continue
        payload = line.split(marker, 1)[1].split('"', 1)[0]
        fields = payload.split("|")
        values = {key: value for field in fields[1:] if "=" in field for key, value in [field.split("=", 1)]}
        try:
            records.append(DonorRecord(int(fields[0]), values["guid"], int(values["itemId"]), values["debugName"], values.get("category", "Unknown")))
        except (KeyError, ValueError):
            continue
    return sorted({record.guid: record for record in records}.values(), key=lambda record: (record.category, record.debug_name, record.guid))


def import_eml_log(log_path: str | Path, output_path: str | Path) -> list[DonorRecord]:
    records = parse_content_probe_lines(Path(log_path).read_text(encoding="utf-8", errors="replace").splitlines())
    Path(output_path).write_text(json.dumps([asdict(record) for record in records], indent=2) + "\n", encoding="utf-8")
    return records
