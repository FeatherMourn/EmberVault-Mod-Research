"""Catalog boundary for validated EML probe records."""
from __future__ import annotations

from typing import Any

from .catalog_store import CatalogStore


def import_probe_result(store: CatalogStore, result: dict[str, Any]) -> int:
    """Import only a read-only, runtime-unapproved probe result."""
    if result.get("read_only") is not True or result.get("runtime_approval") is not False:
        raise ValueError("probe result is outside the read-only catalog boundary")
    records = result.get("records")
    if not isinstance(records, list):
        raise ValueError("probe result records must be a list")
    return store.import_records(records)
