"""Guarded separate-process module launching."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .modules import LaunchContext, ModuleRegistry
from .profiles import Profile
from .risk import RiskGateService


@dataclass(frozen=True)
class LaunchDecision:
    allowed: bool
    reasons: tuple[str, ...] = ()


class ModuleLaunchService:
    def __init__(self, registry: ModuleRegistry, risk: RiskGateService, promotion=None):
        self.registry = registry
        self.risk = risk
        self.promotion = promotion

    def check(self, module_id: str, capability: str, profile: Profile, backup_id: str | None = None) -> LaunchDecision:
        risk = self.risk.evaluate(capability, profile, verified_backup_id=backup_id)
        if not risk.allowed:
            return LaunchDecision(False, risk.reasons)
        manifest = self.registry.get(module_id)
        if not manifest:
            return LaunchDecision(False, (f"Module is not installed: {module_id}",))
        if capability not in manifest.capabilities:
            return LaunchDecision(False, (f"Module does not declare the '{capability}' capability.",))
        if self.promotion and manifest.feature_state in {"verified", "stable"}:
            approved = self.promotion.approved_state(capability)
            if approved not in {"verified", "stable"}:
                return LaunchDecision(False, (f"Capability '{capability}' lacks a promotion decision.",))
        if not manifest.executable:
            return LaunchDecision(False, ("Module does not declare a separate-process executable.",))
        return LaunchDecision(True)

    def launch(self, module_id: str, capability: str, profile: Profile, context: LaunchContext,
               backup_id: str | None = None) -> subprocess.Popen:
        decision = self.check(module_id, capability, profile, backup_id)
        if not decision.allowed:
            raise PermissionError(" ".join(decision.reasons))
        return self.registry.launch(module_id, context)
