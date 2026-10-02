"""Conservative binary-layout primitives for offline KFC reconstruction."""
from __future__ import annotations

from dataclasses import dataclass


class KfcBinaryError(ValueError):
    pass


@dataclass(frozen=True)
class BinaryField:
    name: str
    offset: int
    size: int
    alignment: int = 1


@dataclass(frozen=True)
class FixedArrayLayout:
    name: str
    element_size: int
    count: int
    offset: int


@dataclass(frozen=True)
class BlobReference:
    name: str
    relative_offset: int
    length: int
    field_position: int


class KfcBinaryLayout:
    """Validate layout metadata without reading or writing game archives."""

    @staticmethod
    def align(position: int, alignment: int) -> int:
        if position < 0 or alignment <= 0 or alignment & (alignment - 1):
            raise KfcBinaryError("Position must be non-negative and alignment must be a power of two.")
        return (position + alignment - 1) & ~(alignment - 1)

    @classmethod
    def validate_fields(cls, fields: list[BinaryField], total_size: int) -> None:
        if total_size < 0:
            raise KfcBinaryError("Total size cannot be negative.")
        occupied: list[tuple[int, int, str]] = []
        for field in fields:
            if field.offset < 0 or field.size < 0:
                raise KfcBinaryError(f"Field has invalid bounds: {field.name}")
            if field.offset != cls.align(field.offset, field.alignment):
                raise KfcBinaryError(f"Field is not aligned: {field.name}")
            end = field.offset + field.size
            if end > total_size:
                raise KfcBinaryError(f"Field exceeds buffer: {field.name}")
            for old_start, old_end, old_name in occupied:
                if field.offset < old_end and old_start < end:
                    raise KfcBinaryError(f"Fields overlap: {old_name} and {field.name}")
            occupied.append((field.offset, end, field.name))

    @classmethod
    def validate_fixed_array(cls, array: FixedArrayLayout, total_size: int) -> None:
        if array.element_size <= 0 or array.count < 0:
            raise KfcBinaryError(f"Invalid fixed array: {array.name}")
        field = BinaryField(array.name, array.offset, array.element_size * array.count, array.element_size)
        cls.validate_fields([field], total_size)

    @staticmethod
    def resolve_blob(reference: BlobReference, stream_size: int) -> tuple[int, int]:
        if reference.field_position < 0 or reference.relative_offset < 0 or reference.length < 0:
            raise KfcBinaryError(f"Invalid blob reference: {reference.name}")
        start = reference.field_position + reference.relative_offset
        end = start + reference.length
        if end > stream_size:
            raise KfcBinaryError(f"Blob exceeds stream: {reference.name}")
        return start, end
