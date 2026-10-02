"""Durable operation tracking for reviewable actions."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

from .integration import IntegrationContext


class OperationStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Operation:
    id: str
    operation_type: str
    started_at: str
    status: str = OperationStatus.STARTED
    finished_at: str | None = None
    profile_id: str | None = None
    package_id: str | None = None
    backup_id: str | None = None
    capability: str | None = None
    capability_state: str | None = None
    recovery_expectation: str | None = None
    message: str = ""


class OperationService:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def start(self, operation_type: str, **context) -> Operation:
        capability = context.get("capability") or self._capability_for(operation_type)
        capability_state = context.get("capability_state") or self._state_for(operation_type)
        recovery_expectation = context.get("recovery_expectation") or self._recovery_for(operation_type)
        operation = Operation(
            id=f"EV-OP-{uuid.uuid4().hex[:8].upper()}",
            operation_type=operation_type,
            started_at=datetime.now(timezone.utc).isoformat(),
            profile_id=context.get("profile_id"), package_id=context.get("package_id"),
            capability=capability,
            capability_state=capability_state,
            recovery_expectation=recovery_expectation,
        )
        self._append(operation)
        return operation

    @staticmethod
    def _capability_for(operation_type: str) -> str:
        prefix = operation_type.split("-", 1)[0]
        return {
            "package": "mods", "module": "mods", "tuning": "tuning",
            "research": "research", "knowledge": "knowledge",
            "content": "content-creator", "character": "character-tools",
            "trainer": "trainer", "save": "save-manager",
            "catalog": "catalog", "troubleshooter": "operations",
        }.get(prefix, "operations")

    @staticmethod
    def _state_for(operation_type: str) -> str:
        if any(token in operation_type for token in ("deploy", "restore", "rollback")):
            return "staged"
        if any(token in operation_type for token in ("research", "trainer", "content", "character")):
            return "plan-only"
        if any(token in operation_type for token in ("inspection", "verify", "scan", "export", "catalog")):
            return "read-only"
        return "ready"

    @staticmethod
    def _recovery_for(operation_type: str) -> str:
        if any(token in operation_type for token in ("deploy", "restore", "rollback", "tuning")):
            return "verified backup or rollback required"
        if any(token in operation_type for token in ("research", "trainer", "content", "character")):
            return "no live mutation; preserve source record"
        return "retain operation record for review"

    def finish(self, operation: Operation, status: OperationStatus, message: str = "", backup_id: str | None = None) -> Operation:
        operation.status = status
        operation.message = message
        operation.backup_id = backup_id or operation.backup_id
        operation.finished_at = datetime.now(timezone.utc).isoformat()
        self._append(operation)
        return operation

    @staticmethod
    def integration_context(operation: Operation) -> IntegrationContext:
        """Return the validated handoff context carried by an operation."""
        if not all((operation.capability, operation.capability_state, operation.recovery_expectation)):
            raise ValueError("Operation is missing cross-module integration metadata")
        return IntegrationContext.from_operation(
            operation,
            capability=operation.capability,
            capability_state=operation.capability_state,
            recovery_expectation=operation.recovery_expectation,
        )

    def list_recent(self, limit: int = 20) -> list[Operation]:
        """Return the latest operation records, newest first."""
        if not self.path.exists():
            return []
        records: dict[str, Operation] = {}
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    try:
                        operation = Operation(**json.loads(line))
                    except (ValueError, TypeError, json.JSONDecodeError):
                        continue
                    if (not isinstance(operation.id, str) or not operation.id.strip()
                            or not isinstance(operation.operation_type, str) or not operation.operation_type.strip()
                            or operation.status not in {item.value for item in OperationStatus}):
                        continue
                    records[operation.id] = operation
        latest = list(records.values())[-max(0, limit):]
        return list(reversed(latest))

    def _append(self, operation: Operation) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(operation), sort_keys=True) + "\n")
