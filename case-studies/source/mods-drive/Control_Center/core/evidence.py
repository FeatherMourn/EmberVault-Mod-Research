"""Conservative evidence-state normalization for research and publication."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class EvidenceLevel(IntEnum):
    REVIEW_REQUIRED = 0
    PACKAGED = 1
    RUNTIME_VERIFIED = 2
    VISUAL_VERIFIED = 3


@dataclass(frozen=True)
class EvidenceState:
    level: EvidenceLevel
    label: str
    reasons: tuple[str, ...]


def classify_evidence(record: dict[str, Any]) -> EvidenceState:
    """Promote only from explicit evidence fields; never infer visual proof."""
    reasons: list[str] = []
    if record.get("package_valid") is True:
        level = EvidenceLevel.PACKAGED
        reasons.append("package integrity verified")
    else:
        return EvidenceState(EvidenceLevel.REVIEW_REQUIRED, "review_required", ("package integrity is not verified",))
    if record.get("runtime_verified") is True:
        level = EvidenceLevel.RUNTIME_VERIFIED
        reasons.append("runtime registration evidence recorded")
    if record.get("visual_verified") is True and record.get("visual_evidence"):
        level = EvidenceLevel.VISUAL_VERIFIED
        reasons.append("visual evidence is explicitly attached")
    return EvidenceState(level, {
        EvidenceLevel.PACKAGED: "packaged",
        EvidenceLevel.RUNTIME_VERIFIED: "runtime_verified",
        EvidenceLevel.VISUAL_VERIFIED: "visual_verified",
    }.get(level, "review_required"), tuple(reasons))
