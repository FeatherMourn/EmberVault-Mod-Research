from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, order=True)
class Coordinate:
    x: int
    y: int
    z: int

    def add(self, other: "Coordinate") -> "Coordinate":
        return Coordinate(self.x + other.x, self.y + other.y, self.z + other.z)


@dataclass(frozen=True)
class Transform:
    rotation: int = 0
    mirror: str = "none"

    def normalized(self) -> "Transform":
        if self.rotation not in (0, 90, 180, 270):
            raise ValueError("rotation must be 0, 90, 180, or 270")
        if self.mirror not in ("none", "x", "y", "z"):
            raise ValueError("mirror must be none, x, y, or z")
        return self


@dataclass(frozen=True)
class Piece:
    position: Coordinate
    resource_id: str
    material_id: str | None = None
    orientation: int = 0
    properties: dict[str, Any] = field(default_factory=dict)

    def moved(self, position: Coordinate, orientation: int | None = None) -> "Piece":
        return Piece(position, self.resource_id, self.material_id,
                     self.orientation if orientation is None else orientation,
                     dict(self.properties))


@dataclass
class Blueprint:
    name: str
    pieces: list[Piece] = field(default_factory=list)
    blueprint_id: str | None = None
    source_type: str = "manual"
    format_version: str = "0.1"
    anchor: Coordinate = Coordinate(0, 0, 0)
    metadata: dict[str, Any] = field(default_factory=dict)

    def bounds(self) -> tuple[Coordinate, Coordinate]:
        if not self.pieces:
            return self.anchor, self.anchor
        coords = [p.position for p in self.pieces]
        return (Coordinate(min(c.x for c in coords), min(c.y for c in coords), min(c.z for c in coords)),
                Coordinate(max(c.x for c in coords), max(c.y for c in coords), max(c.z for c in coords)))

    def material_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for piece in self.pieces:
            key = piece.material_id or "unknown"
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "emberworks.blueprint",
            "version": self.format_version,
            "id": self.blueprint_id,
            "name": self.name,
            "source_type": self.source_type,
            "anchor": [self.anchor.x, self.anchor.y, self.anchor.z],
            "pieces": [
                {
                    "position": [p.position.x, p.position.y, p.position.z],
                    "resource_id": p.resource_id,
                    "material_id": p.material_id,
                    "orientation": p.orientation,
                    "properties": p.properties,
                }
                for p in self.pieces
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Blueprint":
        if data.get("format") != "emberworks.blueprint":
            raise ValueError("unsupported blueprint format")
        anchor = data.get("anchor", [0, 0, 0])
        pieces = []
        for raw in data.get("pieces", []):
            position = raw["position"]
            pieces.append(Piece(Coordinate(*position), raw["resource_id"], raw.get("material_id"),
                                raw.get("orientation", 0), dict(raw.get("properties", {}))))
        return cls(name=data["name"], pieces=pieces, blueprint_id=data.get("id"),
                   source_type=data.get("source_type", "manual"), format_version=data.get("version", "0.1"),
                   anchor=Coordinate(*anchor), metadata=dict(data.get("metadata", {})))
