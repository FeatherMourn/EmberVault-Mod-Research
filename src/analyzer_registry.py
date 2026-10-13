"""Read-only registry for independently supplied offline analyzer contracts."""
from __future__ import annotations

from .analyzers import AnalyzerSpec, PipelineRun


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

    def record_pipeline_run(self, run: PipelineRun) -> dict[str, object]:
        """Attach a registered analyzer contract to a reproducibility record."""
        registered = self.get(run.analyzer.analyzer_id, run.analyzer.version)
        if registered != run.analyzer:
            raise ValueError("pipeline analyzer does not match its registered contract")
        return {"schema_version": 1, "read_only": True, "runtime_approval": False,
                "analyzer_contract": registered.to_dict(), "pipeline": run.to_dict()}
