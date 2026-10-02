"""Isolated research records and evidence notes."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from .storage import write_json_atomic
from .integration import IntegrationContext


@dataclass
class ResearchRecord:
    id: str
    title: str
    hypothesis: str
    profile_id: str
    status: str = "planned"
    evidence: list[str] = field(default_factory=list)
    created_at: str = ""
    published: bool = False
    published_at: str = ""
    game_build: str = ""
    game_version: str = ""
    reproduction_steps: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    promotion_status: str = "not-requested"
    promotion_note: str = ""
    linked_package_ids: list[str] = field(default_factory=list)
    linked_module_ids: list[str] = field(default_factory=list)
    linked_knowledge_ids: list[str] = field(default_factory=list)
    experiment_template: str = "general"
    attachments: list[dict] = field(default_factory=list)
    build_history: list[str] = field(default_factory=list)
    comparison_runs: list[dict] = field(default_factory=list)
    discussion_notes: list[str] = field(default_factory=list)


class ResearchService:
    def __init__(self, root: Path):
        self.path = Path(root) / "research" / "records.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[ResearchRecord]:
        if not self.path.exists():
            return []
        try:
            records = []
            raw_records = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw_records, list):
                return []
            for item in raw_records:
                if not isinstance(item, dict):
                    continue
                try:
                    record = ResearchRecord(**item)
                except (TypeError, ValueError):
                    continue
                if record.status not in {"planned", "running", "completed", "blocked"}:
                    record.status = "planned"
                if not isinstance(record.evidence, list):
                    record.evidence = []
                else:
                    record.evidence = [item.strip() for item in record.evidence if isinstance(item, str) and item.strip()]
                if not isinstance(record.published, bool):
                    record.published = False
                if not isinstance(record.published_at, str):
                    record.published_at = ""
                for field_name in ("game_build", "game_version", "promotion_note"):
                    if not isinstance(getattr(record, field_name), str):
                        setattr(record, field_name, "")
                for field_name in ("reproduction_steps", "failures"):
                    values = getattr(record, field_name)
                    if not isinstance(values, list):
                        values = []
                    setattr(record, field_name, [value.strip() for value in values
                                                 if isinstance(value, str) and value.strip()])
                if record.promotion_status not in {"not-requested", "requested", "approved", "rejected"}:
                    record.promotion_status = "not-requested"
                for field_name in ("linked_package_ids", "linked_module_ids", "linked_knowledge_ids"):
                    values = getattr(record, field_name)
                    if not isinstance(values, list):
                        values = []
                    setattr(record, field_name, sorted({value.strip() for value in values
                                                         if isinstance(value, str) and value.strip()}))
                for field_name in ("build_history", "discussion_notes"):
                    values = getattr(record, field_name)
                    setattr(record, field_name, [value.strip() for value in values if isinstance(value, str) and value.strip()] if isinstance(values, list) else [])
                for field_name in ("attachments", "comparison_runs"):
                    values = getattr(record, field_name)
                    setattr(record, field_name, [value for value in values if isinstance(value, dict)] if isinstance(values, list) else [])
                if not isinstance(record.experiment_template, str) or not record.experiment_template.strip():
                    record.experiment_template = "general"
                records.append(record)
            return records
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return []

    def create(self, title: str, hypothesis: str, profile_id: str,
               game_build: str = "", game_version: str = "", experiment_template: str = "general") -> ResearchRecord:
        if not title.strip() or not hypothesis.strip() or not profile_id.strip():
            raise ValueError("Research title, hypothesis, and profile are required")
        if experiment_template not in {"general", "runtime-observation", "compatibility", "content-design", "reproduction"}:
            raise ValueError("Unknown experiment template")
        record = ResearchRecord(
            id=f"EV-RES-{uuid.uuid4().hex[:8].upper()}", title=title.strip(),
            hypothesis=hypothesis.strip(), profile_id=profile_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            game_build=game_build.strip(), game_version=game_version.strip(),
            experiment_template=experiment_template,
        )
        records = self.list()
        records.append(record)
        write_json_atomic(self.path, [asdict(item) for item in records])
        return record

    def add_evidence(self, record_id: str, note: str) -> ResearchRecord:
        records = self.list()
        for record in records:
            if record.id == record_id:
                if not note.strip():
                    raise ValueError("Evidence note is required")
                record.evidence.append(note.strip())
                if record.published:
                    record.published = False
                    record.published_at = ""
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def add_attachment(self, record_id: str, name: str, kind: str, note: str = "") -> ResearchRecord:
        if not name.strip() or not kind.strip():
            raise ValueError("Evidence attachment name and kind are required")
        path = Path(name.strip())
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Evidence attachments must be relative")
        records = self.list()
        for record in records:
            if record.id == record_id:
                record.attachments.append({"name": path.as_posix(), "kind": kind.strip(), "note": note.strip()})
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def import_runtime_log(self, record_id: str, source: Path) -> ResearchRecord:
        """Import bounded text evidence without retaining the source path."""
        source = Path(source)
        if not source.is_file():
            raise ValueError("Runtime log does not exist")
        text = source.read_text(encoding="utf-8", errors="replace")[-12000:]
        safe = "\n".join(line[:500] for line in text.splitlines()[-100:])
        return self.add_evidence(record_id, "runtime-log-import: " + safe)

    def reproducibility_score(self, record_id: str) -> dict:
        record = next((item for item in self.list() if item.id == record_id), None)
        if record is None:
            raise KeyError(record_id)
        checks = {"hypothesis": bool(record.hypothesis), "evidence": bool(record.evidence),
                  "reproduction_steps": bool(record.reproduction_steps), "game_build": bool(record.game_build),
                  "outcome": record.status == "completed" and not record.failures}
        return {"score": round(sum(checks.values()) / len(checks) * 100), "checks": checks}

    def add_comparison(self, record_id: str, label: str, outcome: str, build: str = "") -> ResearchRecord:
        if not label.strip() or not outcome.strip():
            raise ValueError("Comparison label and outcome are required")
        records = self.list()
        for record in records:
            if record.id == record_id:
                record.comparison_runs.append({"label": label.strip(), "outcome": outcome.strip(), "build": build.strip()})
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def add_discussion_note(self, record_id: str, note: str) -> ResearchRecord:
        return self._append_record_text(record_id, "discussion_notes", note)

    def export_report(self, record_id: str) -> Path:
        record = next((item for item in self.list() if item.id == record_id), None)
        if record is None:
            raise KeyError(record_id)
        destination = self.path.parent.parent / "exports" / "research" / f"{record.id}-report.json"
        write_json_atomic(destination, {"schema_version": 1, "report": {"id": record.id, "title": record.title,
            "hypothesis": record.hypothesis, "status": record.status, "build": record.game_build,
            "reproducibility": self.reproducibility_score(record.id), "evidence_count": len(record.evidence),
            "attachment_count": len(record.attachments), "comparison_count": len(record.comparison_runs),
            "discussion_count": len(record.discussion_notes)}, "application_state": "research-report",
            "generated_at": datetime.now(timezone.utc).isoformat()})
        return destination

    def _append_record_text(self, record_id: str, field_name: str, text: str) -> ResearchRecord:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Research record text is required")
        records = self.list()
        for record in records:
            if record.id == record_id:
                getattr(record, field_name).append(text.strip())
                if record.published:
                    record.published = False
                    record.published_at = ""
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def add_reproduction_step(self, record_id: str, step: str) -> ResearchRecord:
        return self._append_record_text(record_id, "reproduction_steps", step)

    def add_failure(self, record_id: str, failure: str) -> ResearchRecord:
        return self._append_record_text(record_id, "failures", failure)

    def set_promotion_review(self, record_id: str, status: str, note: str = "") -> ResearchRecord:
        if status not in {"not-requested", "requested", "approved", "rejected"}:
            raise ValueError("Unknown promotion review status")
        records = self.list()
        for record in records:
            if record.id == record_id:
                if status in {"requested", "approved"} and record.status != "completed":
                    raise ValueError("Only completed research can enter promotion review")
                if status == "approved" and (not record.evidence or not record.reproduction_steps):
                    raise ValueError("Approved research requires evidence and reproduction steps")
                record.promotion_status = status
                record.promotion_note = note.strip()
                if record.published:
                    record.published = False
                    record.published_at = ""
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def link_context(self, record_id: str, packages: list[str] | None = None,
                     modules: list[str] | None = None, knowledge: list[str] | None = None) -> ResearchRecord:
        """Attach stable public IDs without copying private records into research."""
        records = self.list()
        for record in records:
            if record.id == record_id:
                for field_name, values in (("linked_package_ids", packages),
                                           ("linked_module_ids", modules),
                                           ("linked_knowledge_ids", knowledge)):
                    if values is not None:
                        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
                            raise ValueError("Research links must be non-empty string IDs")
                        setattr(record, field_name, sorted(set(value.strip() for value in values)))
                if record.published:
                    record.published = False
                    record.published_at = ""
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def record_runtime_evidence(self, record_id: str, result: dict,
                                context: IntegrationContext) -> ResearchRecord:
        """Store a sanitized, operation-bound adapter observation.

        Runtime adapters provide evidence; Research owns the durable record.
        No adapter payload or private path is copied into the public catalog.
        """
        if context.capability != "research" or context.capability_state not in {"read-only", "staged"}:
            raise ValueError("Runtime evidence requires a research read-only or staged context")
        if not isinstance(result, dict) or result.get("operation_id") != context.operation_id:
            raise ValueError("Runtime evidence operation does not match integration context")
        allowed = ("operation_id", "field", "loader", "loader_api_version", "game_build",
                    "old_value", "new_value", "readback_verified", "status")
        sanitized = {key: result[key] for key in allowed if key in result}
        if sanitized.get("readback_verified") is not True:
            raise ValueError("Only verified runtime readback may be recorded")
        sanitized["profile_id"] = context.profile_id
        return self.add_evidence(record_id, "runtime-adapter: " + json.dumps(sanitized, sort_keys=True))

    def set_status(self, record_id: str, status: str) -> ResearchRecord:
        if status not in {"planned", "running", "completed", "blocked"}:
            raise ValueError("Unknown research status")
        records = self.list()
        for record in records:
            if record.id == record_id:
                if status == "completed" and not record.evidence:
                    raise ValueError("Add evidence before completing research")
                record.status = status
                if record.published:
                    record.published = False
                    record.published_at = ""
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def publish(self, record_id: str) -> ResearchRecord:
        records = self.list()
        for record in records:
            if record.id == record_id:
                if record.status != "completed" or not record.evidence:
                    raise ValueError("Complete the research and add evidence before publishing")
                record.published = True
                record.published_at = datetime.now(timezone.utc).isoformat()
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def unpublish(self, record_id: str) -> ResearchRecord:
        records = self.list()
        for record in records:
            if record.id == record_id:
                record.published = False
                record.published_at = ""
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def export_summary(self, record: ResearchRecord) -> Path:
        """Export a profile-free research handoff without evidence text."""
        destination = self.path.parent.parent / "exports" / "research" / f"{record.id}.json"
        write_json_atomic(destination, {
            "schema_version": 1,
            "record": {
                "id": record.id, "title": record.title, "hypothesis": record.hypothesis,
                "status": record.status, "evidence_count": len(record.evidence),
                "created_at": record.created_at, "published_at": record.published_at,
                "game_build": record.game_build, "game_version": record.game_version,
                "reproduction_step_count": len(record.reproduction_steps),
                "failure_count": len(record.failures), "promotion_status": record.promotion_status,
                "linked_package_count": len(record.linked_package_ids),
                "linked_module_count": len(record.linked_module_ids),
                "linked_knowledge_count": len(record.linked_knowledge_ids),
            },
            "application_state": "research-summary",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })
        return destination
