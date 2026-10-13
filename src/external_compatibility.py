"""Read-only comparison of external tool metadata to Ember Vault boundaries."""
from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = ("manifest", "profile", "settings", "package")


def compare_external_metadata(external: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    """Compare synthetic metadata without executing or importing the external tool."""
    matches: list[str] = []
    gaps: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in external:
            gaps.append(f"missing external field: {field}")
            continue
        expected = contract.get(field, {})
        observed = external[field]
        if isinstance(expected, dict) and isinstance(observed, dict):
            missing = sorted(set(expected) - set(observed))
            if missing:
                gaps.append(f"{field} missing contract keys: {', '.join(missing)}")
            else:
                matches.append(field)
        else:
            matches.append(field)
    return {
        "kind": "external-compatibility-comparison",
        "read_only": True,
        "runtime_approval": False,
        "matches": matches,
        "gaps": gaps,
        "state": "compatible-with-gaps" if gaps else "compatible",
        "limitations": [
            "Synthetic metadata comparison does not prove runtime compatibility.",
            "No external code was executed and no files were installed or modified.",
        ],
    }
