"""Read-only filtering and comparison for persisted analyzer-run records."""
from __future__ import annotations

from typing import Any, Iterable


def _parts(run: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    pipeline = run.get("pipeline", run)
    return pipeline.get("analyzer", {}), pipeline.get("result", {})


def filter_runs(runs: Iterable[dict[str, Any]], *, analyzer_id: str | None = None,
                version: str | None = None, build: str | None = None) -> list[dict[str, Any]]:
    matches = []
    for run in runs:
        analyzer, result = _parts(run)
        if analyzer_id and analyzer.get("analyzer_id") != analyzer_id:
            continue
        if version and analyzer.get("version") != version:
            continue
        if build and build not in {str(value) for value in result.get("build_scope", [])}:
            continue
        matches.append(run)
    return sorted(matches, key=lambda item: (_parts(item)[0].get("analyzer_id", ""),
                                             _parts(item)[0].get("version", ""),
                                             tuple(_parts(item)[1].get("build_scope", []))))


def compare_runs(before: Iterable[dict[str, Any]], after: Iterable[dict[str, Any]]) -> dict[str, Any]:
    def key(run: dict[str, Any]) -> tuple[Any, ...]:
        analyzer, result = _parts(run)
        return (analyzer.get("analyzer_id"), analyzer.get("version"), tuple(result.get("build_scope", [])))

    left, right = {key(run): run for run in before}, {key(run): run for run in after}
    def display(run_key: tuple[Any, ...]) -> list[Any]:
        return [run_key[0], run_key[1], *run_key[2]]

    changed = []
    for run_key in sorted(set(left) & set(right), key=str):
        if left[run_key] != right[run_key]:
            changed.append({"key": display(run_key), "before": left[run_key], "after": right[run_key]})
    return {"schema_version": 1, "read_only": True, "runtime_approval": False, "actions": [],
            "added": [display(key) for key in sorted(set(right) - set(left), key=str)],
            "removed": [display(key) for key in sorted(set(left) - set(right), key=str)],
            "changed": changed}
