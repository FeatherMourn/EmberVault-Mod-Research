from __future__ import annotations

from dataclasses import dataclass

from construction_sdk.models import Blueprint, Coordinate, Piece
from construction_sdk.operations import Operation, SimulatedWorld


@dataclass(frozen=True)
class Difference:
    position: Coordinate
    expected: Piece | None
    actual: Piece | None
    classification: str
    severity: str = "repairable"


@dataclass
class RestorationPlan:
    differences: list[Difference]
    selected: list[Difference]
    substitutions: dict[str, str]
    status: str = "planned"

    @property
    def material_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for difference in self.selected:
            if difference.expected is None:
                continue
            material = difference.expected.material_id or "unknown"
            material = self.substitutions.get(material, material)
            counts[material] = counts.get(material, 0) + 1
        return dict(sorted(counts.items()))


def compare(reference: Blueprint, world: SimulatedWorld, anchor: Coordinate = Coordinate(0, 0, 0)) -> list[Difference]:
    expected = {p.position.add(anchor): p.moved(p.position.add(anchor)) for p in reference.pieces}
    positions = set(expected) | set(world.pieces)
    differences = []
    for position in sorted(positions):
        wanted, actual = expected.get(position), world.inspect(position)
        if wanted is None:
            classification, severity = "unexpected_piece", "warning"
        elif actual is None:
            classification, severity = "missing_piece", "repairable"
        elif wanted.resource_id != actual.resource_id:
            classification, severity = "wrong_resource", "warning"
        elif wanted.material_id != actual.material_id:
            classification, severity = "wrong_material", "repairable"
        elif wanted.orientation != actual.orientation:
            classification, severity = "wrong_orientation", "repairable"
        else:
            continue
        differences.append(Difference(position, wanted, actual, classification, severity))
    return differences


def make_plan(differences: list[Difference], policy: str = "missing_only",
              substitutions: dict[str, str] | None = None) -> RestorationPlan:
    substitutions = dict(substitutions or {})
    allowed = {
        "missing_only": {"missing_piece"},
        "safe_differences": {"missing_piece", "wrong_material", "wrong_orientation"},
        "repair_resources": {"missing_piece", "wrong_resource", "wrong_material", "wrong_orientation"},
    }
    if policy not in allowed:
        raise ValueError("unsupported restoration policy")
    selected = [d for d in differences if d.classification in allowed[policy]]
    return RestorationPlan(differences, selected, substitutions)


def apply_plan(world: SimulatedWorld, plan: RestorationPlan) -> dict[Coordinate, Piece | None]:
    before = {difference.position: world.inspect(difference.position)
              for difference in plan.selected if difference.expected is not None}
    operation = apply_plan_operation(world, plan)
    return before


def apply_plan_operation(world: SimulatedWorld, plan: RestorationPlan) -> Operation:
    """Apply a restoration plan and return a shared undoable operation."""
    before: dict[Coordinate, Piece | None] = {}
    after: dict[Coordinate, Piece] = {}
    for difference in plan.selected:
        if difference.expected is None:
            continue
        before[difference.position] = world.inspect(difference.position)
        expected = difference.expected
        material = plan.substitutions.get(expected.material_id or "unknown", expected.material_id)
        replacement = expected.moved(difference.position) if material == expected.material_id else Piece(
            difference.position, expected.resource_id, material, expected.orientation, dict(expected.properties))
        world.put(replacement)
        after[difference.position] = replacement
    plan.status = "applied"
    return Operation("restoration", {p: piece for p, piece in before.items() if piece is not None}, after)
