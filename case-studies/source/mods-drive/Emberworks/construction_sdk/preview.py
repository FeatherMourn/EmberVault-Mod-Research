from __future__ import annotations

from dataclasses import dataclass, field

from .models import Coordinate, Piece


@dataclass
class MaterialSummary:
    counts: dict[str, int] = field(default_factory=dict)

    def add(self, material_id: str | None, amount: int = 1) -> None:
        key = material_id or "unknown"
        self.counts[key] = self.counts.get(key, 0) + amount

    def merge(self, other: "MaterialSummary") -> None:
        for material, count in other.counts.items():
            self.add(material, count)


@dataclass(frozen=True)
class PreviewPiece:
    piece: Piece
    state: str = "valid"
    message: str = ""


@dataclass
class Preview:
    source_mod: str
    pieces: list[PreviewPiece] = field(default_factory=list)
    status: str = "valid"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def material_summary(self) -> MaterialSummary:
        summary = MaterialSummary()
        for item in self.pieces:
            summary.add(item.piece.material_id)
        return summary

    def add(self, piece: Piece, state: str = "valid", message: str = "") -> None:
        self.pieces.append(PreviewPiece(piece, state, message))
        if state == "blocked":
            self.status = "blocked"
            self.errors.append(message or "blocked piece")
        elif state in ("warning", "unsupported") and self.status == "valid":
            self.status = "warning"
            self.warnings.append(message or state)
