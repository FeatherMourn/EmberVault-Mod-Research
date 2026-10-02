from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from .models import Coordinate, Piece


@dataclass(frozen=True)
class CapabilityEvidence:
    capability: str
    status: str
    evidence: str
    game_build: str | None = None
    persisted: bool | None = None
    multiplayer: str = "unverified"


@dataclass
class RuntimeReport:
    adapter_id: str
    evidence: list[CapabilityEvidence] = field(default_factory=list)

    def record(self, capability: str, status: str, evidence: str, **kwargs: Any) -> None:
        self.evidence.append(CapabilityEvidence(capability, status, evidence, **kwargs))

    def status(self, capability: str) -> str:
        matches = [item.status for item in self.evidence if item.capability == capability]
        return matches[-1] if matches else "unverified"

    def require_verified(self, capability: str) -> None:
        """Guard an operation that must be backed by verified runtime evidence."""
        current = self.status(capability)
        if current != "verified":
            raise RuntimeCapabilityError(
                f"runtime capability '{capability}' is {current}, not verified"
            )

    @classmethod
    def from_probe_export(
        cls, data: Mapping[str, Any], *, adapter_id: str = "eml-probe",
        game_build: str | None = None,
    ) -> "RuntimeReport":
        """Convert a read-only EML probe marker into shared SDK evidence.

        Probe exports are intentionally treated as capability evidence only;
        they never imply that construction or persistence succeeded.
        """
        report = cls(adapter_id)
        state = str(data.get("state", "unverified"))
        detail = str(data.get("detail", ""))
        report.record("eml_mod_loading", "verified", "probe export was written", game_build=game_build)
        report.record("read_only_asset_probe", "verified", detail, game_build=game_build)
        if state != "capabilities_observed":
            report.record("runtime_probe", "inconclusive", detail, game_build=game_build)
        else:
            report.record("runtime_probe", "verified", detail, game_build=game_build)
        report.record("world_capture", "unverified", "no world/player capture evidence", game_build=game_build)
        report.record("construction_mutation", "unverified", "no placement or mutation evidence", game_build=game_build)
        return report


class RuntimeAdapter(Protocol):
    """The only boundary allowed to communicate with a live game runtime."""

    def player_position(self) -> Coordinate: ...
    def inspect(self, position: Coordinate) -> Piece | None: ...
    def place(self, piece: Piece) -> bool: ...
    def remove(self, position: Coordinate) -> bool: ...


class RuntimeCapabilityError(RuntimeError):
    """Raised when a requested live-game operation lacks runtime evidence."""


class UnavailableRuntimeAdapter:
    """Explicit boundary for builds where EML exposes no world/action surface."""

    def __init__(self, reason: str = "live runtime world/construction API unavailable"):
        self.reason = reason

    def _unavailable(self) -> None:
        raise RuntimeCapabilityError(self.reason)

    def player_position(self) -> Coordinate:
        self._unavailable()

    def inspect(self, position: Coordinate) -> Piece | None:
        self._unavailable()

    def place(self, piece: Piece) -> bool:
        self._unavailable()

    def remove(self, position: Coordinate) -> bool:
        self._unavailable()


class SimulatedAdapter:
    def __init__(self, world: Any):
        self.world = world

    def player_position(self) -> Coordinate:
        return Coordinate(0, 0, 0)

    def inspect(self, position: Coordinate) -> Piece | None:
        return self.world.inspect(position)

    def place(self, piece: Piece) -> bool:
        self.world.put(piece)
        return True

    def remove(self, position: Coordinate) -> bool:
        return self.world.remove(position) is not None
