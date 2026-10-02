"""Deterministic identity and ownership helpers for imported content."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


IDENTITY_NAMESPACE = uuid.UUID("8f5f3e93-73c2-4d8a-bf5c-c7f2d5f45a61")
ID_MIN = 3_800_000_000
ID_MAX = 4_294_967_000
NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_-]{2,63}$")


@dataclass(frozen=True)
class ContentIdentity:
    namespace: str
    slug: str
    numeric_id: int
    guid: str


class ContentIdentityService:
    """Generate stable identities and persist ownership claims locally."""

    def __init__(self, registry_path: Path):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def identity(self, namespace: str, slug: str, occupied_ids: set[int] | frozenset[int] | tuple[int, ...] = ()) -> ContentIdentity:
        """Return a stable identity that avoids local and known runtime IDs.

        ``occupied_ids`` is supplied by a catalog/resource discovery step when
        allocating against a live or exported game registry. It is deliberately
        explicit: the identity service cannot infer the game's occupied IDs
        from the local ownership file alone.
        """
        namespace = self.validate_namespace(namespace)
        slug = self._slug(slug)
        try:
            occupied = {int(value) for value in occupied_ids}
        except (TypeError, ValueError) as exc:
            raise ValueError("occupied_ids must contain integers") from exc
        if any(value <= 0 for value in occupied):
            raise ValueError("occupied_ids must contain positive integers")
        key = f"{namespace}:{slug}"
        existing = self._data.get("identities", {}).get(key)
        if existing:
            if int(existing["numeric_id"]) in occupied:
                raise ValueError(f"Existing identity is occupied by another runtime ID: {key}")
            return ContentIdentity(namespace, slug, int(existing["numeric_id"]), str(existing["guid"]))
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        span = ID_MAX - ID_MIN + 1
        numeric_id = ID_MIN + (int.from_bytes(digest[:8], "big") % span)
        # A collision is rare, but ownership must remain explicit and stable.
        used = {int(item["numeric_id"]) for item in self._data.get("identities", {}).values()}
        used.update(occupied)
        while numeric_id in used:
            numeric_id = ID_MIN + ((numeric_id - ID_MIN + 1) % span)
        guid = str(uuid.uuid5(IDENTITY_NAMESPACE, key))
        identity = ContentIdentity(namespace, slug, numeric_id, guid)
        self._data.setdefault("identities", {})[key] = {
            "namespace": namespace, "slug": slug, "numeric_id": numeric_id, "guid": guid
        }
        self._save()
        return identity

    def claim(self, identity: ContentIdentity, owner: str) -> None:
        owner = str(owner).strip()
        if not owner:
            raise ValueError("Content identity owner cannot be empty.")
        claims = self._data.setdefault("claims", {})
        key = f"{identity.namespace}:{identity.slug}"
        previous = claims.get(key)
        if previous and previous != owner:
            raise ValueError(f"Content identity is already owned by {previous}: {key}")
        claims[key] = owner
        self._save()

    @staticmethod
    def validate_namespace(namespace: str) -> str:
        namespace = str(namespace).strip().lower()
        if not NAMESPACE_RE.fullmatch(namespace):
            raise ValueError("Namespace must start with a letter and contain 3-64 lowercase letters, digits, '_' or '-'.")
        return namespace

    @staticmethod
    def _slug(value: str) -> str:
        value = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value).strip()).strip("-").lower()
        if not value:
            raise ValueError("Content slug cannot be empty.")
        return value[:96]

    def _load(self) -> dict[str, Any]:
        if not self.registry_path.is_file():
            return {"version": 1, "identities": {}, "claims": {}}
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"version": 1, "identities": {}, "claims": {}}
        return data if isinstance(data, dict) else {"version": 1, "identities": {}, "claims": {}}

    def _save(self) -> None:
        temporary = self.registry_path.with_suffix(self.registry_path.suffix + ".tmp")
        temporary.write_text(json.dumps(self._data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.registry_path)
