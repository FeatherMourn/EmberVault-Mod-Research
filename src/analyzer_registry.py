"""Read-only registry for independently supplied offline analyzer contracts."""
from __future__ import annotations

from .analyzers import AnalyzerSpec


class AnalyzerRegistry:
    """Store analyzer specifications without loading or executing analyzers."""

    def __init__(self) -> None:
        self._specs: dict[tuple[str, str], AnalyzerSpec] = {}

    def register(self, spec: AnalyzerSpec) -> None:
        if not spec.read_only or spec.network_allowed:
            raise ValueError("registered analyzers must be read-only and offline")
        key = (spec.analyzer_id, spec.version)
        if key in self._specs:
            raise ValueError("analyzer identity is already registered")
        self._specs[key] = spec

    def get(self, analyzer_id: str, version: str) -> AnalyzerSpec:
        try:
            return self._specs[(analyzer_id, version)]
        except KeyError as error:
            raise KeyError(f"unknown analyzer: {analyzer_id}@{version}") from error

    def manifest(self) -> list[dict[str, object]]:
        return [self._specs[key].to_dict() for key in sorted(self._specs)]
