from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy
from typing import Iterable

from .models import Coordinate, Piece


class SimulatedWorld:
    """Deterministic offline world used until an Enshrouded adapter is proven."""

    def __init__(self, pieces: Iterable[Piece] = ()):
        self.pieces: dict[Coordinate, Piece] = {p.position: p for p in pieces}

    def snapshot(self) -> dict[Coordinate, Piece]:
        return deepcopy(self.pieces)

    def inspect(self, position: Coordinate) -> Piece | None:
        return self.pieces.get(position)

    def put(self, piece: Piece) -> None:
        self.pieces[piece.position] = piece

    def remove(self, position: Coordinate) -> Piece | None:
        return self.pieces.pop(position, None)


@dataclass
class Operation:
    operation_type: str
    before: dict[Coordinate, Piece]
    after: dict[Coordinate, Piece]
    status: str = "committed"
    conflicts: list[Coordinate] = field(default_factory=list)

    def undo(self, world: SimulatedWorld) -> bool:
        if any(world.inspect(pos) != piece for pos, piece in self.after.items()):
            self.conflicts = [pos for pos, piece in self.after.items() if world.inspect(pos) != piece]
            self.status = "conflicted"
            return False
        for pos in self.after:
            world.remove(pos)
        for piece in self.before.values():
            world.put(piece)
        self.status = "undone"
        return True

    def redo(self, world: SimulatedWorld) -> bool:
        if any(world.inspect(pos) != piece for pos, piece in self.before.items()):
            self.status = "conflicted"
            return False
        for pos in self.before:
            world.remove(pos)
        for piece in self.after.values():
            world.put(piece)
        self.status = "committed"
        return True


@dataclass
class BatchOperation:
    """Several operations presented as one user-visible edit."""

    operation_type: str
    operations: list[Operation]

    def undo(self, world: SimulatedWorld) -> bool:
        undone: list[Operation] = []
        for operation in reversed(self.operations):
            if not operation.undo(world):
                for prior in undone:
                    prior.redo(world)
                return False
            undone.append(operation)
        return True

    def redo(self, world: SimulatedWorld) -> bool:
        redone: list[Operation] = []
        for operation in self.operations:
            if not operation.redo(world):
                for prior in reversed(redone):
                    prior.undo(world)
                return False
            redone.append(operation)
        return True

class OperationHistory:
    """Transactional undo/redo stack shared by construction-facing mods."""

    def __init__(self, limit: int = 256):
        if limit < 1:
            raise ValueError("history limit must be positive")
        self.limit = limit
        self._undo: list[Operation | BatchOperation] = []
        self._redo: list[Operation | BatchOperation] = []

    def push(self, operation: Operation | BatchOperation) -> None:
        self._undo.append(operation)
        del self._undo[:-self.limit]
        self._redo.clear()

    def undo(self, world: SimulatedWorld) -> bool:
        if not self._undo:
            return False
        operation = self._undo[-1]
        if not operation.undo(world):
            return False
        self._undo.pop()
        self._redo.append(operation)
        return True

    def redo(self, world: SimulatedWorld) -> bool:
        if not self._redo:
            return False
        operation = self._redo[-1]
        if not operation.redo(world):
            return False
        self._redo.pop()
        self._undo.append(operation)
        return True

    @property
    def undo_depth(self) -> int:
        return len(self._undo)

    @property
    def redo_depth(self) -> int:
        return len(self._redo)
