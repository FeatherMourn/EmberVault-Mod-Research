"""Shared context for cross-module actions.

Modules exchange IDs and safety state through this small contract instead of
passing service objects or reaching into another module's private storage.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IntegrationContext:
    """Identity and safety metadata that must survive a module handoff."""

    operation_id: str
    profile_id: str
    capability: str
    capability_state: str
    recovery_expectation: str

    def __post_init__(self) -> None:
        values = (self.operation_id, self.profile_id, self.capability,
                  self.capability_state, self.recovery_expectation)
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("Integration context fields must be non-empty strings")
        if self.capability_state not in {"ready", "gated", "staged", "read-only", "plan-only"}:
            raise ValueError("Unknown capability state")

    def as_dict(self) -> dict[str, str]:
        return {
            "operation_id": self.operation_id,
            "profile_id": self.profile_id,
            "capability": self.capability,
            "capability_state": self.capability_state,
            "recovery_expectation": self.recovery_expectation,
        }

    @classmethod
    def from_operation(cls, operation: Any, *, capability: str,
                       capability_state: str, recovery_expectation: str) -> "IntegrationContext":
        if not getattr(operation, "id", None) or not getattr(operation, "profile_id", None):
            raise ValueError("An operation with a profile is required for integration")
        return cls(operation.id, operation.profile_id, capability,
                   capability_state, recovery_expectation)
