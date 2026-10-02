"""Stable release-candidate gates."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from .storage import write_json_atomic


class ReleaseCandidateService:
    def __init__(self, root: Path, promotion):
        self.root = Path(root)
        self.promotion = promotion

    def audit(self, capabilities: list[str]) -> dict:
        stable, blocked = [], []
        for capability in capabilities:
            state = self.promotion.approved_state(capability)
            (stable if state == "stable" else blocked).append({"capability_id": capability, "state": state})
        return {"ready": not blocked, "stable": stable, "blocked": blocked,
                "unsupported_mutation_claimed": False, "application_state": "release-audit"}

    def create(self, version: str, capabilities: list[str]) -> Path:
        audit = self.audit(capabilities)
        if not audit["ready"]:
            raise ValueError("Release candidate requires Stable evidence for every listed capability")
        destination = self.root / "releases" / f"embervault-{version}-rc.json"
        write_json_atomic(destination, {"schema_version": 1, "version": version,
            "channel": "stable", "audit": audit, "generated_at": datetime.now(timezone.utc).isoformat()})
        return destination
