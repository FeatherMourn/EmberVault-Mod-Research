"""Character editor project data; intentionally separate from save mutation."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from dataclasses import asdict, dataclass, field
from pathlib import Path
from .storage import write_json_atomic
from .save_manager import SaveManagerError, SaveManagerService


@dataclass
class CharacterRecord:
    id: str
    name: str
    profile_id: str
    notes: str = ""
    planned_level: int = 1
    build_goals: list[str] = field(default_factory=list)
    progression_plan: list[str] = field(default_factory=list)
    equipment_notes: list[str] = field(default_factory=list)
    skill_notes: list[str] = field(default_factory=list)
    verified_backup_id: str = ""
    build_template: str = "general"
    version: int = 1
    history: list[dict] = field(default_factory=list)


class CharacterService:
    def __init__(self, root: Path, saves: SaveManagerService | None = None):
        self.path = Path(root) / "characters" / "records.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.saves = saves

    def list(self) -> list[CharacterRecord]:
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
                    record = CharacterRecord(**item)
                except (TypeError, ValueError):
                    continue
                if isinstance(record.planned_level, bool) or not isinstance(record.planned_level, int) or not 1 <= record.planned_level <= 50:
                    record.planned_level = 1
                for field_name in ("build_goals", "progression_plan", "equipment_notes", "skill_notes"):
                    values = getattr(record, field_name)
                    if not isinstance(values, list):
                        values = []
                    setattr(record, field_name, [value.strip() for value in values if isinstance(value, str) and value.strip()])
                if not isinstance(record.verified_backup_id, str):
                    record.verified_backup_id = ""
                if not isinstance(record.build_template, str) or not record.build_template.strip():
                    record.build_template = "general"
                if not isinstance(record.version, int) or record.version < 1:
                    record.version = 1
                if not isinstance(record.history, list):
                    record.history = []
                records.append(record)
            return records
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return []

    def create(self, name: str, profile_id: str, notes: str = "", build_goals: list[str] | None = None, progression_plan: list[str] | None = None, equipment_notes: list[str] | None = None, skill_notes: list[str] | None = None, verified_backup_id: str = "") -> CharacterRecord:
        if not name.strip() or not profile_id.strip():
            raise ValueError("Character name and profile are required")
        record = CharacterRecord(f"EV-CHAR-{uuid.uuid4().hex[:8].upper()}", name.strip(), profile_id, notes.strip(), 1,
                                 self._normalize_list(build_goals), self._normalize_list(progression_plan),
                                 self._normalize_list(equipment_notes), self._normalize_list(skill_notes), verified_backup_id.strip())
        records = self.list()
        records.append(record)
        write_json_atomic(self.path, [asdict(item) for item in records])
        return record

    @staticmethod
    def _normalize_list(values: list[str] | None) -> list[str]:
        if values is None:
            return []
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("Character planning lists must contain non-empty strings")
        return list(dict.fromkeys(value.strip() for value in values))

    def update_plan(self, record_id: str, build_goals: list[str], progression_plan: list[str], equipment_notes: list[str], skill_notes: list[str], verified_backup_id: str = "") -> CharacterRecord:
        records = self.list()
        for record in records:
            if record.id == record_id:
                if verified_backup_id.strip() and self.saves:
                    try:
                        self.saves.require_verified_backup(verified_backup_id.strip(), profile_id=record.profile_id)
                    except SaveManagerError as exc:
                        raise ValueError("Character plan requires a checksum-valid backup") from exc
                record.build_goals = self._normalize_list(build_goals)
                record.progression_plan = self._normalize_list(progression_plan)
                record.equipment_notes = self._normalize_list(equipment_notes)
                record.skill_notes = self._normalize_list(skill_notes)
                record.verified_backup_id = verified_backup_id.strip()
                record.version += 1
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def simulate_progression(self, record_id: str, target_level: int) -> dict:
        if isinstance(target_level, bool) or not isinstance(target_level, int) or not 1 <= target_level <= 50:
            raise ValueError("Target level must be between 1 and 50")
        record = next((item for item in self.list() if item.id == record_id), None)
        if record is None:
            raise KeyError(record_id)
        return {"character_id": record.id, "from_level": record.planned_level,
                "target_level": target_level, "levels_to_gain": max(0, target_level - record.planned_level),
                "planned_steps": list(record.progression_plan), "application_state": "plan-only"}

    def compare_equipment(self, left_id: str, right_id: str) -> dict:
        records = {item.id: item for item in self.list()}
        if left_id not in records or right_id not in records:
            raise KeyError("Character comparison record not found")
        left, right = records[left_id], records[right_id]
        return {"left": {"id": left.id, "equipment": list(left.equipment_notes)},
                "right": {"id": right.id, "equipment": list(right.equipment_notes)},
                "application_state": "plan-only"}

    def validate_plan(self, record_id: str) -> list[str]:
        for record in self.list():
            if record.id == record_id:
                issues = []
                if not record.build_goals:
                    issues.append("Add at least one build goal")
                if not record.progression_plan:
                    issues.append("Add a progression plan")
                if not record.equipment_notes:
                    issues.append("Add equipment notes")
                if not record.skill_notes:
                    issues.append("Add skill notes")
                return issues
        raise KeyError(record_id)

    def stage_level(self, record_id: str, level: int) -> CharacterRecord:
        if isinstance(level, bool) or not isinstance(level, int) or not 1 <= level <= 50:
            raise ValueError("Planned level must be between 1 and 50")
        records = self.list()
        for record in records:
            if record.id == record_id:
                record.planned_level = level
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def update_notes(self, record_id: str, notes: str) -> CharacterRecord:
        records = self.list()
        for record in records:
            if record.id == record_id:
                record.notes = notes.strip()
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def set_template(self, record_id: str, template: str) -> CharacterRecord:
        if template not in {"general", "tank", "damage", "support", "gatherer"}:
            raise ValueError("Unknown character build template")
        records = self.list()
        for record in records:
            if record.id == record_id:
                record.build_template = template
                record.version += 1
                write_json_atomic(self.path, [asdict(item) for item in records])
                return record
        raise KeyError(record_id)

    def export(self, record: CharacterRecord) -> Path:
        """Export a character plan without modifying save data."""
        destination = self.path.parent.parent / "exports" / "character-plans" / f"{record.id}.json"
        write_json_atomic(destination, {
            "schema_version": 1,
            "character": asdict(record),
            "application_state": "plan-only",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })
        return destination
