"""Friendly control catalog.

Friendly controls are a thin, user-facing layer over the *existing* edit /
profile / validation / Lua-generation backend. A control knows its resource
type, field path, target mode, schema type and allowed value type, so the user
only sees a simple label and value widget.

There is deliberately no second patch engine: converting a control to an edit
goes through :meth:`Lab.make_edit`, producing exactly the same
:class:`ProfileEdit` the Advanced editor would create.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional

from .field_paths import resolve_path
from .profile import EVIDENCE_STATES
from .resource_catalog import CATEGORIES
from .schema_model import TypeDatabase
from .type_parser import resource_type_to_lua_class

UI_TYPES = {"number", "bool", "string", "enum", "guid"}


def _package_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_control_catalog_path() -> str:
    return os.path.join(_package_dir(), "data", "control_catalog.json")


@dataclass
class FriendlyControl:
    id: str
    name: str
    category: str
    description: str
    ui_type: str
    status: str
    backend: Dict[str, Any] = dc_field(default_factory=dict)

    @staticmethod
    def from_dict(data: Dict) -> "FriendlyControl":
        return FriendlyControl(
            id=data.get("id", ""),
            name=data.get("name", ""),
            category=data.get("category", ""),
            description=data.get("description", ""),
            ui_type=data.get("ui_type", "number"),
            status=data.get("status", "EXPERIMENTAL"),
            backend=dict(data.get("backend", {})),
        )

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "ui_type": self.ui_type,
            "status": self.status,
            "backend": dict(self.backend),
        }

    # -- backend accessors ---------------------------------------------------

    @property
    def resource_type(self) -> str:
        return self.backend.get("resource_type", "")

    @property
    def path(self) -> str:
        return self.backend.get("path", "")

    @property
    def target(self) -> Dict[str, Any]:
        return self.backend.get("target", {"mode": "first"})


class ControlCatalog:
    def __init__(self, controls: List[FriendlyControl]) -> None:
        self.controls = controls
        self._by_id = {c.id: c for c in controls}

    @staticmethod
    def load(path: Optional[str] = None) -> "ControlCatalog":
        path = path or default_control_catalog_path()
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        raw = data.get("controls", data if isinstance(data, list) else [])
        return ControlCatalog([FriendlyControl.from_dict(item) for item in raw])

    def get(self, control_id: str) -> Optional[FriendlyControl]:
        return self._by_id.get(control_id)

    def controls_in_category(self, category: str) -> List[FriendlyControl]:
        return [c for c in self.controls if c.category == category]

    def validate(self, db: TypeDatabase) -> List[str]:
        """Validate every control against the live schema. Fails closed."""
        errors: List[str] = []
        seen_ids = set()
        for control in self.controls:
            if not control.id:
                errors.append("control missing id")
            if control.id in seen_ids:
                errors.append("duplicate control id: %s" % control.id)
            seen_ids.add(control.id)

            if not control.name:
                errors.append("control %s missing name" % control.id)
            if not control.description:
                errors.append("control %s missing description" % control.id)
            if control.category not in CATEGORIES:
                errors.append("control %s has unapproved category %r"
                              % (control.id, control.category))
            if control.ui_type not in UI_TYPES:
                errors.append("control %s has invalid ui_type %r"
                              % (control.id, control.ui_type))
            if control.status not in EVIDENCE_STATES:
                errors.append("control %s has invalid status %r"
                              % (control.id, control.status))

            backend = control.backend
            resource_type = backend.get("resource_type", "")
            path = backend.get("path", "")
            target = backend.get("target", {})
            if not resource_type:
                errors.append("control %s missing backend.resource_type" % control.id)
            if not path:
                errors.append("control %s missing backend.path" % control.id)
            if target.get("mode") not in {"first", "all", "match"}:
                errors.append("control %s has invalid target mode" % control.id)

            # Schema-level resolution.
            lua_class = resource_type_to_lua_class(resource_type)
            if not db.has_class(lua_class):
                errors.append("control %s resource_type not in schema: %s"
                              % (control.id, resource_type))
                continue
            resolution = resolve_path(db, lua_class, path)
            if not resolution.ok:
                errors.append("control %s path does not resolve: %s (%s)"
                              % (control.id, path, resolution.error))
            elif not resolution.editable:
                errors.append("control %s path is not editable by MVP: %s (%s)"
                              % (control.id, path, resolution.kind_label))

        return errors


def control_to_edit(lab, control: FriendlyControl, value: Any,
                    expected_original: Any = None):
    """Convert a friendly control + value into a validated ProfileEdit.

    Uses the existing ``Lab.make_edit`` so the result is identical to what the
    Advanced editor produces for the same resource/path/value/target.

    Returns ``(edit, error)``.
    """
    target = control.target or {"mode": "first"}
    return lab.make_edit(
        resource_type=control.resource_type,
        path=control.path,
        value=value,
        mode=target.get("mode", "first"),
        selector=target.get("selector"),
        evidence_state=control.status,
        expected_original=expected_original,
    )
