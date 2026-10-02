"""Versioned, implementation-independent procedural blueprint recipes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA_VERSION = 1
REQUIRED = {"schemaVersion", "name", "shape", "parameters", "material", "anchor", "transforms", "chunking", "metadata"}


@dataclass(frozen=True)
class BlueprintRecipe:
    name: str
    shape: str
    parameters: Mapping[str, Any]
    material: Mapping[str, Any] | str
    anchor: str | Mapping[str, Any]
    transforms: Mapping[str, Any]
    chunking: Mapping[str, Any]
    metadata: Mapping[str, Any]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {"schemaVersion": self.schema_version, "name": self.name, "shape": self.shape,
                "parameters": dict(self.parameters), "material": self.material, "anchor": self.anchor,
                "transforms": dict(self.transforms), "chunking": dict(self.chunking), "metadata": dict(self.metadata)}


def validate_recipe(value: Mapping[str, Any]) -> None:
    missing = REQUIRED - set(value)
    if missing: raise ValueError(f"missing recipe fields: {sorted(missing)}")
    if value["schemaVersion"] != SCHEMA_VERSION: raise ValueError("unsupported schemaVersion")
    for key in ("name", "shape"):
        if not isinstance(value[key], str) or not value[key]: raise ValueError(f"{key} must be a non-empty string")
    for key in ("parameters", "transforms", "chunking", "metadata"):
        if not isinstance(value[key], Mapping): raise ValueError(f"{key} must be an object")
    if not isinstance(value["material"], (str, Mapping)): raise ValueError("material must be a string or object")


def serialize_recipe(recipe: BlueprintRecipe) -> str:
    value = recipe.to_dict(); validate_recipe(value)
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def deserialize_recipe(text: str) -> BlueprintRecipe:
    value = json.loads(text)
    if not isinstance(value, Mapping): raise ValueError("recipe root must be an object")
    validate_recipe(value)
    return BlueprintRecipe(name=value["name"], shape=value["shape"], parameters=value["parameters"], material=value["material"],
                           anchor=value["anchor"], transforms=value["transforms"], chunking=value["chunking"], metadata=value["metadata"], schema_version=value["schemaVersion"])


def migrate_recipe(value: Mapping[str, Any], from_version: int) -> dict[str, Any]:
    """Apply explicit migrations; refusing unknown versions avoids silent drift."""
    if from_version == SCHEMA_VERSION:
        result = dict(value); validate_recipe(result); return result
    raise ValueError(f"no migration registered from schemaVersion {from_version} to {SCHEMA_VERSION}")
