"""Conservative automatic recovery after authoritative EML failure states."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess

from .platform_services import RuntimeHealthService
from .recovery import ModQuarantineService, QuarantineRecord


@dataclass(frozen=True)
class CrashRecoveryResult:
    status: str
    message: str
    candidates: tuple[str, ...] = ()
    record: QuarantineRecord | None = None


class CrashRecoveryService:
    """Automatically quarantine only one unambiguous direct-child mod candidate."""

    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir).resolve()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine = ModQuarantineService(state_dir)
        self.health = RuntimeHealthService()
        self.state_path = self.state_dir / "crash-recovery-state.json"

    def _load_state(self) -> dict[str, str]:
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}

    def _remember_log(self, log_path: Path) -> str:
        digest = hashlib.sha256(Path(log_path).read_bytes()).hexdigest()
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"processed_log": str(Path(log_path).resolve()), "processed_sha256": digest}, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)
        return digest

    @staticmethod
    def _running() -> bool:
        try:
            output = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq Enshrouded.exe"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            return "Enshrouded.exe" in output
        except (OSError, subprocess.SubprocessError):
            # Recovery is destructive to the mod directory, so uncertainty is
            # treated as running rather than risking a live-file move.
            return True

    def recover(self, game_dir: Path) -> CrashRecoveryResult:
        game_dir = Path(game_dir).resolve()
        if self._running():
            return CrashRecoveryResult("not_triggered", "Enshrouded is still running or its process state is unavailable; recovery was not triggered.")
        runtime = self.health.inspect(game_dir)
        if runtime.status != "failed":
            return CrashRecoveryResult("not_triggered", f"Runtime state is {runtime.status}; automatic recovery was not triggered.")
        if not runtime.log_path:
            return CrashRecoveryResult("review_required", "Runtime failed but no authoritative log was found.")
        try:
            log_digest = hashlib.sha256(runtime.log_path.read_bytes()).hexdigest()
        except OSError:
            return CrashRecoveryResult("review_required", "The authoritative failure log could not be read.")
        previous = self._load_state()
        if previous.get("processed_log") == str(runtime.log_path.resolve()) and previous.get("processed_sha256") == log_digest:
            return CrashRecoveryResult("already_processed", "This failure log has already been processed; no module was moved again.")
        candidates = tuple(self.quarantine.candidates_from_log(runtime.log_path))
        existing = tuple(candidate for candidate in candidates if (game_dir / "mods" / candidate / "mod.json").is_file())
        if len(existing) != 1:
            return CrashRecoveryResult("review_required", "Automatic recovery requires exactly one identifiable mod candidate.", existing)
        record = self.quarantine.quarantine(game_dir / "mods", existing[0], "automatic recovery after authoritative runtime failure")
        self._remember_log(runtime.log_path)
        return CrashRecoveryResult("quarantined", f"Automatically quarantined {existing[0]} for reversible recovery.", existing, record)
