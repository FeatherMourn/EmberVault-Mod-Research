"""Offline partitioning of voxel sets into bounded execution tiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

try:  # Works both as a package and when the folder is on PYTHONPATH.
    from .architect_voxel import Coord, Dimensions, VoxelSet, compress_occupancy, _dims
except ImportError:  # pragma: no cover - direct script/test invocation
    from architect_voxel import Coord, Dimensions, VoxelSet, compress_occupancy, _dims


@dataclass(frozen=True)
class VoxelTile:
    origin: Coord
    dimensions: Dimensions
    occupied: frozenset[Coord]

    @property
    def is_empty(self) -> bool:
        return not self.occupied

    @property
    def payload(self) -> bytes:
        return compress_occupancy(self.dimensions, self.occupied)

    def as_dict(self) -> dict[str, object]:
        return {
            "origin": list(self.origin),
            "dimensions": list(self.dimensions),
            "occupiedVoxelCount": len(self.occupied),
            "occupied": [list(p) for p in sorted(self.occupied, key=lambda p: (p[1], p[2], p[0]))],
            "payloadHex": self.payload.hex(),
            "empty": self.is_empty,
        }

    def global_coordinates(self) -> frozenset[Coord]:
        return frozenset((x + self.origin[0], y + self.origin[1], z + self.origin[2]) for x, y, z in self.occupied)

    def bounding_box(self) -> tuple[Coord, Coord] | None:
        if not self.occupied:
            return None
        xs=[p[0] for p in self.occupied]; ys=[p[1] for p in self.occupied]; zs=[p[2] for p in self.occupied]
        return ((min(xs)+self.origin[0], min(ys)+self.origin[1], min(zs)+self.origin[2]),
                (max(xs)+self.origin[0], max(ys)+self.origin[1], max(zs)+self.origin[2]))


def plan_voxels(
    dimensions: Sequence[int],
    occupied: Iterable[Coord],
    tile_dimensions: Sequence[int] = (8, 8, 8),
) -> list[VoxelTile]:
    """Partition a bounded set into complete tile footprints, including empty tiles."""
    dims = _dims(dimensions)
    td = _dims(tile_dimensions)
    points = set(occupied)
    for x, y, z in points:
        if not (0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]):
            raise ValueError(f"voxel {(x, y, z)} lies outside {dims}")
    nx = (dims[0] + td[0] - 1) // td[0]
    ny = (dims[1] + td[1] - 1) // td[1]
    nz = (dims[2] + td[2] - 1) // td[2]
    tiles: list[VoxelTile] = []
    for iy in range(ny):
        for iz in range(nz):
            for ix in range(nx):
                origin = (ix * td[0], iy * td[1], iz * td[2])
                actual = (
                    min(td[0], dims[0] - origin[0]),
                    min(td[1], dims[1] - origin[1]),
                    min(td[2], dims[2] - origin[2]),
                )
                local = frozenset((x-origin[0], y-origin[1], z-origin[2])
                                  for x, y, z in points
                                  if origin[0] <= x < origin[0]+actual[0]
                                  and origin[1] <= y < origin[1]+actual[1]
                                  and origin[2] <= z < origin[2]+actual[2])
                tiles.append(VoxelTile(origin, actual, local))
    return tiles


def plan_voxel_set(voxels: VoxelSet, tile_dimensions: Sequence[int] = (8, 8, 8)) -> list[VoxelTile]:
    return plan_voxels(voxels.dimensions, voxels.occupied, tile_dimensions)


def resolve_anchor(dimensions: Sequence[int], anchor: str = "min") -> Coord:
    dims = _dims(dimensions); anchor = anchor.lower()
    if anchor in {"min", "origin", "world"}: return (0, 0, 0)
    if anchor == "center": return tuple(-(d // 2) for d in dims)  # type: ignore[return-value]
    raise ValueError("anchor must be min, origin/world, or center")


def detect_overlaps(tiles: Sequence[VoxelTile]) -> list[dict[str, object]]:
    owners: dict[Coord, int] = {}; overlaps=[]
    for index, tile in enumerate(tiles):
        for point in tile.global_coordinates():
            prior = owners.get(point)
            if prior is not None:
                overlaps.append({"coordinate": list(point), "firstTile": prior, "secondTile": index})
            else:
                owners[point] = index
    return overlaps


def estimate_placement_operations(tiles: Sequence[VoxelTile], *, per_tile: int = 1) -> int:
    if per_tile < 0: raise ValueError("per_tile must be non-negative")
    return sum(per_tile for tile in tiles if not tile.is_empty)


def plan_voxels_v2(
    dimensions: Sequence[int],
    occupied: Iterable[Coord],
    tile_dimensions: Sequence[int] = (8, 8, 8),
    *,
    suppress_empty: bool = True,
    anchor: str = "min",
) -> dict[str, object]:
    """V2 plan with stable ordering, transforms, overlap and operation metadata."""
    dims = _dims(dimensions); offset = resolve_anchor(dims, anchor)
    shifted_dims = tuple(d - min(0, offset[i]) for i, d in enumerate(dims))
    shifted = {(x + offset[0] - min(0, offset[0]), y + offset[1] - min(0, offset[1]), z + offset[2] - min(0, offset[2])) for x,y,z in occupied}
    tiles = plan_voxels(shifted_dims, shifted, tile_dimensions)
    if suppress_empty: tiles = [tile for tile in tiles if not tile.is_empty]
    return {
        "dimensions": list(dims), "tileDimensions": list(_dims(tile_dimensions)), "anchor": anchor,
        "emptyChunksSuppressed": suppress_empty, "tiles": [tile.as_dict() for tile in tiles],
        "overlaps": detect_overlaps(tiles), "boundingBoxes": [None if tile.bounding_box() is None else [list(v) for v in tile.bounding_box()] for tile in tiles],
        "estimatedPlacementOperations": estimate_placement_operations(tiles),
    }
