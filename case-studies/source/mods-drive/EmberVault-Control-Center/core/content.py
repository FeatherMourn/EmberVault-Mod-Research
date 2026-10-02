"""Content Creator project metadata, separate from live game content."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from dataclasses import asdict, dataclass, field
from pathlib import Path
from .storage import write_json_atomic


@dataclass
class ContentProject:
    id: str
    name: str
    profile_id: str
    status: str = "draft"
    description: str = ""
    design_type: str = "furniture"
    design_notes: str = ""
    asset_references: list[str] = field(default_factory=list)
    published: bool = False
    published_at: str = ""
    materials: list[str] = field(default_factory=list)
    dimensions: dict[str, float] = field(default_factory=dict)
    recipe_plan: list[str] = field(default_factory=list)
    registration_plan: str = ""
    compatibility_notes: str = ""
    linked_research_ids: list[str] = field(default_factory=list)
    linked_knowledge_ids: list[str] = field(default_factory=list)
    design_decisions: list[dict] = field(default_factory=list)


class ContentProjectService:
    def __init__(self, root: Path):
        self.path = Path(root) / "content-projects" / "projects.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[ContentProject]:
        if not self.path.exists():
            return []
        try:
            projects = []
            raw_projects = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw_projects, list):
                return []
            for item in raw_projects:
                if not isinstance(item, dict):
                    continue
                try:
                    project = ContentProject(**item)
                except (TypeError, ValueError):
                    continue
                if project.status not in {"draft", "ready", "blocked"}:
                    project.status = "draft"
                if project.design_type not in {"furniture", "building", "recipe", "other"}:
                    project.design_type = "furniture"
                if not isinstance(project.design_notes, str):
                    project.design_notes = ""
                if not isinstance(project.asset_references, list):
                    project.asset_references = []
                else:
                    project.asset_references = [item.strip() for item in project.asset_references
                                                if isinstance(item, str) and item.strip() and not Path(item).is_absolute() and ".." not in Path(item).parts]
                if not isinstance(project.published, bool):
                    project.published = False
                if not isinstance(project.published_at, str):
                    project.published_at = ""
                for field_name in ("materials", "recipe_plan"):
                    values = getattr(project, field_name)
                    if not isinstance(values, list):
                        values = []
                    setattr(project, field_name, [value.strip() for value in values if isinstance(value, str) and value.strip()])
                if not isinstance(project.dimensions, dict):
                    project.dimensions = {}
                else:
                    project.dimensions = {str(key): float(value) for key, value in project.dimensions.items()
                                          if isinstance(key, str) and isinstance(value, (int, float)) and value > 0}
                for field_name in ("registration_plan", "compatibility_notes"):
                    if not isinstance(getattr(project, field_name), str):
                        setattr(project, field_name, "")
                if not isinstance(project.linked_research_ids, list):
                    project.linked_research_ids = []
                else:
                    project.linked_research_ids = sorted({value.strip() for value in project.linked_research_ids
                                                          if isinstance(value, str) and value.strip()})
                if not isinstance(project.linked_knowledge_ids, list):
                    project.linked_knowledge_ids = []
                else:
                    project.linked_knowledge_ids = sorted({value.strip() for value in project.linked_knowledge_ids
                                                           if isinstance(value, str) and value.strip()})
                if not isinstance(project.design_decisions, list):
                    project.design_decisions = []
                else:
                    project.design_decisions = [decision for decision in project.design_decisions
                                                if isinstance(decision, dict) and isinstance(decision.get("decision"), str)
                                                and decision["decision"].strip()]
                projects.append(project)
            return projects
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return []

    def create(self, name: str, profile_id: str, description: str = "", design_type: str = "furniture", design_notes: str = "", asset_references: list[str] | None = None, materials: list[str] | None = None, dimensions: dict[str, float] | None = None, recipe_plan: list[str] | None = None, registration_plan: str = "", compatibility_notes: str = "", linked_research_ids: list[str] | None = None) -> ContentProject:
        if not name.strip() or not profile_id.strip():
            raise ValueError("Content project name and profile are required")
        if design_type not in {"furniture", "building", "recipe", "other"}:
            raise ValueError("Unknown content design type")
        references = self._normalize_asset_references(asset_references or [])
        project = ContentProject(f"EV-CONTENT-{uuid.uuid4().hex[:8].upper()}", name.strip(), profile_id,
                                 description=description.strip(), design_type=design_type,
                                 design_notes=design_notes.strip(), asset_references=references,
                                 materials=self._normalize_text_list(materials), dimensions=self._normalize_dimensions(dimensions),
                                 recipe_plan=self._normalize_text_list(recipe_plan), registration_plan=registration_plan.strip(),
                                 compatibility_notes=compatibility_notes.strip(),
                                 linked_research_ids=self._normalize_ids(linked_research_ids))
        projects = self.list()
        projects.append(project)
        write_json_atomic(self.path, [asdict(item) for item in projects])
        return project

    @staticmethod
    def _normalize_text_list(values: list[str] | None) -> list[str]:
        if values is None:
            return []
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("Content lists must contain non-empty strings")
        return list(dict.fromkeys(value.strip() for value in values))

    @staticmethod
    def _normalize_ids(values: list[str] | None) -> list[str]:
        if values is None:
            return []
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("Research references must contain non-empty IDs")
        return sorted(set(value.strip() for value in values))

    def link_research(self, project_id: str, research_ids: list[str]) -> ContentProject:
        """Attach stable research IDs without copying research records."""
        return self.link_references(project_id, research_ids=research_ids)

    def link_references(self, project_id: str, research_ids: list[str] | None = None,
                        knowledge_ids: list[str] | None = None) -> ContentProject:
        """Attach stable research and knowledge IDs without copying source records."""
        links = self._normalize_ids(research_ids)
        knowledge_links = self._normalize_ids(knowledge_ids)
        projects = self.list()
        for project in projects:
            if project.id == project_id:
                project.linked_research_ids = links
                project.linked_knowledge_ids = knowledge_links
                if project.published:
                    project.published = False
                    project.published_at = ""
                write_json_atomic(self.path, [asdict(item) for item in projects])
                return project
        raise KeyError(project_id)

    def record_design_decision(self, project_id: str, decision: str, rationale: str,
                               research_ids: list[str] | None = None,
                               knowledge_ids: list[str] | None = None) -> ContentProject:
        """Record a traceable design choice without embedding source records."""
        if not isinstance(decision, str) or not decision.strip() or not isinstance(rationale, str) or not rationale.strip():
            raise ValueError("Design decision and rationale are required")
        projects = self.list()
        for project in projects:
            if project.id == project_id:
                project.design_decisions.append({
                    "decision": decision.strip(),
                    "rationale": rationale.strip(),
                    "research_ids": self._normalize_ids(research_ids),
                    "knowledge_ids": self._normalize_ids(knowledge_ids),
                })
                if project.published:
                    project.published = False
                    project.published_at = ""
                write_json_atomic(self.path, [asdict(item) for item in projects])
                return project
        raise KeyError(project_id)

    def preview(self, project_id: str) -> dict:
        """Build a deterministic, non-mutating design review for the Control Center."""
        project = next((item for item in self.list() if item.id == project_id), None)
        if project is None:
            raise KeyError(project_id)
        issues = self.validate_design(project_id)
        return {
            "schema_version": 1,
            "project_id": project.id,
            "name": project.name,
            "design_type": project.design_type,
            "status": project.status,
            "ready_for_export": not issues,
            "validation_issues": issues,
            "asset_references": list(project.asset_references),
            "asset_count": len(project.asset_references),
            "materials": list(project.materials),
            "dimensions": dict(sorted(project.dimensions.items())),
            "recipe_steps": list(project.recipe_plan),
            "registration_plan": project.registration_plan,
            "compatibility_notes": project.compatibility_notes,
            "research_ids": list(project.linked_research_ids),
            "knowledge_ids": list(project.linked_knowledge_ids),
            "design_decisions": list(project.design_decisions),
            "application_state": "design-only",
            "live_installation": False,
        }

    @staticmethod
    def _normalize_dimensions(values: dict[str, float] | None) -> dict[str, float]:
        if values is None:
            return {}
        if not isinstance(values, dict):
            raise ValueError("Dimensions must be an object")
        result = {}
        for key, value in values.items():
            if not isinstance(key, str) or not key.strip() or not isinstance(value, (int, float)) or value <= 0:
                raise ValueError("Dimensions must contain positive numeric values")
            result[key.strip()] = float(value)
        return result

    def set_status(self, project_id: str, status: str) -> ContentProject:
        if status not in {"draft", "ready", "blocked"}:
            raise ValueError("Unknown content project status")
        projects = self.list()
        for project in projects:
            if project.id == project_id:
                if status == "ready" and not project.description.strip():
                    raise ValueError("Add a development brief before marking content ready")
                project.status = status
                if project.published:
                    project.published = False
                    project.published_at = ""
                write_json_atomic(self.path, [asdict(item) for item in projects])
                return project
        raise KeyError(project_id)

    def update_design(self, project_id: str, design_type: str, design_notes: str, asset_references: list[str] | None = None, materials: list[str] | None = None, dimensions: dict[str, float] | None = None, recipe_plan: list[str] | None = None, registration_plan: str = "", compatibility_notes: str = "") -> ContentProject:
        if design_type not in {"furniture", "building", "recipe", "other"}:
            raise ValueError("Unknown content design type")
        projects = self.list()
        for project in projects:
            if project.id == project_id:
                project.design_type = design_type
                project.design_notes = design_notes.strip()
                project.asset_references = self._normalize_asset_references(asset_references or [])
                project.materials = self._normalize_text_list(materials)
                project.dimensions = self._normalize_dimensions(dimensions)
                project.recipe_plan = self._normalize_text_list(recipe_plan)
                project.registration_plan = registration_plan.strip()
                project.compatibility_notes = compatibility_notes.strip()
                if project.published:
                    project.published = False
                    project.published_at = ""
                write_json_atomic(self.path, [asdict(item) for item in projects])
                return project
        raise KeyError(project_id)

    def validate_design(self, project_id: str) -> list[str]:
        projects = self.list()
        for project in projects:
            if project.id != project_id:
                continue
            issues = []
            if not project.description.strip():
                issues.append("Development brief is required")
            if not project.design_notes.strip():
                issues.append("Design notes are required")
            if project.design_type == "furniture" and not project.materials:
                issues.append("Furniture projects need at least one material")
            if not project.dimensions:
                issues.append("At least one positive dimension is required")
            if project.design_type == "recipe" and not project.recipe_plan:
                issues.append("Recipe projects need a recipe plan")
            if not project.registration_plan.strip():
                issues.append("Registration plan is required")
            if not project.compatibility_notes.strip():
                issues.append("Compatibility notes are required")
            return issues
        raise KeyError(project_id)

    @staticmethod
    def _normalize_asset_references(references: list[str]) -> list[str]:
        if not isinstance(references, list):
            raise ValueError("Asset references must be a list")
        result = []
        for reference in references:
            if not isinstance(reference, str) or not reference.strip():
                continue
            path = Path(reference.strip())
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Asset references must remain relative to the project")
            result.append(reference.strip())
        return list(dict.fromkeys(result))

    def publish(self, project_id: str) -> ContentProject:
        projects = self.list()
        for project in projects:
            if project.id == project_id:
                if project.status != "ready" or not project.description.strip():
                    raise ValueError("Mark the content project ready before publishing")
                project.published = True
                project.published_at = datetime.now(timezone.utc).isoformat()
                write_json_atomic(self.path, [asdict(item) for item in projects])
                return project
        raise KeyError(project_id)

    def unpublish(self, project_id: str) -> ContentProject:
        projects = self.list()
        for project in projects:
            if project.id == project_id:
                project.published = False
                project.published_at = ""
                write_json_atomic(self.path, [asdict(item) for item in projects])
                return project
        raise KeyError(project_id)

    def export(self, project: ContentProject) -> Path:
        """Export project metadata without touching live game content."""
        destination = self.path.parent.parent / "exports" / "content-projects" / f"{project.id}.json"
        write_json_atomic(destination, {
            "schema_version": 1,
            "project": asdict(project),
            "preview": self.preview(project.id),
            "application_state": "design-only",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })
        return destination
