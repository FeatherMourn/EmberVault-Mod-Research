"""Game-independent deterministic voxel shape and payload generation.

The byte order intentionally mirrors the Architect Toolkit Lua generator: y is
the outer loop, then z, then x; each voxel is one LSB-first bit.  This module
has no Enshrouded or process/runtime dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Callable, Iterable, Iterator, Mapping, Sequence

Coord = tuple[int, int, int]
Dimensions = tuple[int, int, int]
Predicate = Callable[[int, int, int], bool]


def _dims(dimensions: Sequence[int]) -> Dimensions:
    if len(dimensions) != 3:
        raise ValueError("dimensions must contain x, y and z")
    result = tuple(int(v) for v in dimensions)
    if any(v <= 0 for v in result):
        raise ValueError("dimensions must be positive")
    return result  # type: ignore[return-value]


@dataclass(frozen=True)
class VoxelSet:
    """An immutable bounded occupancy set in zero-based x/y/z coordinates."""

    dimensions: Dimensions
    occupied: frozenset[Coord]

    def __post_init__(self) -> None:
        dimensions = _dims(self.dimensions)
        for x, y, z in self.occupied:
            if not (0 <= x < dimensions[0] and 0 <= y < dimensions[1] and 0 <= z < dimensions[2]):
                raise ValueError(f"voxel {(x, y, z)} lies outside {dimensions}")

    @property
    def occupied_count(self) -> int:
        return len(self.occupied)

    @property
    def payload(self) -> bytes:
        return compress_occupancy(self.dimensions, self.occupied)

    def bounds(self) -> tuple[Coord, Coord] | None:
        if not self.occupied:
            return None
        xs = [p[0] for p in self.occupied]
        ys = [p[1] for p in self.occupied]
        zs = [p[2] for p in self.occupied]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def iter_coordinates(dimensions: Sequence[int]) -> Iterator[Coord]:
    """Yield coordinates in the same order used by the Lua compressor."""
    sx, sy, sz = _dims(dimensions)
    for y in range(sy):
        for z in range(sz):
            for x in range(sx):
                yield x, y, z


def occupancy(dimensions: Sequence[int], predicate: Predicate) -> VoxelSet:
    dims = _dims(dimensions)
    points = frozenset((x, y, z) for x, y, z in iter_coordinates(dims) if predicate(x, y, z))
    return VoxelSet(dims, points)


def compress_occupancy(dimensions: Sequence[int], occupied: Iterable[Coord]) -> bytes:
    """Pack occupancy LSB-first, matching ``compressBlueprint`` in mod.lua."""
    dims = _dims(dimensions)
    points = set(occupied)
    total = dims[0] * dims[1] * dims[2]
    output = bytearray((total + 7) // 8)
    for index, point in enumerate(iter_coordinates(dims)):
        if point in points:
            output[index // 8] |= 1 << (index % 8)
    return bytes(output)


def _center(value: int) -> float:
    return (value - 1) / 2.0


def hollow_square(dimensions: Sequence[int], thickness: int = 1) -> VoxelSet:
    """A horizontal rectangular perimeter, repeated over all y layers."""
    sx, sy, sz = _dims(dimensions)
    if not 1 <= thickness <= min(sx, sz):
        raise ValueError("thickness must fit the x/z footprint")
    return occupancy((sx, sy, sz), lambda x, y, z: (
        x < thickness or x >= sx - thickness or z < thickness or z >= sz - thickness
    ))


def hollow_cube(dimensions: Sequence[int], thickness: int = 1) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    if not 1 <= thickness <= min(sx, sy, sz):
        raise ValueError("thickness must fit all dimensions")
    return occupancy((sx, sy, sz), lambda x, y, z: (
        x < thickness or x >= sx - thickness or
        y < thickness or y >= sy - thickness or
        z < thickness or z >= sz - thickness
    ))


def plus_cross(dimensions: Sequence[int]) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    center_x = (sx - 1) // 2
    center_z = (sz - 1) // 2
    return occupancy((sx, sy, sz), lambda x, y, z: x == center_x or z == center_z)


def diagonal_cross(dimensions: Sequence[int]) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    if sx != sz:
        raise ValueError("diagonal_cross currently requires a square x/z footprint")
    return occupancy((sx, sy, sz), lambda x, y, z: x == z or x + z == sx - 1)


def diamond(dimensions: Sequence[int]) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    cx, cz = _center(sx), _center(sz)
    radius = min(sx, sz) / 2.0 - 0.5
    return occupancy((sx, sy, sz), lambda x, y, z: abs(x - cx) + abs(z - cz) <= radius)


def architect_stairs(dimensions: Sequence[int]) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    return occupancy((sx, sy, sz), lambda x, y, z: y < (((x + 1) * sy) // sx))


def stepped_pyramid(dimensions: Sequence[int]) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    max_inset = (min(sx, sz) - 1) // 2
    def pred(x: int, y: int, z: int) -> bool:
        inset = (y * (max_inset + 1)) // sy
        return inset <= x < sx - inset and inset <= z < sz - inset
    return occupancy((sx, sy, sz), pred)


def archway(dimensions: Sequence[int]) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    return occupancy((sx, sy, sz), lambda x, y, z: x == 0 or x == sx - 1 or y == sy - 1)


def filled_circle(dimensions: Sequence[int], radius: float | None = None) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    r = min(sx, sz) / 2.0 if radius is None else float(radius)
    if r < 0:
        raise ValueError("radius must be non-negative")
    cx, cz = _center(sx), _center(sz)
    rr = r * r
    return occupancy((sx, sy, sz), lambda x, y, z: (
        (x - cx) ** 2 + (z - cz) ** 2 <= rr
    ))


def ring(dimensions: Sequence[int], outer_radius: float | None = None, thickness: float = 1.5) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    outer = min(sx, sz) / 2.0 if outer_radius is None else float(outer_radius)
    inner = outer - float(thickness)
    if outer < 0 or inner < 0:
        raise ValueError("ring radii must be non-negative")
    cx, cz = _center(sx), _center(sz)
    outer_sq, inner_sq = outer * outer, inner * inner
    return occupancy((sx, sy, sz), lambda x, y, z: (
        inner_sq <= (x - cx) ** 2 + (z - cz) ** 2 <= outer_sq
    ))


def filled_cylinder(
    dimensions: Sequence[int],
    radius: float | None = None,
    axis: str = "y",
    height: int | None = None,
) -> VoxelSet:
    """Fill a cylinder along x, y or z, centered on the other two axes."""
    sx, sy, sz = _dims(dimensions)
    axis = axis.lower()
    if axis not in {"x", "y", "z"}:
        raise ValueError("axis must be x, y or z")
    axis_length = {"x": sx, "y": sy, "z": sz}[axis]
    if height is None:
        height = axis_length
    height = int(height)
    if not 1 <= height <= axis_length:
        raise ValueError("height must fit the selected axis")
    axis_start = (axis_length - height) // 2
    axis_end = axis_start + height
    radial = {"x": (sy, sz), "y": (sx, sz), "z": (sx, sy)}[axis]
    r = min(radial) / 2.0 if radius is None else float(radius)
    if r < 0:
        raise ValueError("radius must be non-negative")
    c0, c1 = _center(radial[0]), _center(radial[1])
    rr = r * r
    if axis == "x":
        return occupancy((sx, sy, sz), lambda x, y, z: axis_start <= x < axis_end and (y-c0)**2 + (z-c1)**2 <= rr)
    if axis == "y":
        return occupancy((sx, sy, sz), lambda x, y, z: axis_start <= y < axis_end and (x-c0)**2 + (z-c1)**2 <= rr)
    return occupancy((sx, sy, sz), lambda x, y, z: axis_start <= z < axis_end and (x-c0)**2 + (y-c1)**2 <= rr)


def hollow_cylinder(
    dimensions: Sequence[int],
    outer_radius: float | None = None,
    thickness: float = 1.5,
    axis: str = "y",
    height: int | None = None,
) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    axis = axis.lower()
    radial = {"x": (sy, sz), "y": (sx, sz), "z": (sx, sy)}.get(axis)
    if radial is None:
        raise ValueError("axis must be x, y or z")
    axis_length = {"x": sx, "y": sy, "z": sz}[axis]
    if height is None:
        height = axis_length
    height = int(height)
    if not 1 <= height <= axis_length:
        raise ValueError("height must fit the selected axis")
    axis_start = (axis_length - height) // 2
    axis_end = axis_start + height
    outer = min(radial) / 2.0 if outer_radius is None else float(outer_radius)
    inner = outer - float(thickness)
    if inner < 0:
        raise ValueError("thickness exceeds radius")
    c0, c1 = _center(radial[0]), _center(radial[1])
    outer_sq, inner_sq = outer * outer, inner * inner
    if axis == "x":
        return occupancy((sx, sy, sz), lambda x, y, z: axis_start <= x < axis_end and inner_sq <= (y-c0)**2 + (z-c1)**2 <= outer_sq)
    if axis == "y":
        return occupancy((sx, sy, sz), lambda x, y, z: axis_start <= y < axis_end and inner_sq <= (x-c0)**2 + (z-c1)**2 <= outer_sq)
    return occupancy((sx, sy, sz), lambda x, y, z: axis_start <= z < axis_end and inner_sq <= (x-c0)**2 + (y-c1)**2 <= outer_sq)


def sphere(dimensions: Sequence[int], radius: float | None = None) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    r = min(sx, sy, sz) / 2.0 if radius is None else float(radius)
    if r < 0:
        raise ValueError("radius must be non-negative")
    cx, cy, cz = _center(sx), _center(sy), _center(sz)
    rr = r * r
    return occupancy((sx, sy, sz), lambda x, y, z: (
        (x-cx)**2 + (y-cy)**2 + (z-cz)**2 <= rr
    ))


def baseline_shapes() -> Mapping[str, VoxelSet]:
    """The twelve CODE-0015 Architect shape definitions, matching src/mod.lua."""
    return {
        "hollow_square_4m": hollow_square((8, 1, 8)),
        "filled_circle_4m": filled_circle((8, 1, 8)),
        "ring_4m": ring((8, 1, 8)),
        "cross_4m": plus_cross((8, 1, 8)),
        "diamond_4m": diamond((8, 1, 8)),
        "diagonal_cross_4m": diagonal_cross((8, 1, 8)),
        "sphere_2m": sphere((4, 4, 4)),
        "filled_cylinder_2m": filled_cylinder((4, 4, 4)),
        "hollow_cube_2m": hollow_cube((4, 4, 4)),
        "stairs_2m": architect_stairs((4, 4, 4)),
        "pyramid_2m": stepped_pyramid((4, 4, 4)),
        "archway_2m": archway((4, 4, 4)),
    }


def shape_payload_report(shape: VoxelSet) -> dict[str, object]:
    return {
        "dimensions": list(shape.dimensions),
        "occupiedVoxelCount": shape.occupied_count,
        "compressedByteCount": len(shape.payload),
        "payloadHex": shape.payload.hex(),
        "bounds": None if shape.bounds() is None else [list(v) for v in shape.bounds()],
    }


# ---------------------------------------------------------------------------
# Shape Engine v2 primitives. These operate only on Python coordinate sets.

def _filled_or_shell(dimensions: Dimensions, predicate: Predicate, hollow: bool = False, thickness: int = 1) -> VoxelSet:
    if not hollow:
        return occupancy(dimensions, predicate)
    # Keep a voxel when it is in the shape and has a neighbor outside the
    # shape within the requested Chebyshev shell thickness.
    sx, sy, sz = dimensions
    base = {(x, y, z) for x, y, z in iter_coordinates(dimensions) if predicate(x, y, z)}
    if thickness < 1:
        raise ValueError("thickness must be positive")
    shell = set()
    for point in base:
        x, y, z = point
        for d in range(1, thickness + 1):
            if any((x + dx, y + dy, z + dz) not in base
                   for dx in (-d, 0, d) for dy in (-d, 0, d) for dz in (-d, 0, d)
                   if (dx, dy, dz) != (0, 0, 0)):
                shell.add(point)
                break
    return VoxelSet(dimensions, frozenset(shell))


def line(dimensions: Sequence[int], start: Coord, end: Coord, thickness: int = 1) -> VoxelSet:
    dims = _dims(dimensions)
    if thickness < 1:
        raise ValueError("thickness must be positive")
    x0, y0, z0 = start; x1, y1, z1 = end
    steps = max(abs(x1-x0), abs(y1-y0), abs(z1-z0))
    points = set()
    for i in range(steps + 1):
        t = 0 if steps == 0 else i / steps
        cx, cy, cz = round(x0 + (x1-x0)*t), round(y0 + (y1-y0)*t), round(z0 + (z1-z0)*t)
        for dx in range(-thickness+1, thickness):
            for dy in range(-thickness+1, thickness):
                for dz in range(-thickness+1, thickness):
                    p = (cx+dx, cy+dy, cz+dz)
                    if 0 <= p[0] < dims[0] and 0 <= p[1] < dims[1] and 0 <= p[2] < dims[2]: points.add(p)
    return VoxelSet(dims, frozenset(points))


def wall(dimensions: Sequence[int], axis: str = "z", hollow: bool = False, thickness: int = 1) -> VoxelSet:
    sx, sy, sz = _dims(dimensions); axis = axis.lower()
    if axis == "x": pred = lambda x,y,z: x == sx // 2
    elif axis == "y": pred = lambda x,y,z: y == sy // 2
    elif axis == "z": pred = lambda x,y,z: z == sz // 2
    else: raise ValueError("axis must be x, y or z")
    return _filled_or_shell((sx,sy,sz), pred, hollow, thickness)


def floor(dimensions: Sequence[int], level: int | None = None, hollow: bool = False, thickness: int = 1) -> VoxelSet:
    sx, sy, sz = _dims(dimensions); level = sy // 2 if level is None else int(level)
    if not 0 <= level < sy: raise ValueError("floor level outside dimensions")
    return _filled_or_shell((sx,sy,sz), lambda x,y,z: y == level, hollow, thickness)


def rectangle(dimensions: Sequence[int], filled: bool = True, thickness: int = 1) -> VoxelSet:
    sx, sy, sz = _dims(dimensions)
    pred = (lambda x,y,z: True) if filled else (lambda x,y,z: x < thickness or x >= sx-thickness or z < thickness or z >= sz-thickness)
    return occupancy((sx,sy,sz), pred)


def box(dimensions: Sequence[int], filled: bool = True, thickness: int = 1) -> VoxelSet:
    return occupancy(_dims(dimensions), lambda x,y,z: True) if filled else hollow_cube(dimensions, thickness)


def ellipse(dimensions: Sequence[int], radii: tuple[float, float] | None = None, hollow: bool = False, thickness: int = 1) -> VoxelSet:
    sx, sy, sz = _dims(dimensions); rx, rz = radii or (sx/2.0, sz/2.0); cx, cz = _center(sx), _center(sz)
    pred = lambda x,y,z: ((x-cx)/rx)**2 + ((z-cz)/rz)**2 <= 1.0
    return _filled_or_shell((sx,sy,sz), pred, hollow, thickness)


def ellipsoid(dimensions: Sequence[int], radii: tuple[float, float, float] | None = None, hollow: bool = False, thickness: int = 1) -> VoxelSet:
    sx, sy, sz = _dims(dimensions); rx, ry, rz = radii or (sx/2.0, sy/2.0, sz/2.0); cx, cy, cz = _center(sx), _center(sy), _center(sz)
    pred = lambda x,y,z: ((x-cx)/rx)**2 + ((y-cy)/ry)**2 + ((z-cz)/rz)**2 <= 1.0
    return _filled_or_shell((sx,sy,sz), pred, hollow, thickness)


def dome(dimensions: Sequence[int], radii: tuple[float, float, float] | None = None, hollow: bool = False, thickness: int = 1) -> VoxelSet:
    sx, sy, sz = _dims(dimensions); cy = (sy - 1) / 2.0
    full = ellipsoid((sx,sy,sz), radii, hollow, thickness)
    return VoxelSet(full.dimensions, frozenset(p for p in full.occupied if p[1] >= cy))


def cone(dimensions: Sequence[int], axis: str = "y", hollow: bool = False, thickness: int = 1) -> VoxelSet:
    sx, sy, sz = _dims(dimensions); axis = axis.lower(); axis_len = {"x":sx,"y":sy,"z":sz}.get(axis)
    if axis_len is None: raise ValueError("axis must be x, y or z")
    radial = {"x":(sy,sz),"y":(sx,sz),"z":(sx,sy)}[axis]; c0,c1 = _center(radial[0]),_center(radial[1]); maxr=min(radial)/2.0
    def pred(x,y,z):
        a = {"x":x,"y":y,"z":z}[axis]; fraction = 1.0 - a / max(1, axis_len-1); r = maxr * fraction
        q0,q1 = ({"x":(y,z),"y":(x,z),"z":(x,y)}[axis]); return (q0-c0)**2 + (q1-c1)**2 <= r*r
    return _filled_or_shell((sx,sy,sz), pred, hollow, thickness)


def arch(dimensions: Sequence[int], axis: str = "z", thickness: int = 1) -> VoxelSet:
    sx, sy, sz = _dims(dimensions); axis = axis.lower();
    if axis != "z": raise ValueError("arch currently uses a z-normal plane")
    cx, radius = (sx-1)/2.0, min(sx, sy)/2.0
    def pred(x,y,z):
        dx, dy = x-cx, y
        return y == 0 or (dx*dx + (dy-radius)**2 <= radius*radius and y >= radius)
    return occupancy((sx,sy,sz), pred)


def ramp(dimensions: Sequence[int], axis: str = "x") -> VoxelSet:
    sx, sy, sz = _dims(dimensions); axis = axis.lower(); length = {"x":sx,"y":sy,"z":sz}.get(axis)
    if length is None: raise ValueError("axis must be x, y or z")
    def pred(x,y,z):
        along = {"x":x,"y":y,"z":z}[axis]; height = int((along + 1) * sy / length)
        return y < height
    return occupancy((sx,sy,sz), pred)


def stairs(dimensions: Sequence[int], axis: str = "x") -> VoxelSet:
    sx, sy, sz = _dims(dimensions); axis = axis.lower(); length = {"x":sx,"y":sy,"z":sz}.get(axis)
    if length is None: raise ValueError("axis must be x, y or z")
    def pred(x,y,z):
        along = {"x":x,"y":y,"z":z}[axis]; return y <= int((along + 1) * sy / length)
    return occupancy((sx,sy,sz), pred)


def spiral_stairs(dimensions: Sequence[int], turns: float = 1.0, thickness: int = 1) -> VoxelSet:
    sx, sy, sz = _dims(dimensions); cx, cz = _center(sx), _center(sz); radius = min(sx,sz)/2.0 - 1
    points=set(); steps=max(1, sy*16)
    for i in range(steps):
        y = min(sy-1, i * (sy-1) / max(1, steps-1)); angle = turns*2*3.141592653589793*i/max(1,steps-1)
        x,z=round(cx+radius*__import__('math').cos(angle)),round(cz+radius*__import__('math').sin(angle))
        for dx in range(-thickness+1,thickness):
            for dz in range(-thickness+1,thickness):
                p=(x+dx,round(y),z+dz)
                if 0<=p[0]<sx and 0<=p[1]<sy and 0<=p[2]<sz: points.add(p)
    return VoxelSet((sx,sy,sz), frozenset(points))


def tunnel(dimensions: Sequence[int], axis: str = "x", thickness: float = 1.5) -> VoxelSet:
    return hollow_cylinder(dimensions, thickness=thickness, axis=axis)


def road_strip(dimensions: Sequence[int], width: int | None = None, axis: str = "x") -> VoxelSet:
    sx, sy, sz = _dims(dimensions); axis = axis.lower(); width = width or (sz if axis == "x" else sx)
    if axis == "x": pred=lambda x,y,z: y == sy//2 and abs(z-(sz-1)/2) < width/2
    elif axis == "z": pred=lambda x,y,z: y == sy//2 and abs(x-(sx-1)/2) < width/2
    else: raise ValueError("road axis must be x or z")
    return occupancy((sx,sy,sz), pred)


def transform_voxel_set(voxels: VoxelSet, rotation: tuple[int,int,int] = (0,0,0), mirror: tuple[bool,bool,bool] = (False,False,False), translation: Coord = (0,0,0)) -> VoxelSet:
    """Apply axis mirrors and 90-degree rotations, then a non-negative translation."""
    points=set(voxels.occupied); dims=voxels.dimensions
    for axis, enabled in enumerate(mirror):
        if enabled:
            points = {(dims[0]-1-x if axis==0 else x, dims[1]-1-y if axis==1 else y, dims[2]-1-z if axis==2 else z) for x,y,z in points}
    for axis, turns in enumerate(rotation):
        for _ in range(turns % 4):
            sx,sy,sz=dims
            if axis==0: points={(x, sz-1-z, y) for x,y,z in points}; dims=(sx,sz,sy)
            elif axis==1: points={(z, y, sx-1-x) for x,y,z in points}; dims=(sz,sy,sx)
            else: points={(sy-1-y, x, z) for x,y,z in points}; dims=(sy,sx,sz)
    tx,ty,tz=translation
    if min(tx,ty,tz) < 0: raise ValueError("translation must be non-negative for bounded VoxelSet")
    points={(x+tx,y+ty,z+tz) for x,y,z in points}; dims=(dims[0]+tx,dims[1]+ty,dims[2]+tz)
    return VoxelSet(dims, frozenset(points))


def make_shape(name: str, dimensions: Sequence[int], **parameters: object) -> VoxelSet:
    table = {"line": line, "wall": wall, "floor": floor, "rectangle": rectangle, "box": box, "ellipse": ellipse, "ellipsoid": ellipsoid, "dome": dome, "cone": cone, "arch": arch, "ramp": ramp, "stairs": stairs, "spiral_stairs": spiral_stairs, "tunnel": tunnel, "road_strip": road_strip}
    if name not in table: raise ValueError(f"unknown shape {name}")
    return table[name](dimensions, **parameters)  # type: ignore[arg-type]
