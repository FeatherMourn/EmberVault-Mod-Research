"""Game-independent target observation contract.

The contract intentionally models *observations*, not a callable target
resolver. Every semantic value is optional and must carry provenance so an
unknown target cannot be mistaken for a valid building/entity/terrain result.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

TargetKind = Literal["building", "terrain", "entity", "plant", "item", "unknown"]


@dataclass(frozen=True)
class TargetProvenance:
    source: str
    status: Literal["PROVEN", "INFERRED", "UNKNOWN"]
    evidence: str
    function_rva: str | None = None
    field_path: str | None = None

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.evidence.strip():
            raise ValueError("target provenance source and evidence are required")
        if self.status not in {"PROVEN", "INFERRED", "UNKNOWN"}:
            raise ValueError("invalid target provenance status")


@dataclass(frozen=True)
class ArchitectTargetObservation:
    """Optional semantic target snapshot produced by a future adapter.

    ``kind`` defaults to ``unknown`` and semantic payloads remain ``None``
    until an adapter supplies evidence. This class has no game/process
    dependencies and performs no I/O.
    """

    target_id: str | None = None
    source_capability: str = "target.observe_target"
    raw_evidence: dict[str, Any] | None = None
    kind: TargetKind = "unknown"
    item_identity: dict[str, Any] | None = None
    entity_identity: dict[str, Any] | None = None
    material: dict[str, Any] | None = None
    transform: dict[str, Any] | None = None
    bounds: dict[str, Any] | None = None
    resource_identity: dict[str, Any] | None = None
    project_membership: dict[str, Any] | None = None
    provenance: tuple[TargetProvenance, ...] = field(default_factory=tuple)
    confidence: float = 0.0
    observed_at: str | None = None

    def __post_init__(self) -> None:
        if not self.source_capability.strip():
            raise ValueError("source_capability is required")
        if self.kind not in {"building", "terrain", "entity", "plant", "item", "unknown"}:
            raise ValueError("invalid target kind")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("target confidence must be between 0 and 1")
        if self.kind == "unknown" and any(v is not None for v in (self.item_identity, self.entity_identity, self.material, self.transform, self.bounds, self.resource_identity, self.project_membership)) and not self.provenance:
            raise ValueError("semantic payload for unknown target requires provenance")
        if self.observed_at is not None:
            try:
                datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("observed_at must be ISO-8601") from exc

    @classmethod
    def unknown(cls, source: str = "offline", evidence: str = "no target observer installed") -> "ArchitectTargetObservation":
        return cls(provenance=(TargetProvenance(source, "UNKNOWN", evidence),))

    def to_dict(self) -> dict[str, Any]:
        return {
            "targetId": self.target_id,
            "sourceCapability": self.source_capability,
            "rawEvidence": self.raw_evidence,
            "kind": self.kind,
            "itemIdentity": self.item_identity,
            "entityIdentity": self.entity_identity,
            "material": self.material,
            "transform": self.transform,
            "bounds": self.bounds,
            "resourceIdentity": self.resource_identity,
            "projectMembership": self.project_membership,
            "provenance": [
                {"source": p.source, "status": p.status, "evidence": p.evidence,
                 "functionRva": p.function_rva, "fieldPath": p.field_path}
                for p in self.provenance
            ],
            "confidence": self.confidence,
            "observedAt": self.observed_at,
        }


def new_unknown_observation() -> ArchitectTargetObservation:
    """Return an explicit unknown observation with a deterministic timestamp omitted."""
    return ArchitectTargetObservation.unknown()
