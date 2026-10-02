"""Conservative local runtime status adapter.

This adapter detects processes only. It intentionally does not perform memory
writes or claim Cheat Engine attachment/activation without a supported bridge.
"""
from __future__ import annotations
import subprocess
from dataclasses import dataclass

@dataclass(frozen=True)
class RuntimeStatus:
    game: bool
    cheat_engine: bool
    attached: bool = False
    table_loaded: bool = False
    detail: str = 'No verified Cheat Engine bridge is configured.'

def _running(name: str) -> bool:
    try:
        result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {name}'], capture_output=True, text=True, timeout=2)
        return name.lower() in result.stdout.lower()
    except (OSError, subprocess.SubprocessError):
        return False

def detect() -> RuntimeStatus:
    return RuntimeStatus(_running('Enshrouded.exe'), _running('cheatengine-x86_64.exe') or _running('cheatengine.exe'))
