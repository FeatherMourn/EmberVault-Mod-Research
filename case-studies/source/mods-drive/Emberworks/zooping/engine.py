from __future__ import annotations

from dataclasses import dataclass

from construction_sdk.models import Blueprint, Coordinate, Piece


@dataclass(frozen=True)
class ZoopOperation:
    mode: str
    blueprint: Blueprint
    requested: int
    warnings: tuple[str, ...] = ()


def _piece(position: Coordinate, prototype: Piece) -> Piece:
    return prototype.moved(position)


def line(name: str, origin: Coordinate, length: int, prototype: Piece, axis: str = "x") -> ZoopOperation:
    if length < 1:
        raise ValueError("length must be positive")
    if axis not in ("x", "y", "z"):
        raise ValueError("axis must be x, y, or z")
    pieces = []
    for i in range(length):
        offset = Coordinate(i if axis == "x" else 0, i if axis == "y" else 0, i if axis == "z" else 0)
        pieces.append(_piece(origin.add(offset), prototype))
    return ZoopOperation("line", Blueprint(name, pieces, source_type="procedural", anchor=origin), length)


def wall(name: str, origin: Coordinate, width: int, height: int, prototype: Piece, axis: str = "x") -> ZoopOperation:
    if width < 1 or height < 1:
        raise ValueError("width and height must be positive")
    if axis not in ("x", "z"):
        raise ValueError("wall axis must be x or z")
    pieces = []
    for y in range(height):
        for i in range(width):
            offset = Coordinate(i if axis == "x" else 0, y, i if axis == "z" else 0)
            pieces.append(_piece(origin.add(offset), prototype))
    return ZoopOperation("wall", Blueprint(name, pieces, source_type="procedural", anchor=origin), len(pieces))


def floor(name: str, origin: Coordinate, width: int, depth: int, prototype: Piece) -> ZoopOperation:
    if width < 1 or depth < 1:
        raise ValueError("width and depth must be positive")
    pieces = [_piece(origin.add(Coordinate(x, 0, z)), prototype)
              for z in range(depth) for x in range(width)]
    return ZoopOperation("floor", Blueprint(name, pieces, source_type="procedural", anchor=origin), len(pieces))


def column(name: str, origin: Coordinate, height: int, prototype: Piece) -> ZoopOperation:
    operation = line(name, origin, height, prototype, axis="y")
    return ZoopOperation("column", operation.blueprint, height)


def bridge(name: str, origin: Coordinate, length: int, width: int, prototype: Piece, axis: str = "x") -> ZoopOperation:
    if length < 1 or width < 1:
        raise ValueError("length and width must be positive")
    pieces = []
    for along in range(length):
        for across in range(width):
            offset = Coordinate(along if axis == "x" else across, 0, across if axis == "x" else along)
            pieces.append(_piece(origin.add(offset), prototype))
    return ZoopOperation("bridge", Blueprint(name, pieces, source_type="procedural", anchor=origin), len(pieces))


def repeat(name: str, source: Blueprint, count: int, spacing: Coordinate) -> ZoopOperation:
    if count < 1:
        raise ValueError("count must be positive")
    pieces = []
    for index in range(count):
        offset = Coordinate(spacing.x * index, spacing.y * index, spacing.z * index)
        pieces.extend(p.moved(p.position.add(offset)) for p in source.pieces)
    return ZoopOperation("repeat", Blueprint(name, pieces, source_type="procedural", anchor=source.anchor), len(pieces))
