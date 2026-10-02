"""Lossless coordinate helpers for BuildingPlaceEvent grid values.

Build 1076226 reports grid coordinates as signed Q32.32 integers.  Keep the
raw values as integers and only convert after subtraction so large world
coordinates do not lose precision in JSON/Python float arithmetic.
"""
from __future__ import annotations

import math
from typing import Any, Iterable

Q32_SCALE = 1 << 32
COORDINATE_ENCODING = "signed_q32_32"
COORDINATE_EVIDENCE = "PROVEN_BUILD_1076226"


def coerce_raw_int(value: Any) -> int:
    """Convert an integer or exactly representable integral legacy float.

    Legacy v0.29 files used JSON floats.  Values above 2**53 are rejected
    rather than silently rounding a world coordinate.
    """
    if isinstance(value, bool):
        raise ValueError("boolean is not a coordinate")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer() or abs(value) > (1 << 53):
            raise ValueError("coordinate float is not exactly representable")
        result = int(value)
        if float(result) != value:
            raise ValueError("coordinate float lost integer precision")
        return result
    if isinstance(value, str):
        try:
            result = int(value, 0)
        except ValueError as exc:
            raise ValueError("invalid coordinate string") from exc
        return result
    raise ValueError("invalid coordinate value")


def coerce_raw_vector(values: Any, n: int = 3) -> list[int]:
    if not isinstance(values, (list, tuple)) or len(values) < n:
        raise ValueError("coordinate vector must contain three values")
    return [coerce_raw_int(values[index]) for index in range(n)]


def decode_component(raw: int) -> float:
    return raw / Q32_SCALE


def decode_world(raw: Iterable[int]) -> list[float]:
    return [decode_component(int(value)) for value in raw]


def relative_raw(raw: Iterable[int], origin: Iterable[int]) -> list[int]:
    return [int(value) - int(base) for value, base in zip(raw, origin)]


def relative_world(raw: Iterable[int], origin: Iterable[int]) -> list[float]:
    return decode_world(relative_raw(raw, origin))


def encode_component(value: float) -> int:
    if not math.isfinite(value):
        raise ValueError("cannot encode non-finite coordinate")
    # Encoding is offline-only; round ties deterministically away from zero.
    scaled = value * Q32_SCALE
    return int(math.floor(scaled + 0.5) if scaled >= 0 else math.ceil(scaled - 0.5))


def encode_world(values: Iterable[float]) -> list[int]:
    return [encode_component(float(value)) for value in values]


def coordinate_metadata() -> dict[str, Any]:
    return {"encoding": COORDINATE_ENCODING, "scale": Q32_SCALE,
            "rawType": "signed_int64", "evidence": COORDINATE_EVIDENCE,
            "conversion": "world = raw / scale; local = (raw-origin) / scale"}
