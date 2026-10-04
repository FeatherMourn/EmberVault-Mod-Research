"""Offline package-content checks for the research module."""
from __future__ import annotations

from pathlib import Path


REQUIRED_FILES = ("module.json", "pyproject.toml", "src/research_worker.py", "ROADMAP.md")


def verify_package_contents(root: Path) -> list[str]:
    """Return missing required release files; never builds or installs anything."""
    return [path for path in REQUIRED_FILES if not (root / path).is_file()]
