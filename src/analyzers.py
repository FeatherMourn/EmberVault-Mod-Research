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


def validate_offline_inputs(paths: Iterable[Path], approved_root: Path) -> tuple[Path, ...]:
    """Validate input files stay inside an approved offline research root."""
    root = approved_root.resolve()
    validated = []
    for raw_path in paths:
        path = Path(raw_path)
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as error:
            raise ValueError("offline analyzer input escapes the approved root") from error
        if not resolved.is_file():
            raise ValueError("offline analyzer input must be an existing file")
        validated.append(resolved)
    return tuple(sorted(validated, key=str))


def validate_offline_execution(*, approved_root: Path, working_directory: Path,
                               read_only: bool = True, network_allowed: bool = False) -> Path:
    """Validate a future offline execution request without launching anything."""
    if not read_only or network_allowed:
        raise ValueError("offline execution must be read-only and network-disabled")
    root = approved_root.resolve()
    working = working_directory.resolve()
    try:
        working.relative_to(root)
    except ValueError as error:
        raise ValueError("offline execution directory escapes the approved root") from error
    if not working.is_dir():
        raise ValueError("offline execution directory must exist")
    return working


def build_execution_plan(spec: AnalyzerSpec, inputs: Iterable[Path], *, approved_root: Path,
                         working_directory: Path, transformations: Iterable[str]) -> dict[str, Any]:
    """Create a reproducible, plan-only analyzer request."""
    if not spec.read_only or spec.network_allowed:
        raise ValueError("execution plans must be read-only and network-disabled")
    validated = validate_offline_inputs(inputs, approved_root)
    working = validate_offline_execution(approved_root=approved_root, working_directory=working_directory)
    steps = tuple(str(step) for step in transformations if str(step))
    if not steps:
        raise ValueError("execution plans require transformations")
    return {"schema_version": 1, "analyzer": spec.to_dict(), "inputs": [str(path) for path in validated],
            "input_hashes": list(hash_inputs(validated)), "working_directory": str(working),
            "transformations": list(steps), "read_only": True, "network_allowed": False,
            "executed": False, "runtime_approval": False}


def validate_execution_plan(plan: dict[str, Any], spec: AnalyzerSpec) -> dict[str, Any]:
    """Validate a future runner request without executing the plan."""
    analyzer = plan.get("analyzer", {})
    if analyzer.get("analyzer_id") != spec.analyzer_id or analyzer.get("version") != spec.version:
        raise ValueError("execution plan analyzer does not match the supplied contract")
    if plan.get("read_only") is not True or plan.get("network_allowed") is not False:
        raise ValueError("execution plan safety flags are invalid")
    if plan.get("executed") is not False or plan.get("runtime_approval") is not False:
        raise ValueError("execution plan must remain unexecuted and runtime-unapproved")
    if not plan.get("inputs") or not plan.get("transformations"):
        raise ValueError("execution plan requires inputs and transformations")
    return {"schema_version": 1, "accepted": True, "read_only": True,
            "network_allowed": False, "executed": False, "runtime_approval": False,
            "analyzer_id": spec.analyzer_id, "analyzer_version": spec.version}
