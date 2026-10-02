"""Local, searchable knowledge entries for the Control Center."""
from __future__ import annotations

import json
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from datetime import datetime, timezone

from .storage import write_json_atomic


@dataclass(frozen=True)
class KnowledgeEntry:
    id: str
    title: str
    category: str
    summary: str
    content: str
    published: bool = True
    published_at: str = ""
    tags: tuple[str, ...] = ()
    related_ids: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    version: int = 1
    history: tuple[dict, ...] = ()


class KnowledgeService:
    def __init__(self, root: Path):
        self.path = Path(root) / "knowledge" / "entries.json"
        source_root = Path(__file__).resolve().parents[1] / "knowledge" / "entries.json"
        installed_root = Path(sys.prefix) / "knowledge" / "entries.json"
        self.seed_path = source_root if source_root.exists() else installed_root
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def entries(self) -> list[KnowledgeEntry]:
        source = self.path if self.path.exists() else self.seed_path
        if not source.exists():
            return []
        try:
            raw_entries = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return []
        if not isinstance(raw_entries, list):
            return []
        entries: list[KnowledgeEntry] = []
        seen: set[str] = set()
        for item in raw_entries:
            if not isinstance(item, dict):
                continue
            values = {key: item.get(key) for key in ("id", "title", "category", "summary", "content")}
            if not all(isinstance(value, str) and value.strip() for value in values.values()):
                continue
            entry_id = values["id"].strip()
            if entry_id in seen:
                continue
            seen.add(entry_id)
            raw_tags = item.get("tags", [])
            raw_related = item.get("related_ids", [])
            raw_evidence = item.get("evidence_refs", [])
            clean_lists = {}
            for field_name, raw_values in (("tags", raw_tags), ("related_ids", raw_related), ("evidence_refs", raw_evidence)):
                if not isinstance(raw_values, (list, tuple)):
                    raw_values = []
                clean_lists[field_name] = tuple(sorted({value.strip() for value in raw_values
                                                         if isinstance(value, str) and value.strip()}))
            version = item.get("version", 1)
            if not isinstance(version, int) or isinstance(version, bool) or version < 1:
                version = 1
            history = item.get("history", [])
            if not isinstance(history, list):
                history = []
            entries.append(KnowledgeEntry(**{key: value.strip() for key, value in values.items()},
                                           **clean_lists, version=version,
                                           history=tuple(item for item in history if isinstance(item, dict))))
            entries[-1] = KnowledgeEntry(**{**asdict(entries[-1]),
                                             "published": item.get("published", True) if isinstance(item.get("published", True), bool) else True,
                                             "published_at": item.get("published_at", "") if isinstance(item.get("published_at", ""), str) else ""})
        return entries

    def search(self, query: str = "") -> list[KnowledgeEntry]:
        needle = query.strip().lower()
        if not needle:
            return self.entries()
        return [entry for entry in self.entries() if needle in " ".join((
            entry.title, entry.category, entry.summary, entry.content,
            *entry.tags, *entry.related_ids, *entry.evidence_refs)).lower()]

    def create(self, title: str, category: str, summary: str, content: str,
               tags: list[str] | None = None, related_ids: list[str] | None = None,
               evidence_refs: list[str] | None = None) -> KnowledgeEntry:
        values = (title, category, summary, content)
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError("Knowledge title, category, summary, and content are required")
        entry = KnowledgeEntry(
            id=f"EV-KNOW-{uuid.uuid4().hex[:8].upper()}",
            title=title.strip(), category=category.strip(),
            summary=summary.strip(), content=content.strip(),
            published=False,
            tags=self._clean_ids(tags), related_ids=self._clean_ids(related_ids),
            evidence_refs=self._clean_ids(evidence_refs),
        )
        records = self.entries()
        records.append(entry)
        write_json_atomic(self.path, [asdict(item) for item in records])
        return entry

    @staticmethod
    def _clean_ids(values: list[str] | None) -> tuple[str, ...]:
        if values is None:
            return ()
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("Knowledge references must be non-empty string IDs")
        return tuple(sorted({value.strip() for value in values}))

    def update(self, entry_id: str, title: str, category: str, summary: str, content: str,
               tags: list[str] | None = None, related_ids: list[str] | None = None,
               evidence_refs: list[str] | None = None) -> KnowledgeEntry:
        values = (title, category, summary, content)
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError("Knowledge title, category, summary, and content are required")
        records = self.entries()
        for index, entry in enumerate(records):
            if entry.id == entry_id:
                history = list(entry.history) + [{"version": entry.version, "title": entry.title,
                    "summary": entry.summary, "content": entry.content, "saved_at": datetime.now(timezone.utc).isoformat()}]
                records[index] = KnowledgeEntry(entry.id, title.strip(), category.strip(), summary.strip(), content.strip(),
                    False, "", self._clean_ids(tags), self._clean_ids(related_ids), self._clean_ids(evidence_refs),
                    entry.version + 1, tuple(history))
                write_json_atomic(self.path, [asdict(item) for item in records])
                return records[index]
        raise KeyError(entry_id)

    def publish(self, entry_id: str) -> KnowledgeEntry:
        return self._set_publication(entry_id, True)

    def unpublish(self, entry_id: str) -> KnowledgeEntry:
        return self._set_publication(entry_id, False)

    def _set_publication(self, entry_id: str, published: bool) -> KnowledgeEntry:
        records = self.entries()
        for index, entry in enumerate(records):
            if entry.id == entry_id:
                records[index] = KnowledgeEntry(**{**asdict(entry),
                    "published": published,
                    "published_at": datetime.now(timezone.utc).isoformat() if published else ""})
                write_json_atomic(self.path, [asdict(item) for item in records])
                return records[index]
        raise KeyError(entry_id)
