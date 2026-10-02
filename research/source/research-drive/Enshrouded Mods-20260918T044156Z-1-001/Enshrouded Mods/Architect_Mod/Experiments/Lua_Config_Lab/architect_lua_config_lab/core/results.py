"""Local experiment result recording.

Keeps a local JSON log of tested edits/profiles. This is *separate* from the
canonical Architect project evidence state; the app never auto-promotes
canonical evidence.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

RESULT_VALUES = {
    "PASS",
    "NO_EFFECT",
    "CRASH",
    "LOAD_FAILURE",
    "BEHAVIOR_UNCLEAR",
    "NOT_TESTED",
}


def _today() -> str:
    return date.today().isoformat()


class ResultStore:
    """Append-only JSON result log."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._records: List[Dict[str, Any]] = []
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                self._records = data.get("records", [])
            except (json.JSONDecodeError, OSError):
                self._records = []

    def add(
        self,
        profile: str,
        field: str,
        requested_value: Any,
        result: str,
        notes: str = "",
        game_build: str = "",
        resource_type: str = "",
        test_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        if result not in RESULT_VALUES:
            raise ValueError("unknown result value %r" % result)
        record = {
            "game_build": game_build,
            "profile": profile,
            "resource_type": resource_type,
            "field": field,
            "requested_value": requested_value,
            "result": result,
            "notes": notes,
            "test_date": test_date or _today(),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        self._records.append(record)
        self._save()
        return record

    def records(self) -> List[Dict[str, Any]]:
        return list(self._records)

    def _save(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        payload = {"schema": "architect.lua_config_lab.results.v1", "records": self._records}
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
