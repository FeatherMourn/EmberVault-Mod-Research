"""Fail-closed capability promotion decisions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json


STATES = ("research-only", "experimental", "verified", "stable")


@dataclass(frozen=True)
class PromotionEvidence:
    capability_id: str
    current_build: str
    reproducible: bool
    runtime_confirmed: bool
    recovery_tested: bool
    compatibility_documented: bool
    owner: str
    rollback_tested: bool
    source_research_id: str = ""


class PromotionService:
    def __init__(self, root: Path):
        self.path = Path(root) / "promotion" / "decisions.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def validate(evidence: PromotionEvidence, target_state: str) -> None:
        if target_state not in STATES:
            raise ValueError("Unknown capability promotion state")
        if target_state == "research-only":
            return
        if not evidence.capability_id.strip() or not evidence.current_build.strip() or not evidence.owner.strip():
            raise ValueError("Promotion requires capability, current build, and owner")
        required = (evidence.reproducible, evidence.runtime_confirmed,
                    evidence.recovery_tested, evidence.compatibility_documented,
                    evidence.rollback_tested)
        if not all(required):
            raise ValueError("Promotion requires reproducibility, runtime confirmation, recovery, compatibility, and rollback evidence")

    def promote(self, evidence: PromotionEvidence, target_state: str) -> dict:
        self.validate(evidence, target_state)
        decision = {"schema_version": 1, "target_state": target_state,
                    "decided_at": datetime.now(timezone.utc).isoformat(),
                    "evidence": asdict(evidence)}
        records = []
        if self.path.exists():
            try: records = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError, json.JSONDecodeError): records = []
        records = records if isinstance(records, list) else []
        records.append(decision)
        self.path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
        return decision

    def decisions(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return []
        return [item for item in raw if isinstance(item, dict) and isinstance(item.get("evidence"), dict)] if isinstance(raw, list) else []

    def approved_state(self, capability_id: str) -> str:
        states = {item.get("target_state") for item in self.decisions()
                  if item.get("evidence", {}).get("capability_id") == capability_id}
        return max(states, key=STATES.index) if states else "research-only"

    @staticmethod
    def missing_requirements(evidence: PromotionEvidence | None) -> list[str]:
        if evidence is None:
            return ["current build", "reproducibility", "runtime confirmation", "recovery testing", "compatibility documentation", "owner", "rollback testing"]
        checks = (("reproducibility", evidence.reproducible), ("runtime confirmation", evidence.runtime_confirmed),
                  ("recovery testing", evidence.recovery_tested), ("compatibility documentation", evidence.compatibility_documented),
                  ("owner", bool(evidence.owner.strip())), ("rollback testing", evidence.rollback_tested))
        return [name for name, valid in checks if not valid]
