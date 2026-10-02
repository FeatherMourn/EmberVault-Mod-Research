"""Validate EnshroudedBlenderTools-generated EML mod artifacts.

Validation is packaging and integrity evidence only; it never promotes an
export to a runtime-supported asset or installs it into the stable profile.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


GUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
SUPPORTED_COLLIDERS = {"Box", "Sphere", "Spheroid", "Cylinder", "Capsule", "Tapered Capsule"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_blender_export(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    errors: list[str] = []
    required = ("mod.json", "validation.json", "render_data.bin", "src/mod.lua")
    for name in required:
        if not (root / name).is_file():
            errors.append(f"missing required export file: {name}")
    if errors:
        return {"schema": "control_center.blender_export_validation.v1", "valid": False, "feature_state": "research-only", "errors": errors, "next_steps": _next_steps(errors)}
    try:
        mod = json.loads((root / "mod.json").read_text(encoding="utf-8"))
        validation = json.loads((root / "validation.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"invalid JSON metadata: {exc}")
        mod, validation = {}, {}
    if not isinstance(mod, dict) or not mod.get("id"):
        errors.append("mod.json must contain a module id")
    if isinstance(mod, dict):
        if mod.get("feature_state") not in (None, "research-only"):
            errors.append("Blender exports must remain research-only")
        entrypoint = str(mod.get("entrypoint", "src/mod.lua"))
        if Path(entrypoint).as_posix() != "src/mod.lua":
            errors.append("Blender export entrypoint must be src/mod.lua")
    target_guid = validation.get("target_guid") if isinstance(validation, dict) else None
    if not isinstance(target_guid, str) or not GUID_RE.fullmatch(target_guid):
        errors.append("validation.target_guid must be a GUID")
    mesh = root / "render_data.bin"
    if isinstance(validation, dict):
        lua = (root / "src" / "mod.lua").read_text(encoding="utf-8", errors="replace")
        if validation.get("target_type"):
            if target_guid not in lua:
                errors.append("src/mod.lua does not reference validation.target_guid")
            if validation["target_type"] not in lua:
                errors.append("src/mod.lua does not reference validation.target_type")
        icon = validation.get("item_icon")
        if isinstance(icon, dict) and icon.get("file"):
            icon_path = (root / str(icon["file"])).resolve()
            if root not in icon_path.parents:
                errors.append("item icon path escapes the staged export")
                icon_path = root / "__invalid_icon__"
            if not icon_path.is_file():
                errors.append(f"missing item icon: {icon['file']}")
            else:
                if icon.get("size") != icon_path.stat().st_size:
                    errors.append("item icon size does not match validation metadata")
                if icon.get("sha256") != _sha256(icon_path):
                    errors.append("item icon hash does not match validation metadata")
        if validation.get("mesh_size") != mesh.stat().st_size:
            errors.append("validation mesh_size does not match render_data.bin")
        if validation.get("mesh_sha256") != _sha256(mesh):
            errors.append("validation mesh_sha256 does not match render_data.bin")
        if validation.get("vertex_count", 0) <= 0:
            errors.append("validation vertex_count must be positive")
        elif validation.get("vertex_count", 0) > 65535:
            errors.append("validation vertex_count exceeds the 65,535 full-topology export limit")
        colliders = validation.get("colliders")
        if colliders is not None:
            if not isinstance(colliders, list):
                errors.append("validation colliders must be a list when provided")
            else:
                for collider in colliders:
                    shape = collider.get("shape") if isinstance(collider, dict) else collider
                    if shape not in SUPPORTED_COLLIDERS:
                        errors.append(f"unsupported collider shape: {shape}")
        lods = validation.get("lods")
        if lods is not None:
            if not isinstance(lods, list):
                errors.append("validation lods must be a list when provided")
            else:
                for lod in lods:
                    if isinstance(lod, dict) and isinstance(lod.get("vertex_count"), int) and lod["vertex_count"] > 65535:
                        errors.append("LOD vertex_count exceeds the 65,535 full-topology export limit")
        if validation.get("vertex_stride") not in (None, 24):
            errors.append("only 24-byte vertex streams are currently accepted")
        for patch in validation.get("texture_patches", []):
            if not isinstance(patch, dict):
                errors.append("texture patch entry is not an object")
                continue
            filename = f"{patch.get('material_index')}_{patch.get('material_guid')}_{patch.get('slot')}.bin"
            path = (root / "textures" / filename).resolve()
            if root not in path.parents:
                errors.append(f"texture patch path escapes the staged export: {filename}")
                continue
            if not path.is_file():
                errors.append(f"missing texture patch: {filename}")
            elif patch.get("sha256") != _sha256(path):
                errors.append(f"texture hash mismatch: {filename}")
    return {
        "schema": "control_center.blender_export_validation.v1",
        "valid": not errors,
        "feature_state": "research-only",
        "module_id": mod.get("id") if isinstance(mod, dict) else None,
        "target_guid": target_guid,
        "mesh_size": mesh.stat().st_size if mesh.is_file() else 0,
        "vertex_count": validation.get("vertex_count", 0) if isinstance(validation, dict) else 0,
        "texture_patch_count": len(validation.get("texture_patches", [])) if isinstance(validation, dict) and isinstance(validation.get("texture_patches", []), list) else 0,
        "icon_present": bool(isinstance(validation, dict) and isinstance(validation.get("item_icon"), dict) and validation["item_icon"].get("file")),
        "lod_metadata_status": "present" if isinstance(validation, dict) and validation.get("lods") is not None else "not provided",
        "collider_metadata_status": "present" if isinstance(validation, dict) and validation.get("colliders") is not None else "not provided",
        "errors": errors,
        "next_steps": _next_steps(errors),
    }


def _next_steps(errors: list[str]) -> list[str]:
    """Translate validator failures into beginner-readable repair actions."""
    steps: list[str] = []
    for error in errors:
        if "missing required export file" in error:
            steps.append("Export the asset again from BlenderTools and choose the complete export folder.")
        elif "target_guid" in error:
            steps.append("Re-export with a valid donor target selected; do not edit the GUID by hand.")
        elif "mesh_size" in error or "mesh_sha256" in error or "texture hash" in error:
            steps.append("The export changed after validation. Re-export to a new folder and try again.")
        elif "vertex_stride" in error:
            steps.append("Use the supported BlenderTools vertex export format, then export again.")
        elif "65,535" in error:
            steps.append("Reduce the generated mesh below 65,535 vertices or use a topology-preserving replacement.")
        elif "collider shape" in error:
            steps.append("Use only Box, Sphere, Spheroid, Cylinder, Capsule, or Tapered Capsule colliders.")
        elif "LOD vertex_count" in error:
            steps.append("Reduce the affected LOD below 65,535 vertices or export a topology-preserving replacement.")
        elif "escapes the staged export" in error:
            steps.append("Keep icons and texture patches inside the BlenderTools export folder.")
        elif "research-only" in error:
            steps.append("Leave the export marked research-only; stable installation is not supported yet.")
    return list(dict.fromkeys(steps))
