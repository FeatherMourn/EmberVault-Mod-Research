"""Contracts for offline research analyzers; execution remains external and sandboxed."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


ALLOWED_EVIDENCE_TYPES = {"offline-static", "synthetic", "staging", "runtime-observation"}


@dataclass(frozen=True)
class AnalyzerSpec:
    analyzer_id: str
    version: str
    input_kinds: tuple[str, ...]
    output_kinds: tuple[str, ...]
    read_only: bool = True
    network_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnalysisResult:
    analyzer_id: str
    analyzer_version: str
    input_hashes: tuple[str, ...]
    output_record_ids: tuple[str, ...]
    build_scope: tuple[str, ...]
    evidence_type: str
    limitations: tuple[str, ...]
    reproducible: bool

    def __post_init__(self) -> None:
        if self.evidence_type not in ALLOWED_EVIDENCE_TYPES:
            raise ValueError("unsupported evidence type")
        if not self.limitations:
            raise ValueError("analysis results must declare limitations")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PipelineRun:
    """Reproducibility record for an externally executed offline analyzer."""
    analyzer: AnalyzerSpec
    result: AnalysisResult
    output_hashes: tuple[str, ...]
    transformations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.analyzer.read_only or self.analyzer.network_allowed:
            raise ValueError("pipeline analyzers must be read-only and offline")
        if self.result.analyzer_id != self.analyzer.analyzer_id or self.result.analyzer_version != self.analyzer.version:
            raise ValueError("pipeline analyzer and result metadata do not match")
        if not self.output_hashes:
            raise ValueError("pipeline results must declare output hashes")
        if not self.transformations:
            raise ValueError("pipeline results must declare transformations")

    def to_dict(self) -> dict[str, Any]:
        return {"analyzer": self.analyzer.to_dict(), "result": self.result.to_dict(),
                "output_hashes": self.output_hashes, "transformations": self.transformations,
                "read_only": True, "network_allowed": False}


def hash_inputs(paths: Iterable[Path]) -> tuple[str, ...]:
    """Hash offline inputs without modifying or executing them."""
    hashes = []
    for path in sorted(paths, key=lambda item: str(item)):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes.append(f"{path}:{digest}")
    return tuple(hashes)
