"""User-facing display vocabulary.

Pure mapping helpers (no UI dependency) that translate internal engineering
terms into the friendly terminology used in normal mode.
"""

from __future__ import annotations

# Evidence state -> friendly badge (section 18).
FRIENDLY_STATUS = {
    "PROVEN_STARTUP_EFFECT": "\u2713 Tested",
    "SCHEMA_VALIDATED": "\u25c7 Schema Available",
    "EXPERIMENTAL": "\U0001f9ea Experimental",
    "DISPROVEN": "\u2715 Known Not Working",
    "UNSUPPORTED": "\u26a0 Unsupported",
}

# Target mode -> friendly wording (section 16: avoid FIRST/MATCH/selector).
FRIENDLY_TARGET = {
    "first": "First matching resource",
    "all": "All resources of this type",
    "match": "Resource matching a condition",
}


def friendly_status(evidence_state: str) -> str:
    return FRIENDLY_STATUS.get(evidence_state, evidence_state)


def friendly_target(mode: str) -> str:
    return FRIENDLY_TARGET.get(mode, mode)


def access_level_label(access_level: str) -> str:
    return "Advanced" if access_level == "ADVANCED" else "Standard"
