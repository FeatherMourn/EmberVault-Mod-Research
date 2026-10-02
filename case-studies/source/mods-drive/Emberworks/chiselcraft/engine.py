from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Iterable

from construction_sdk.models import Blueprint, Coordinate, Piece


SIZE = 16
Cell = tuple[int, int, int]


@dataclass
class MicroStructure:
    name: str
    materials: dict[str, str] = field(default_factory=dict)
    cells: dict[Cell, str] = field(default_factory=dict)
    parent_shape: str = "cube"

    def validate_cell(self, cell: Cell) -> None:
        if len(cell) != 3 or any(value < 0 or value >= SIZE for value in cell):
            raise ValueError(f"cell outside {SIZE}x{SIZE}x{SIZE} grid: {cell}")

    def add_material(self, material_id: str, resource_id: str) -> None:
        if not material_id or not resource_id:
            raise ValueError("material and resource IDs are required")
        self.materials[material_id] = resource_id

    def set_cell(self, cell: Cell, material_id: str) -> None:
        self.validate_cell(cell)
        if material_id not in self.materials:
            raise ValueError(f"unknown material: {material_id}")
        self.cells[cell] = material_id

    def remove_cell(self, cell: Cell) -> None:
        self.validate_cell(cell)
        self.cells.pop(cell, None)

    def fill_box(self, minimum: Cell, maximum: Cell, material_id: str) -> None:
        if material_id not in self.materials:
            raise ValueError(f"unknown material: {material_id}")
        for x in range(minimum[0], maximum[0] + 1):
            for y in range(minimum[1], maximum[1] + 1):
                for z in range(minimum[2], maximum[2] + 1):
                    self.set_cell((x, y, z), material_id)

    def cells_with_material(self, material_id: str) -> set[Cell]:
        return {cell for cell, value in self.cells.items() if value == material_id}

    def material_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for material in self.cells.values():
            counts[material] = counts.get(material, 0) + 1
        return dict(sorted(counts.items()))

    def to_blueprint(self, origin: Coordinate = Coordinate(0, 0, 0)) -> Blueprint:
        """Export occupied microcells through the shared construction contract."""
        pieces = []
        for (x, y, z), material_id in sorted(self.cells.items()):
            pieces.append(Piece(origin.add(Coordinate(x, y, z)), self.materials[material_id], material_id,
                                 properties={"microstructure": self.name, "parent_shape": self.parent_shape}))
        return Blueprint(self.name, pieces, source_type="chiselcraft", anchor=origin,
                         metadata={"resolution": [SIZE, SIZE, SIZE], "parent_shape": self.parent_shape})

    def to_dict(self) -> dict:
        return {
            "format": "emberworks.microstructure",
            "version": "0.1",
            "name": self.name,
            "resolution": [SIZE, SIZE, SIZE],
            "parent_shape": self.parent_shape,
            "materials": self.materials,
            "cells": [{"x": x, "y": y, "z": z, "material": material}
                      for (x, y, z), material in sorted(self.cells.items())],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MicroStructure":
        if data.get("format") != "emberworks.microstructure":
            raise ValueError("unsupported microstructure format")
        resolution = data.get("resolution")
        if resolution != [SIZE, SIZE, SIZE]:
            raise ValueError("only 16x16x16 microstructures are supported")
        result = cls(data["name"], dict(data.get("materials", {})), parent_shape=data.get("parent_shape", "cube"))
        for raw in data.get("cells", []):
            result.set_cell((raw["x"], raw["y"], raw["z"]), raw["material"])
        return result


@dataclass
class MicroOperation:
    before: dict[Cell, str | None]
    after: dict[Cell, str | None]
    status: str = "committed"

    def undo(self, structure: MicroStructure) -> None:
        for cell, material in self.before.items():
            if material is None:
                structure.cells.pop(cell, None)
            else:
                structure.set_cell(cell, material)
        self.status = "undone"

    def redo(self, structure: MicroStructure) -> None:
        for cell, material in self.after.items():
            if material is None:
                structure.cells.pop(cell, None)
            else:
                structure.set_cell(cell, material)
        self.status = "committed"


def edit_cells(structure: MicroStructure, changes: Iterable[tuple[Cell, str | None]]) -> MicroOperation:
    changes = list(changes)
    before = {cell: structure.cells.get(cell) for cell, _ in changes}
    after = {cell: material for cell, material in changes}
    for cell, material in changes:
        if material is None:
            structure.remove_cell(cell)
        else:
            structure.set_cell(cell, material)
    return MicroOperation(before, after)
