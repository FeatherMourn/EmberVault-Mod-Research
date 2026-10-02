"""Audited Save Manager use cases."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .logging_service import StructuredLogService
from .operations import Operation, OperationService, OperationStatus
from .save_manager import SaveManagerService, SaveSnapshot


@dataclass(frozen=True)
class WorkflowResult:
    operation: Operation
    snapshot: SaveSnapshot | None = None
    payload: dict | None = None


class SaveWorkflowService:
    def __init__(self, saves: SaveManagerService, operations: OperationService, logs: StructuredLogService):
        self.saves = saves
        self.operations = operations
        self.logs = logs
        self._restore_previews: dict[tuple[str, str], str] = {}

    def inspect(self, save_dir: Path, profile_id: str | None = None) -> WorkflowResult:
        operation = self.operations.start("save-inspection", profile_id=profile_id)
        try:
            files = self.saves.inspect(save_dir)
            operation = self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Inspected {len(files)} files")
            self.logs.info("Save inspection completed", operation_id=operation.id, profile_id=profile_id, details={"file_count": len(files)})
            return WorkflowResult(operation, payload={"files": files})
        except Exception as exc:
            operation = self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self.logs.error("Save inspection failed", operation_id=operation.id, profile_id=profile_id, details={"error": str(exc)})
            raise

    def backup(self, save_dir: Path, label: str, profile_id: str | None = None) -> WorkflowResult:
        operation = self.operations.start("save-backup", profile_id=profile_id)
        try:
            snapshot = self.saves.backup(save_dir, label)
            operation = self.operations.finish(operation, OperationStatus.SUCCEEDED, "Backup verified", snapshot.id)
            self.logs.info("Save backup verified", operation_id=operation.id, profile_id=profile_id, details={"backup_id": snapshot.id})
            return WorkflowResult(operation, snapshot)
        except Exception as exc:
            operation = self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self.logs.error("Save backup failed", operation_id=operation.id, profile_id=profile_id, details={"error": str(exc)})
            raise

    def preview_restore(self, backup_id: str, destination: Path, profile_id: str | None = None) -> WorkflowResult:
        operation = self.operations.start("save-restore-preview", profile_id=profile_id)
        try:
            payload = self.saves.preview_restore(backup_id, destination)
            self._restore_previews[(profile_id or "", str(Path(destination).resolve()))] = backup_id
            operation = self.operations.finish(operation, OperationStatus.SUCCEEDED, "Restore preview generated", backup_id)
            self.logs.info("Restore preview generated", operation_id=operation.id, profile_id=profile_id, details=payload)
            return WorkflowResult(operation, payload=payload)
        except Exception as exc:
            operation = self.operations.finish(operation, OperationStatus.FAILED, str(exc), backup_id)
            self.logs.error("Restore preview failed", operation_id=operation.id, profile_id=profile_id, details={"error": str(exc)})
            raise

    def verify(self, backup_id: str, profile_id: str | None = None) -> WorkflowResult:
        operation = self.operations.start("save-verification", profile_id=profile_id)
        try:
            if not self.saves.verify_backup(backup_id):
                raise ValueError("Backup verification failed")
            operation = self.operations.finish(operation, OperationStatus.SUCCEEDED, "Backup verified", backup_id)
            self.logs.info("Save backup re-verified", operation_id=operation.id, profile_id=profile_id, details={"backup_id": backup_id})
            return WorkflowResult(operation, payload={"verified": True, "backup_id": backup_id})
        except Exception as exc:
            operation = self.operations.finish(operation, OperationStatus.FAILED, str(exc), backup_id)
            self.logs.error("Save backup verification failed", operation_id=operation.id, profile_id=profile_id, details={"error": str(exc)})
            raise

    def restore(self, backup_id: str, destination: Path, profile_id: str | None = None) -> WorkflowResult:
        operation = self.operations.start("save-restore", profile_id=profile_id)
        try:
            preview_key = (profile_id or "", str(Path(destination).resolve()))
            if self._restore_previews.get(preview_key) != backup_id:
                raise ValueError("Restore preview required for the selected backup and destination")
            self._restore_previews.pop(preview_key, None)
            current = self.saves.backup(destination, "automatic-before-restore")
            self.saves.restore(backup_id, destination, current_backup=current)
            operation = self.operations.finish(operation, OperationStatus.SUCCEEDED, "Restore verified", current.id)
            self.logs.info("Save restore verified", operation_id=operation.id, profile_id=profile_id, details={"restored_backup": backup_id, "current_backup": current.id})
            return WorkflowResult(operation, current)
        except Exception as exc:
            operation = self.operations.finish(operation, OperationStatus.FAILED, str(exc), backup_id)
            self.logs.error("Save restore failed", operation_id=operation.id, profile_id=profile_id, details={"error": str(exc)})
            raise
