"""Controlled maturity labels shared by research and deployment surfaces."""
from __future__ import annotations

from enum import StrEnum
from typing import Any


class CapabilityStatus(StrEnum):
    VERIFIED = "verified"
    EXPERIMENTAL = "experimental"
    RESEARCH_ONLY = "research-only"
    UNSUPPORTED = "unsupported"


def is_promotable(status: str | CapabilityStatus) -> bool:
    return CapabilityStatus(status) == CapabilityStatus.VERIFIED


def require_known(status: str | CapabilityStatus) -> CapabilityStatus:
    try:
        return CapabilityStatus(status)
    except ValueError as exc:
        raise ValueError(f"Unknown capability status: {status}") from exc


def audit_evidence(evidence: dict[str, Any]) -> CapabilityStatus:
    """Conservatively derive maturity from explicit evidence flags."""
    if not isinstance(evidence, dict):
        raise ValueError("Evidence must be an object.")
    if evidence.get("unsupported"):
        return CapabilityStatus.UNSUPPORTED
    if evidence.get("visual_verified") and evidence.get("runtime_verified") \
            and evidence.get("rollback_verified"):
        return CapabilityStatus.VERIFIED
    if evidence.get("runtime_verified"):
        return CapabilityStatus.EXPERIMENTAL
    return CapabilityStatus.RESEARCH_ONLY
