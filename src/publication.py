"""Sanitized Web Catalog publication records."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .catalog_store import CatalogStore


def build_web_publication(records: Iterable[dict[str, Any]], *, reviewed_ids: set[str] | None = None) -> dict[str, Any]:
    """Create public-safe records; raw evidence paths and private claims never cross this boundary."""
    reviewed_ids = reviewed_ids or set()
    published = []
    for record in sorted(records, key=lambda item: item["id"]):
        if reviewed_ids and record["id"] not in reviewed_ids:
            continue
        published.append({
            "id": record["id"],
            "kind": record["kind"],
            "identity": record["identity"],
            "build_scope": record.get("build_scope", []),
            "status": record["state"],
            "confidence": record.get("confidence"),
            "summary": record.get("supported_claims", []),
            "limitations": record.get("unsupported_claims", []),
            "open_questions": record.get("open_questions", []),
            "evidence_count": len(record.get("evidence", [])),
            "reviewed": record["id"] in reviewed_ids,
        })
    return {"schema_version": 1, "publication": "web-catalog", "records": published}


def build_web_publication_from_catalog(catalog_path: Path, *, reviewed_ids: set[str], generated_at: str) -> dict[str, Any]:
    """Build the public snapshot from the durable catalog without mutating it."""
    store = CatalogStore(catalog_path)
    try:
        publication = build_web_publication(store.records(), reviewed_ids=reviewed_ids)
    finally:
        store.close()
    publication["generated_at"] = generated_at
    return publication
