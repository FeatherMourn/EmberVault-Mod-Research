"""Research-only planning for donor-preserving TemplateResource model patches."""
from __future__ import annotations

import json
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class TemplateGraphError(ValueError):
    pass


@dataclass(frozen=True)
class TemplateModelPatchPlan:
    source: Path
    component_path: str
    donor_model_guid: str
    replacement_model_guid: str
    preserved_components: bool = True
    state: str = "research-only"
    source_sha256: str = ""


class TemplateGraphPlanner:
    """Locate a model edge and describe a minimal replacement without editing files."""

    def plan(self, source: Path, replacement_model_guid: str,
             model_component_index: int | None = None) -> TemplateModelPatchPlan:
        source = Path(source).resolve()
        if not source.is_file() or source.is_symlink():
            raise TemplateGraphError("TemplateResource source must be a regular file.")
        replacement = str(replacement_model_guid).strip()
        if not replacement:
            raise TemplateGraphError("A replacement model GUID is required.")
        try:
            data = json.loads(source.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise TemplateGraphError(f"TemplateResource JSON is invalid: {exc}") from exc
        components = data.get("components") if isinstance(data, dict) else None
        if not isinstance(components, list):
            raise TemplateGraphError("TemplateResource components must be a list.")
        matches: list[tuple[int, dict[str, Any]]] = []
        for index, component in enumerate(components):
            if not isinstance(component, dict) or component.get("$type") != "keen::ecs::ModelResource":
                continue
            matches.append((index, component))
        if len(matches) > 1 and model_component_index is None:
            raise TemplateGraphError("TemplateResource has multiple ModelResource components; explicit selection is required.")
        if model_component_index is not None:
            matches = [item for item in matches if item[0] == int(model_component_index)]
            if not matches:
                raise TemplateGraphError("Requested model component index was not found.")
        for index, component in matches:
            value = component.get("$value")
            donor = value.get("model") if isinstance(value, dict) else None
            if not isinstance(donor, str) or not donor.strip():
                raise TemplateGraphError("ModelResource component has no model GUID.")
            return TemplateModelPatchPlan(
                source, f"components[{index}].$value.model", donor.strip(), replacement,
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            )
        raise TemplateGraphError("No keen::ecs::ModelResource component was found.")

    @staticmethod
    def inventory(source: Path) -> tuple[dict[str, Any], ...]:
        """Return a read-only inventory of component types and indexes."""
        source = Path(source).resolve()
        try:
            data = json.loads(source.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise TemplateGraphError(f"TemplateResource JSON is invalid: {exc}") from exc
        components = data.get("components") if isinstance(data, dict) else None
        if not isinstance(components, list):
            raise TemplateGraphError("TemplateResource components must be a list.")
        return tuple({"index": index, "type": component.get("$type", "")}
                     for index, component in enumerate(components)
                     if isinstance(component, dict))

    @staticmethod
    def manifest_metadata(plan: TemplateModelPatchPlan) -> dict[str, Any]:
        source_hash = plan.source_sha256 or hashlib.sha256(plan.source.read_bytes()).hexdigest()
        component_index = int(plan.component_path.split("[")[1].split("]")[0])
        return {
            "state": plan.state,
            "source": str(plan.source),
            "component_path": plan.component_path,
            "component_index": component_index,
            "donor_model_guid": plan.donor_model_guid,
            "replacement_model_guid": plan.replacement_model_guid,
            "mechanics_policy": "preserve_all_other_components",
            "preserved_components": plan.preserved_components,
            "runtime_mutation": False,
            "rollback_policy": "donor_unchanged_remove_candidate_restore_recorded_version",
            "source_sha256": source_hash,
            "promotion_requirements": [
                "replacement RenderModel exists on the target build",
                "TemplateResource graph is accepted by the runtime route",
                "placed object visibly uses the replacement model",
                "comfort, collision, health, and interaction behavior is preserved",
                "rollback restores the recorded donor graph",
            ],
        }

    def write_candidate(self, plan: TemplateModelPatchPlan, destination: Path) -> Path:
        """Write a candidate JSON copy with only the planned model edge changed."""
        destination = Path(destination).resolve()
        current_hash = hashlib.sha256(plan.source.read_bytes()).hexdigest()
        if plan.source_sha256 and current_hash != plan.source_sha256:
            raise TemplateGraphError(
                "TemplateResource changed after planning; re-plan against the current donor before writing."
            )
        try:
            data = json.loads(plan.source.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise TemplateGraphError(f"TemplateResource JSON is invalid: {exc}") from exc
        components = data.get("components") if isinstance(data, dict) else None
        index = int(plan.component_path.split("[")[1].split("]")[0])
        try:
            component = components[index]
            component["$value"]["model"] = plan.replacement_model_guid
        except (IndexError, KeyError, TypeError) as exc:
            raise TemplateGraphError("Planned model component no longer matches source.") from exc
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        try:
            temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            os.replace(temporary, destination)
        except OSError as exc:
            if temporary.exists():
                temporary.unlink()
            raise TemplateGraphError(f"Candidate could not be written: {exc}") from exc
        return destination

    @staticmethod
    def verify_candidate(plan: TemplateModelPatchPlan, candidate: Path) -> tuple[bool, tuple[str, ...]]:
        """Verify donor/candidate differ only at the planned model path."""
        try:
            donor = json.loads(plan.source.read_text(encoding="utf-8-sig"))
            variant = json.loads(Path(candidate).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise TemplateGraphError(f"Candidate verification could not read JSON: {exc}") from exc
        differences: list[str] = []

        def walk(left: Any, right: Any, path: str) -> None:
            if isinstance(left, dict) and isinstance(right, dict):
                for key in sorted(set(left) | set(right)):
                    walk(left.get(key), right.get(key), f"{path}.{key}" if path else str(key))
            elif isinstance(left, list) and isinstance(right, list):
                for index in range(max(len(left), len(right))):
                    walk(left[index] if index < len(left) else None,
                         right[index] if index < len(right) else None,
                         f"{path}[{index}]")
            elif left != right:
                differences.append(path)

        walk(donor, variant, "")
        allowed = plan.component_path
        unexpected = tuple(path for path in differences if path != allowed)
        model_changed = allowed in differences
        return model_changed and not unexpected, unexpected
