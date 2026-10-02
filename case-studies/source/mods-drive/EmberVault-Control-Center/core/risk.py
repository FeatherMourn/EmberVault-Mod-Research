"""Launch gates for higher-risk or separate-process capabilities."""
from __future__ import annotations

from dataclasses import dataclass

from .profiles import Profile
from .save_manager import SaveManagerService, SaveManagerError


@dataclass(frozen=True)
class RiskDecision:
    capability: str
    allowed: bool
    reasons: tuple[str, ...] = ()


class RiskGateService:
    def __init__(self, saves: SaveManagerService | None = None):
        self.saves = saves

    def evaluate(self, capability: str, profile: Profile, *, verified_backup_id: str | None = None) -> RiskDecision:
        reasons: list[str] = []
        if capability in {"trainer", "research", "content-creator", "tuning-audit"} and profile.profile_type != "research":
            reasons.append("Select the isolated Research profile.")
        if capability in {"trainer", "content-creator"}:
            backup_valid = False
            if verified_backup_id and self.saves:
                backup = next((item for item in self.saves.list_backups() if item.id == verified_backup_id), None)
                if backup and backup.verified:
                    try:
                        backup_valid = self.saves.verify_backup(backup.id)
                    except (SaveManagerError, OSError):
                        backup_valid = False
            if not backup_valid:
                reasons.append("Create or select a verified, checksum-valid backup first.")
        return RiskDecision(capability, not reasons, tuple(reasons))
