"""Pure double-precision transform math for offline structure plans."""
from __future__ import annotations

import math
from itertools import product
from typing import Iterable, Sequence

Vec3 = tuple[float, float, float]
Quat = tuple[float, float, float, float]  # internal XYZW; replay convention unresolved


def _finite(values: Iterable[float]) -> bool:
    try:
        return all(math.isfinite(float(value)) for value in values)
    except TypeError:
        return False


def vec3(value: Sequence[float]) -> Vec3:
    if len(value) != 3 or not _finite(value):
        raise ValueError("expected three finite coordinates")
    return tuple(float(x) for x in value)  # type: ignore[return-value]


def add(a: Sequence[float], b: Sequence[float]) -> Vec3:
    a, b = vec3(a), vec3(b); return tuple(a[i] + b[i] for i in range(3))  # type: ignore[return-value]


def sub(a: Sequence[float], b: Sequence[float]) -> Vec3:
    a, b = vec3(a), vec3(b); return tuple(a[i] - b[i] for i in range(3))  # type: ignore[return-value]


def scale(a: Sequence[float], factor: float) -> Vec3:
    a = vec3(a); factor = float(factor)
    if not math.isfinite(factor): raise ValueError("factor must be finite")
    return tuple(x * factor for x in a)  # type: ignore[return-value]


def quat_normalize(q: Sequence[float]) -> Quat:
    if len(q) != 4 or not _finite(q): raise ValueError("quaternion must contain four finite values")
    norm = math.sqrt(sum(float(x) * float(x) for x in q))
    if norm < 1e-12: raise ValueError("zero quaternion")
    return tuple(float(x) / norm for x in q)  # type: ignore[return-value]


def quat_multiply(a: Sequence[float], b: Sequence[float]) -> Quat:
    x1, y1, z1, w1 = quat_normalize(a); x2, y2, z2, w2 = quat_normalize(b)
    return quat_normalize((w1*x2 + x1*w2 + y1*z2 - z1*y2, w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2, w1*w2 - x1*x2 - y1*y2 - z1*z2))


def quat_conjugate(q: Sequence[float]) -> Quat:
    x, y, z, w = quat_normalize(q); return (-x, -y, -z, w)


def quat_inverse(q: Sequence[float]) -> Quat:
    return quat_conjugate(q)


def quat_to_matrix(q: Sequence[float]) -> tuple[tuple[float, float, float], ...]:
    x, y, z, w = quat_normalize(q)
    return ((1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)), (2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)), (2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)))


def matrix_to_quat(m: Sequence[Sequence[float]]) -> Quat:
    if len(m) != 3 or any(len(row) != 3 for row in m) or not _finite(v for row in m for v in row): raise ValueError("expected finite 3x3 matrix")
    trace = float(m[0][0] + m[1][1] + m[2][2])
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2; w = .25*s; x = (m[2][1]-m[1][2])/s; y = (m[0][2]-m[2][0])/s; z = (m[1][0]-m[0][1])/s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1+m[0][0]-m[1][1]-m[2][2])*2; w=(m[2][1]-m[1][2])/s; x=.25*s; y=(m[0][1]+m[1][0])/s; z=(m[0][2]+m[2][0])/s
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1+m[1][1]-m[0][0]-m[2][2])*2; w=(m[0][2]-m[2][0])/s; x=(m[0][1]+m[1][0])/s; y=.25*s; z=(m[1][2]+m[2][1])/s
    else:
        s = math.sqrt(1+m[2][2]-m[0][0]-m[1][1])*2; w=(m[1][0]-m[0][1])/s; x=(m[0][2]+m[2][0])/s; y=(m[1][2]+m[2][1])/s; z=.25*s
    return quat_normalize((x, y, z, w))


def rotate_point(point: Sequence[float], pivot: Sequence[float], rotation: Sequence[float]) -> Vec3:
    p, c = vec3(point), vec3(pivot); m = quat_to_matrix(rotation); d = sub(p, c)
    return add(c, tuple(sum(m[row][col] * d[col] for col in range(3)) for row in range(3)))


def axis_quaternion(axis: str, degrees: float) -> Quat:
    axis = axis.lower(); radians = math.radians(float(degrees))
    if axis not in {"x", "y", "z"} or not math.isfinite(radians): raise ValueError("axis must be x, y or z and angle finite")
    half = radians / 2; s, c = math.sin(half), math.cos(half)
    return {"x": (s, 0.0, 0.0, c), "y": (0.0, s, 0.0, c), "z": (0.0, 0.0, s, c)}[axis]


def transform_placement(position: Sequence[float], orientation: Sequence[float], pivot: Sequence[float], rotation: Sequence[float]) -> tuple[Vec3, Quat]:
    return rotate_point(position, pivot, rotation), quat_multiply(rotation, orientation)


def bounds_for_placement(position: Sequence[float], orientation: Sequence[float], volume_min: Sequence[float], volume_max: Sequence[float]) -> dict[str, object]:
    p, lo, hi = vec3(position), vec3(volume_min), vec3(volume_max)
    corners = [rotate_point((x, y, z), (0.0, 0.0, 0.0), orientation) for x, y, z in product((lo[0], hi[0]), (lo[1], hi[1]), (lo[2], hi[2]))]
    points = [add(p, corner) for corner in corners]
    return {"min": [min(x[i] for x in points) for i in range(3)], "max": [max(x[i] for x in points) for i in range(3)], "rotationConfidence": "INFERRED_DERIVED_EXPERIMENTAL"}
