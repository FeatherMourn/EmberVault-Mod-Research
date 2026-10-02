from __future__ import annotations

from dataclasses import dataclass, field

from construction_sdk.models import Blueprint, Coordinate, Piece


SHAPES = {
    "framed_cube", "framed_slab", "framed_panel", "framed_wall", "framed_slope",
    "framed_corner", "framed_pillar", "framed_stairs", "framed_fence", "framed_gate",
}


@dataclass(frozen=True)
class AppearanceProfile:
    parent_resource_id: str
    material_id: str
    inherit: frozenset[str] = frozenset({"texture", "color", "surface_type"})


@dataclass
class ShapeCatalog:
    shapes: set[str] = field(default_factory=lambda: set(SHAPES))

    def require(self, shape_id: str) -> None:
        if shape_id not in self.shapes:
            raise ValueError(f"unsupported framed shape: {shape_id}")


@dataclass
class CompatibilityRegistry:
    compatible: dict[str, set[str]] = field(default_factory=dict)

    def register(self, parent_resource_id: str, shapes: set[str]) -> None:
        self.compatible[parent_resource_id] = set(shapes)

    def supports(self, parent_resource_id: str, shape_id: str) -> bool:
        return shape_id in self.compatible.get(parent_resource_id, set())


@dataclass(frozen=True)
class FramedPiece:
    position: Coordinate
    shape_id: str
    appearance: AppearanceProfile
    orientation: int = 0

    def to_piece(self, catalog: ShapeCatalog, registry: CompatibilityRegistry) -> Piece:
        catalog.require(self.shape_id)
        if not registry.supports(self.appearance.parent_resource_id, self.shape_id):
            raise ValueError(f"parent does not support shape: {self.appearance.parent_resource_id}/{self.shape_id}")
        return Piece(self.position, f"framed:{self.shape_id}", self.appearance.material_id,
                     self.orientation, {"parent_resource_id": self.appearance.parent_resource_id,
                                         "inherit": sorted(self.appearance.inherit)})


def to_blueprint(name: str, pieces: list[FramedPiece], catalog: ShapeCatalog,
                 registry: CompatibilityRegistry) -> Blueprint:
    """Export a validated framed assembly through the shared Blueprint contract."""
    sdk_pieces = [piece.to_piece(catalog, registry) for piece in pieces]
    anchor = min((piece.position for piece in sdk_pieces), default=Coordinate(0, 0, 0))
    return Blueprint(name, sdk_pieces, source_type="framed_architecture", anchor=anchor,
                     metadata={"shapes": sorted({piece.shape_id for piece in pieces}),
                               "parents": sorted({piece.appearance.parent_resource_id for piece in pieces})})
