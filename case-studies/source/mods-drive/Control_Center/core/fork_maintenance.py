"""Read-only maintenance status for the local EML/KFC fork."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ForkStatus:
    repository: Path
    head: str | None
    upstream: str | None
    dirty: bool
    modified_files: tuple[str, ...]
    workspace_crates: tuple[str, ...]
    issues: tuple[str, ...]


class ForkMaintenanceService:
    """Inspect fork health without running builds or mutating Git state."""

    def inspect(self, repository: Path) -> ForkStatus:
        repository = Path(repository).resolve()
        issues: list[str] = []
        if not (repository / ".git").exists():
            return ForkStatus(repository, None, None, False, (), self._crates(repository), ("Git repository is missing.",))
        head = self._run(repository, ["git", "rev-parse", "HEAD"])
        remote = self._run(repository, ["git", "remote", "get-url", "origin"])
        raw_status = self._run(repository, ["git", "status", "--short"]) or ""
        modified = tuple(line[3:] for line in raw_status.splitlines() if len(line) >= 4)
        if modified:
            issues.append("Working tree contains uncommitted changes.")
        crates = self._crates(repository)
        if not crates:
            issues.append("No Rust workspace crates were detected.")
        return ForkStatus(repository, head, remote, bool(modified), modified, crates, tuple(issues))

    @staticmethod
    def _run(repository: Path, command: list[str]) -> str | None:
        try:
            result = subprocess.run(command, cwd=repository, capture_output=True, text=True, timeout=10, check=False)
        except (OSError, subprocess.SubprocessError):
            return None
        return result.stdout.strip() if result.returncode == 0 else None

    @staticmethod
    def _crates(repository: Path) -> tuple[str, ...]:
        crates: list[str] = []
        for cargo in sorted(repository.glob("crates/*/Cargo.toml")):
            crates.append(cargo.parent.name)
        return tuple(crates)
