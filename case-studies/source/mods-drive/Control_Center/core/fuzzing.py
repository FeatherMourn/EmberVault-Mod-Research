"""Deterministic offline malformed-input probes for Control Center validators."""
from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .content_validation import ContentProjectValidator
from .kfc_binary import BinaryField, KfcBinaryError, KfcBinaryLayout


@dataclass(frozen=True)
class FuzzCase:
    name: str
    payload: object


@dataclass(frozen=True)
class FuzzResult:
    name: str
    rejected: bool
    detail: str


class OfflineFuzzService:
    """Run bounded deterministic cases without touching game or package state."""

    def cases(self) -> tuple[FuzzCase, ...]:
        return (
            FuzzCase("negative_field_offset", lambda: KfcBinaryLayout.validate_fields([BinaryField("x", -1, 1)], 4)),
            FuzzCase("overlapping_fields", lambda: KfcBinaryLayout.validate_fields([BinaryField("a", 0, 4), BinaryField("b", 2, 4)], 8)),
            FuzzCase("invalid_alignment", lambda: KfcBinaryLayout.align(1, 3)),
            FuzzCase("invalid_json_manifest", "{not-json"),
            FuzzCase("unsafe_project_reference", {"path": "../outside.json"}),
        )

    def run(self) -> tuple[FuzzResult, ...]:
        results: list[FuzzResult] = []
        for case in self.cases():
            try:
                if callable(case.payload):
                    case.payload()
                    results.append(FuzzResult(case.name, False, "malformed input was accepted"))
                else:
                    with tempfile.TemporaryDirectory() as td:
                        project = Path(td)
                        (project / "mod.json").write_text(str(case.payload), encoding="utf-8")
                        report = ContentProjectValidator().validate(project)
                        results.append(FuzzResult(case.name, not report.valid, "validator completed"))
            except (KfcBinaryError, ValueError, OSError, json.JSONDecodeError) as exc:
                results.append(FuzzResult(case.name, True, str(exc)))
        return tuple(results)

    def assert_safe(self) -> tuple[FuzzResult, ...]:
        results = self.run()
        unsafe = [result for result in results if not result.rejected]
        if unsafe:
            raise AssertionError("Fuzz cases accepted malformed input: " + ", ".join(result.name for result in unsafe))
        return results
