from __future__ import annotations

from dataclasses import dataclass

from construction_sdk.models import Blueprint, Coordinate, Piece


@dataclass(frozen=True)
class WandLimits:
    max_pieces: int = 32
    max_distance: int = 16


@dataclass(frozen=True)
class WandTarget:
    position: Coordinate
    pinned: bool = False

    def pin(self) -> "WandTarget":
        return WandTarget(self.position, True)


def _validate_count(count: int, limits: WandLimits) -> None:
    if count < 1 or count > limits.max_pieces or count > limits.max_distance:
        raise ValueError("wand operation exceeds configured limits")


def row(name: str, target: WandTarget, count: int, prototype: Piece,
        axis: str = "x", limits: WandLimits = WandLimits()) -> Blueprint:
    if axis not in ("x", "y", "z"):
        raise ValueError("axis must be x, y, or z")
    _validate_count(count, limits)
    pieces = []
    for i in range(count):
        offset = Coordinate(i if axis == "x" else 0, i if axis == "y" else 0, i if axis == "z" else 0)
        pieces.append(prototype.moved(target.position.add(offset)))
    return Blueprint(name, pieces, source_type="procedural", anchor=target.position)


def column(name: str, target: WandTarget, height: int, prototype: Piece,
           limits: WandLimits = WandLimits()) -> Blueprint:
    return row(name, target, height, prototype, axis="y", limits=limits)


def plane(name: str, target: WandTarget, width: int, depth: int, prototype: Piece,
          limits: WandLimits = WandLimits()) -> Blueprint:
    if width < 1 or depth < 1 or width * depth > limits.max_pieces:
        raise ValueError("wand plane exceeds configured limits")
    pieces = [prototype.moved(target.position.add(Coordinate(x, 0, z)))
              for z in range(depth) for x in range(width)]
    return Blueprint(name, pieces, source_type="procedural", anchor=target.position)
