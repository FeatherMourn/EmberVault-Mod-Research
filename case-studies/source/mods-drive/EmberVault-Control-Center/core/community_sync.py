"""Conflict-safe, reviewable handoffs for the EmberVault website."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from .storage import write_json_atomic


class CommunitySyncService:
    def __init__(self, root: Path, catalog):
        self.root = Path(root)
        self.catalog = catalog
        self.path = self.root / "community" / "handoff.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def prepare(self) -> dict:
        payload = self.catalog.build()
        return {"schema_version": 1, "handoff_type": "embervault-public-sync",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "authority": "website", "catalog": payload}

    def stage(self) -> Path:
        handoff = self.prepare()
        self.catalog.validate(handoff["catalog"])
        write_json_atomic(self.path, handoff)
        return self.path

    @staticmethod
    def compare(local: dict, remote: dict) -> dict:
        if not isinstance(local, dict) or not isinstance(remote, dict):
            raise ValueError("Community handoffs must be objects")
        left = local.get("catalog", local)
        right = remote.get("catalog", remote)
        if not isinstance(left, dict) or not isinstance(right, dict):
            raise ValueError("Community handoffs must contain catalog objects")
        differences = sorted(key for key in set(left) | set(right) if left.get(key) != right.get(key))
        return {"status": "identical" if not differences else "conflict",
                "conflicting_sections": differences, "automatic_overwrite": False}

    def import_remote(self, remote: dict) -> dict:
        """Validate and compare a website snapshot; never overwrite local data."""
        self.catalog.validate(remote.get("catalog", remote))
        local = self.prepare()
        result = self.compare(local, remote)
        result["review_required"] = result["status"] == "conflict"
        result["authority"] = "website"
        return result

    def stage_record(self, record_type: str, record_id: str, version: int, payload: dict,
                     discussion_url: str = "") -> Path:
        """Stage one sanitized website submission without claiming remote authority."""
        if record_type not in {"research", "content", "knowledge"} or not record_id.strip():
            raise ValueError("Unsupported community record type")
        if not isinstance(version, int) or version < 1 or not isinstance(payload, dict):
            raise ValueError("Community records require a versioned object payload")
        if any(token in json.dumps(payload).lower() for token in ("game_path", "profile_id", "private_path")):
            raise ValueError("Community payload contains private data")
        envelope = {"schema_version": 1, "record_type": record_type, "record_id": record_id,
                    "record_version": version, "authority": "website",
                    "discussion_url": discussion_url.strip(), "payload": payload,
                    "application_state": "website-review-required",
                    "generated_at": datetime.now(timezone.utc).isoformat()}
        destination = self.root / "community" / "submissions" / f"{record_type}-{record_id}.json"
        write_json_atomic(destination, envelope)
        return destination

    def compare_record(self, local: dict, remote: dict) -> dict:
        if local.get("record_id") != remote.get("record_id") or local.get("record_type") != remote.get("record_type"):
            raise ValueError("Community records do not identify the same object")
        local_version, remote_version = local.get("record_version"), remote.get("record_version")
        conflict = local_version != remote_version and local.get("payload") != remote.get("payload")
        return {"status": "conflict" if conflict else "compatible", "record_id": local.get("record_id"),
                "local_version": local_version, "remote_version": remote_version,
                "review_required": conflict, "automatic_overwrite": False}
