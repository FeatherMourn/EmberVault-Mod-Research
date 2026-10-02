from __future__ import annotations

from dataclasses import dataclass

from construction_sdk.models import Blueprint, Coordinate, Piece, Transform
from construction_sdk.operations import BatchOperation, Operation, SimulatedWorld
from construction_sdk.preview import Preview


@dataclass(frozen=True)
class Selection:
    point_a: Coordinate
    point_b: Coordinate

    @property
    def minimum(self) -> Coordinate:
        return Coordinate(min(self.point_a.x, self.point_b.x), min(self.point_a.y, self.point_b.y), min(self.point_a.z, self.point_b.z))

    @property
    def maximum(self) -> Coordinate:
        return Coordinate(max(self.point_a.x, self.point_b.x), max(self.point_a.y, self.point_b.y), max(self.point_a.z, self.point_b.z))

    @property
    def volume(self) -> int:
        a, b = self.minimum, self.maximum
        return (b.x - a.x + 1) * (b.y - a.y + 1) * (b.z - a.z + 1)

    def contains(self, position: Coordinate) -> bool:
        a, b = self.minimum, self.maximum
        return a.x <= position.x <= b.x and a.y <= position.y <= b.y and a.z <= position.z <= b.z


def copy_selection(name: str, pieces: list[Piece], selection: Selection) -> Blueprint:
    """Copy matching pieces into anchor-relative coordinates."""
    anchor = selection.minimum
    copied = [p.moved(Coordinate(p.position.x - anchor.x, p.position.y - anchor.y, p.position.z - anchor.z))
              for p in pieces if selection.contains(p.position)]
    return Blueprint(name=name, pieces=copied, source_type="manual", anchor=Coordinate(0, 0, 0))


def transform_blueprint(blueprint: Blueprint, transform: Transform) -> Blueprint:
    transform.normalized()
    transformed: list[Piece] = []
    for piece in blueprint.pieces:
        x = piece.position.x - blueprint.anchor.x
        y = piece.position.y - blueprint.anchor.y
        z = piece.position.z - blueprint.anchor.z
        if transform.mirror == "x": x = -x
        if transform.mirror == "y": y = -y
        if transform.mirror == "z": z = -z
        for _ in range(transform.rotation // 90):
            x, z = -z, x
        orientation = (piece.orientation + transform.rotation) % 360
        transformed.append(piece.moved(Coordinate(x, y, z), orientation))
    return Blueprint(name=blueprint.name, pieces=transformed, source_type=blueprint.source_type,
                     blueprint_id=blueprint.blueprint_id, anchor=blueprint.anchor,
                     metadata=dict(blueprint.metadata))


def paste_plan(blueprint: Blueprint, target: Coordinate, world: SimulatedWorld,
               replacement_policy: str = "empty_only") -> tuple[dict[Coordinate, Piece], list[Coordinate]]:
    """Create a non-mutating paste plan and report blocked positions."""
    if replacement_policy not in ("empty_only", "replace_anything", "replace_matching"):
        raise ValueError("unsupported replacement policy")
    planned: dict[Coordinate, Piece] = {}
    blocked: list[Coordinate] = []
    for piece in blueprint.pieces:
        relative = Coordinate(piece.position.x - blueprint.anchor.x,
                              piece.position.y - blueprint.anchor.y,
                              piece.position.z - blueprint.anchor.z)
        position = relative.add(target)
        existing = world.inspect(position)
        if existing is not None:
            if replacement_policy == "empty_only":
                blocked.append(position)
                continue
            if replacement_policy == "replace_matching" and existing.resource_id != piece.resource_id:
                blocked.append(position)
                continue
        planned[position] = piece.moved(position)
    return planned, blocked


def preview_paste(blueprint: Blueprint, target: Coordinate, world: SimulatedWorld,
                  replacement_policy: str = "empty_only") -> Preview:
    planned, blocked = paste_plan(blueprint, target, world, replacement_policy)
    preview = Preview("emberworks.worldwright")
    blocked_set = set(blocked)
    for piece in blueprint.pieces:
        relative = Coordinate(piece.position.x - blueprint.anchor.x,
                              piece.position.y - blueprint.anchor.y,
                              piece.position.z - blueprint.anchor.z)
        position = relative.add(target)
        if position in blocked_set:
            preview.add(piece.moved(position), "blocked", f"collision at {position}")
        else:
            preview.add(piece.moved(position))
    return preview


def commit_plan(world: SimulatedWorld, planned: dict[Coordinate, Piece],
                operation_type: str = "paste") -> Operation:
    before = {position: world.inspect(position) for position in planned if world.inspect(position) is not None}
    for position, piece in planned.items():
        world.put(piece)
    operation = Operation(operation_type, before, dict(planned))
    return operation


def commit_batch(world: SimulatedWorld, plans: list[dict[Coordinate, Piece]],
                 operation_type: str = "batch") -> BatchOperation:
    """Commit several non-mutating plans and expose them as one undoable edit."""
    operations = [commit_plan(world, plan, operation_type) for plan in plans]
    return BatchOperation(operation_type, operations)


def fill(selection: Selection, prototype: Piece) -> Blueprint:
    pieces = []
    minimum, maximum = selection.minimum, selection.maximum
    for y in range(minimum.y, maximum.y + 1):
        for z in range(minimum.z, maximum.z + 1):
            for x in range(minimum.x, maximum.x + 1):
                pieces.append(prototype.moved(Coordinate(x, y, z)))
    return Blueprint("fill", pieces, source_type="procedural", anchor=minimum)


def replace(world: SimulatedWorld, selection: Selection, resource_id: str,
            replacement: Piece) -> Operation:
    before = {}
    after = {}
    for position, piece in list(world.pieces.items()):
        if selection.contains(position) and piece.resource_id == resource_id:
            before[position] = piece
            after[position] = replacement.moved(position)
            world.put(after[position])
    return Operation("replace", before, after)
