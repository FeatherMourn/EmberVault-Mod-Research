"""Headless application controller.

The UI is a thin wrapper around this object. Everything here can be exercised
from the test suite without opening a window.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from .cache import load_or_build, types_lua_hash
from .eml_template import build_mod_directory, default_mod_id, sanitize_id
from .field_paths import PathResolution, resolve_path
from .kfc_roots import load_root_entries
from .lua_generator import generate_lua, modification_summary
from .profile import Edit, Profile, Target, dumps
from .provenance import build_provenance
from .schema_model import TypeDatabase, TypeExpression
from .type_parser import lua_class_to_resource_type
from .validation import validate_value
from .resource_catalog import ResourceCatalog, default_catalog_path
from .control_catalog import (
    ControlCatalog,
    control_to_edit,
    default_control_catalog_path,
)

# Compatibility revalidation results.
COMPAT_UNCHANGED = "UNCHANGED"
COMPAT_FIELD_MOVED = "FIELD MOVED"
COMPAT_FIELD_TYPE_CHANGED = "FIELD TYPE CHANGED"
COMPAT_FIELD_MISSING = "FIELD MISSING"
COMPAT_RESOURCE_MISSING = "RESOURCE TYPE MISSING"


def leaf_signature(db: TypeDatabase, type_expr: TypeExpression) -> str:
    """Canonical signature string for a leaf type expression."""
    kind = type_expr.kind
    if kind in ("bool", "u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64",
                "f16", "f32", "f64", "string"):
        return kind
    if kind == "guid":
        return "guid"
    if kind == "reference":
        return "reference<%s>" % (type_expr.name or "")
    if kind == "named":
        if db.enum_choices(type_expr.name or ""):
            return type_expr.name or "named"
        return "class<%s>" % (type_expr.name or "")
    if kind == "array":
        return "array"
    if kind == "static_array":
        return "static_array"
    if kind == "bitmask":
        return "bitmask"
    if kind == "variant":
        return "variant"
    return "unknown"


class Lab:
    """Loads the schema, exposes the resource browser model, and generates mods."""

    def __init__(
        self,
        types_lua_path: str,
        base_lua_path: Optional[str] = None,
        kfc_dir: Optional[str] = None,
        cache_dir: Optional[str] = None,
        resource_map_path: Optional[str] = None,
        catalog_path: Optional[str] = None,
        control_catalog_path: Optional[str] = None,
    ) -> None:
        self.types_lua_path = types_lua_path
        self.base_lua_path = base_lua_path
        self.kfc_dir = kfc_dir
        self.cache_dir = cache_dir
        self.resource_map_path = resource_map_path
        self.catalog_path = catalog_path
        self.control_catalog_path = control_catalog_path

        self.db: Optional[TypeDatabase] = None
        self.roots: List[dict] = []
        self._roots_by_resource_type: Dict[str, dict] = {}
        self.types_sha256: str = ""
        self.catalog: Optional[ResourceCatalog] = None
        self.controls: Optional[ControlCatalog] = None

    # ------------------------------------------------------------------ load

    def load(self, force_rebuild: bool = False) -> None:
        if not os.path.isfile(self.types_lua_path):
            raise FileNotFoundError(
                "types.lua not found at %r" % self.types_lua_path
            )
        self.types_sha256 = types_lua_hash(self.types_lua_path)
        if self.cache_dir:
            self.db = load_or_build(
                self.types_lua_path, self.cache_dir, force_rebuild=force_rebuild
            )
        else:
            from .schema_parser import parse_types_lua_file
            self.db = parse_types_lua_file(self.types_lua_path)

        self.roots = load_root_entries(
            self.db,
            kfc_dir=self.kfc_dir,
            resource_map_path=self.resource_map_path,
        )
        self._roots_by_resource_type = {
            entry["resource_type"]: entry for entry in self.roots
        }
        self._load_catalogs()

    def _load_catalogs(self) -> None:
        """Load and validate the resource + control catalogs (fail closed)."""
        import os

        catalog_path = self.catalog_path or default_catalog_path()
        if os.path.isfile(catalog_path):
            self.catalog = ResourceCatalog.load(catalog_path)
            errors = self.catalog.validate(self.roots, self.db)
            if errors:
                raise ValueError(
                    "resource catalog is inconsistent with the technical root "
                    "list:\n  " + "\n  ".join(errors))

        control_path = self.control_catalog_path or default_control_catalog_path()
        if os.path.isfile(control_path):
            self.controls = ControlCatalog.load(control_path)
            errors = self.controls.validate(self.db)
            if errors:
                raise ValueError(
                    "control catalog is inconsistent with the schema:\n  "
                    + "\n  ".join(errors))

        # Mark catalog entries that have at least one friendly control.
        if self.catalog is not None and self.controls is not None:
            for control in self.controls.controls:
                entry = self.catalog.get(control.resource_type)
                if entry is not None:
                    entry.friendly_controls_available = True

    # --------------------------------------------------------------- queries

    def schema(self) -> TypeDatabase:
        if self.db is None:
            raise RuntimeError("schema not loaded")
        return self.db

    def root_entries(self) -> List[dict]:
        return list(self.roots)

    def resource_types(self) -> List[str]:
        return [entry["resource_type"] for entry in self.roots]

    def class_for_resource_type(self, resource_type: str) -> Optional[str]:
        entry = self._roots_by_resource_type.get(resource_type)
        if entry:
            return entry["lua_class"]
        # Fall back to direct conversion (still allows non-whitelisted classes
        # in advanced mode).
        candidate = resource_type.replace("::", ".")
        if self.db and self.db.has_class(candidate):
            return candidate
        return None

    def search(self, query: str) -> List[dict]:
        query = (query or "").strip().lower()
        if not query:
            return list(self.roots)
        results = []
        for entry in self.roots:
            haystack = (
                entry["family"].lower()
                + " "
                + entry["lua_class"].lower()
                + " "
                + entry["resource_type"].lower()
            )
            if query in haystack:
                results.append(entry)
        return results

    def fields_of(self, resource_type: str) -> List[Any]:
        lua_class = self.class_for_resource_type(resource_type)
        if not lua_class:
            return []
        cls = self.schema().get_class(lua_class)
        return list(cls.fields) if cls else []

    def search_catalog(self, query: str):
        """Search the friendly resource catalog (returns list of match dicts)."""
        if self.catalog is None:
            return []
        return self.catalog.search(query)

    def make_control_edit(self, control, value: Any, expected_original: Any = None):
        """Convert a friendly control + value into a validated ProfileEdit."""
        return control_to_edit(self, control, value, expected_original)

    def resolve(self, resource_type: str, path: str) -> PathResolution:
        lua_class = self.class_for_resource_type(resource_type)
        if not lua_class:
            return PathResolution(
                ok=False, path=path,
                error="unknown resource type %r" % resource_type,
            )
        return resolve_path(self.schema(), lua_class, path)

    def validate(self, resource_type: str, path: str, value: Any):
        resolution = self.resolve(resource_type, path)
        if not resolution.ok:
            from .validation import ValidationResult
            return ValidationResult(ok=False, error=resolution.error)
        if not resolution.editable:
            from .validation import ValidationResult
            return ValidationResult(
                ok=False,
                error="field %r is not editable by the MVP (%s)"
                % (path, resolution.kind_label),
            )
        return validate_value(self.schema(), resolution.leaf_type, value)

    # ------------------------------------------------------------- profiles

    def make_edit(
        self,
        resource_type: str,
        path: str,
        value: Any,
        mode: str = "first",
        selector: Optional[Dict[str, Any]] = None,
        evidence_state: str = "EXPERIMENTAL",
        expected_original: Any = None,
        enabled: bool = True,
    ) -> Tuple[Optional[Edit], Optional[str]]:
        """Build a validated edit, returning ``(edit, error)``."""
        resolution = self.resolve(resource_type, path)
        if not resolution.ok:
            return None, resolution.error
        if not resolution.editable:
            return None, "field %r is not editable by the MVP (%s)" % (
                path, resolution.kind_label)

        validation = validate_value(self.schema(), resolution.leaf_type, value)
        if not validation.ok:
            return None, validation.error

        target = Target(mode=mode, selector=selector)
        target_problem = target.validate()
        if target_problem:
            return None, target_problem

        if expected_original is not None:
            expected_validation = validate_value(
                self.schema(), resolution.leaf_type, expected_original
            )
            if not expected_validation.ok:
                return None, "expected_original: " + expected_validation.error

        signature = leaf_signature(self.schema(), resolution.leaf_type)
        edit = Edit(
            enabled=enabled,
            resource_type=resource_type,
            target=target,
            path=resolution.path,
            schema_type=signature,
            value=validation.value,
            evidence_state=evidence_state,
            expected_original=(
                expected_validation.value
                if expected_original is not None
                else None
            ),
        )
        return edit, None

    # --------------------------------------------------------- compatibility

    def compatibility(self, profile: Profile) -> Tuple[bool, List[dict]]:
        """Check a profile against the currently loaded schema.

        Returns ``(mismatch, revalidations)`` where ``mismatch`` is True if the
        profile's ``types_lua_sha256`` differs from the current one.
        """
        mismatch = bool(profile.types_lua_sha256) and (
            profile.types_lua_sha256 != self.types_sha256
        )
        revalidations: List[dict] = []
        for edit in profile.edits:
            lua_class = self.class_for_resource_type(edit.resource_type)
            if not lua_class:
                revalidations.append({
                    "resource_type": edit.resource_type,
                    "path": edit.path,
                    "result": COMPAT_RESOURCE_MISSING,
                })
                continue
            resolution = self.resolve(edit.resource_type, edit.path)
            if resolution.ok:
                signature = leaf_signature(self.schema(), resolution.leaf_type)
                if signature == edit.schema_type:
                    revalidations.append({
                        "resource_type": edit.resource_type,
                        "path": edit.path,
                        "result": COMPAT_UNCHANGED,
                    })
                else:
                    revalidations.append({
                        "resource_type": edit.resource_type,
                        "path": edit.path,
                        "result": COMPAT_FIELD_TYPE_CHANGED,
                        "was": edit.schema_type,
                        "now": signature,
                    })
            else:
                # Distinguish "moved" from "missing" crudely.
                field_name = edit.path.rsplit(".", 1)[-1].split("[")[0]
                cls = self.schema().get_class(lua_class)
                moved = bool(cls) and any(
                    f.name == field_name for f in cls.fields
                )
                revalidations.append({
                    "resource_type": edit.resource_type,
                    "path": edit.path,
                    "result": COMPAT_FIELD_MOVED if moved else COMPAT_FIELD_MISSING,
                })
        return mismatch, revalidations

    # ----------------------------------------------------------- generation

    def generate(self, profile: Profile, mod_id: Optional[str] = None) -> str:
        return generate_lua(
            profile, self.schema(), mod_id=mod_id or default_mod_id(profile)
        )

    def summary(self, profile: Profile) -> str:
        return modification_summary(profile, self.schema())

    def export(
        self,
        profile: Profile,
        base_output_dir: str,
        mod_id: Optional[str] = None,
        overwrite: bool = False,
    ) -> Dict[str, str]:
        """Export a profile as an EML mod directory, returning its paths."""
        mod_id = mod_id or default_mod_id(profile)
        lua_body = self.generate(profile, mod_id=mod_id)
        provenance = build_provenance(
            profile,
            lua_body,
            types_lua_path=self.types_lua_path,
            base_lua_path=self.base_lua_path,
        )
        folder = sanitize_id(profile.name)
        target = build_mod_directory(
            profile,
            self.schema(),
            base_output_dir,
            provenance,
            mod_id=mod_id,
            folder_name=folder,
            overwrite=overwrite,
        )
        return {
            "directory": target,
            "mod_json": os.path.join(target, "mod.json"),
            "mod_lua": os.path.join(target, "src", "mod.lua"),
            "profile_json": os.path.join(target, "profile.json"),
            "manifest": os.path.join(target, "generated_manifest.json"),
        }

    def profile_json(self, profile: Profile) -> str:
        return dumps(profile)
