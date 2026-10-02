"""Helpers for the packed color representation used by ItemInfo."""
from __future__ import annotations

import re


def hex_to_packed_color(value: str) -> int:
    """Convert #RRGGBB or #RRGGBBAA into the game's packed RGBA integer."""
    text = str(value or "").strip().lstrip("#")
    if len(text) == 6:
        text += "FF"
    if len(text) != 8 or not re.fullmatch(r"[0-9a-fA-F]{8}", text):
        raise ValueError("color must be #RRGGBB or #RRGGBBAA")
    red, green, blue, alpha = (int(text[i:i + 2], 16) for i in range(0, 8, 2))
    return (alpha << 24) | (blue << 16) | (green << 8) | red


def packed_color_plan(colors: dict[str, str]) -> dict[str, object]:
    """Build the three-slot ItemInfo color intent from wizard swatches."""
    return {
        "schema": "control_center.item_color_combination_plan.v1",
        "state": "research-only",
        "runtime_field": "itemColorCombinationSetup",
        "color0": hex_to_packed_color(colors.get("frame", "#FFFFFF")),
        "color1": hex_to_packed_color(colors.get("bedding", "#FFFFFF")),
        "color2": hex_to_packed_color(colors.get("trim", "#FFFFFF")),
        "isSet": True,
        "slot_labels": {"color0": "frame", "color1": "bedding", "color2": "trim"},
        "required_evidence": "same-build catalog and placed-world visual screenshots",
    }
