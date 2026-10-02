#!/usr/bin/env python3
"""Conservative offline analysis of Architect player discovery JSONL captures.

This module never opens a process.  It only correlates already-captured evidence;
behavioral correlation is deliberately not promoted to PROVEN.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

REPORT_SCHEMA = "architect.player-discovery-report.v1"
STRONG = "EXPERIMENTAL_STRONG_CORRELATION"
PARTIAL = "EXPERIMENTAL_PARTIAL_CORRELATION"
DISPROVEN = "DISPROVEN_BY_PHASE_BEHAVIOR"
INSUFFICIENT = "UNSOLVED_INSUFFICIENT_EVIDENCE"


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        return [], [{"code": "CAPTURE_NOT_FOUND", "line": None, "detail": str(path)}]
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("JSON value is not an object")
            events.append(value)
        except (json.JSONDecodeError, ValueError) as exc:
            diagnostics.append({"code": "MALFORMED_JSONL_LINE", "line": number,
                                "detail": str(exc)})
    return events, diagnostics


def _number(event: dict[str, Any]) -> float | None:
    raw = event.get("raw") if isinstance(event.get("raw"), dict) else {}
    for key in ("float", "u32", "u16", "value"):
        value = raw.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            return float(value)
    value = event.get("value")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return float(value)
    return None


def _candidate_type(event: dict[str, Any]) -> str:
    interpretation = event.get("interpretation")
    value = interpretation.get("candidateType") if isinstance(interpretation, dict) else None
    if not value:
        value = event.get("candidateType") or event.get("probeId") or "Unknown"
    lowered = str(value).lower()
    for name in ("Health", "Stamina", "Mana", "LocalPlayer"):
        if name.lower() in lowered:
            return name
    return str(value)


def _candidate_parts(event: dict[str, Any]) -> dict[str, Any]:
    candidate = event.get("candidate")
    return candidate if isinstance(candidate, dict) else {}


def _identity(event: dict[str, Any]) -> tuple[str, str]:
    candidate = _candidate_parts(event)
    for key in ("entityId", "ownerPointer", "componentPointer"):
        value = candidate.get(key)
        if value is not None and value != "":
            return key, str(value)
    return "probeId", str(event.get("probeId", "unknown"))


def _median_by_phase(events: Iterable[dict[str, Any]]) -> dict[str, float]:
    values: dict[str, list[float]] = defaultdict(list)
    for event in events:
        value = _number(event)
        phase = event.get("phase")
        if value is not None and isinstance(phase, str):
            values[phase.upper()].append(value)
    return {phase: statistics.median(samples) for phase, samples in sorted(values.items())}


def _direction(before: float, after: float) -> int:
    tolerance = max(1e-6, abs(before) * 1e-5)
    return 1 if after > before + tolerance else (-1 if after < before - tolerance else 0)


def _signal_analysis(kind: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    phases = _median_by_phase(events)
    contradictions: list[str] = []
    matches: list[str] = []
    required: list[str]
    if kind == "Stamina":
        required = ["BASELINE", "SPRINT_ACTIVE", "SPRINT_RECOVERY"]
        if all(p in phases for p in required):
            active = _direction(phases["BASELINE"], phases["SPRINT_ACTIVE"])
            recovery = _direction(phases["SPRINT_ACTIVE"], phases["SPRINT_RECOVERY"])
            if active < 0: matches.append("decreases during SPRINT_ACTIVE")
            elif active > 0: contradictions.append("increases during SPRINT_ACTIVE")
            if recovery > 0: matches.append("increases during SPRINT_RECOVERY")
            elif recovery < 0: contradictions.append("decreases during SPRINT_RECOVERY")
    elif kind == "Health":
        required = ["DAMAGE", "HEAL"]
        before_keys = [p for p in ("BASELINE", "SPRINT_ACTIVE", "SPRINT_RECOVERY", "MANA_SPEND", "MANA_RECOVERY") if p in phases]
        if all(p in phases for p in required) and before_keys:
            before = phases[before_keys[-1]]
            damage = _direction(before, phases["DAMAGE"])
            heal = _direction(phases["DAMAGE"], phases["HEAL"])
            if damage < 0: matches.append("decreases during DAMAGE")
            elif damage > 0: contradictions.append("increases during DAMAGE")
            if heal > 0: matches.append("increases during HEAL")
            elif heal < 0: contradictions.append("decreases during HEAL")
        else:
            required = ["PRE_DAMAGE_SAMPLE", "DAMAGE", "HEAL"]
    elif kind == "Mana":
        required = ["BASELINE", "MANA_SPEND"]
        if all(p in phases for p in required):
            spend = _direction(phases["BASELINE"], phases["MANA_SPEND"])
            if spend < 0: matches.append("decreases during MANA_SPEND")
            elif spend > 0: contradictions.append("increases during MANA_SPEND")
            if "SPRINT_ACTIVE" in phases and _direction(phases["BASELINE"], phases["SPRINT_ACTIVE"]) < 0:
                contradictions.append("also decreases during SPRINT_ACTIVE; may be Stamina-like")
    else:
        required = []

    missing = [p for p in required if p not in phases]
    expected_matches = 2 if kind in ("Stamina", "Health") else 1
    if missing:
        status = INSUFFICIENT
    elif contradictions:
        status = DISPROVEN
    elif len(matches) >= expected_matches:
        status = STRONG
    elif matches:
        status = PARTIAL
    else:
        status = INSUFFICIENT
    return {"candidateType": kind, "status": status, "phaseMedians": phases,
            "matchedPatterns": matches, "missingEvidence": missing,
            "contradictions": contradictions, "observationCount": len(events)}


def analyze_events(events: Iterable[dict[str, Any]], diagnostics: Iterable[dict[str, Any]] = ()) -> dict[str, Any]:
    valid = [e for e in events if isinstance(e, dict)]
    valid.sort(key=lambda e: (str(e.get("sessionId", "")), int(e.get("sequence", 0) or 0),
                              str(e.get("probeId", ""))))
    sessions = sorted({str(e["sessionId"]) for e in valid if e.get("sessionId") is not None})
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in valid:
        # BEGIN/END/phase-marker records are useful session evidence but are
        # not candidates.  In particular, a safe zero-probe capture must not
        # manufacture an "unknown" candidate from marker-only JSONL.
        if _number(event) is not None or _candidate_parts(event):
            groups[_identity(event)].append(event)

    candidates = []
    for (identity_kind, identity_value), candidate_events in sorted(groups.items()):
        signal_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in candidate_events:
            signal_groups[_candidate_type(event)].append(event)
        signals = [_signal_analysis(kind, rows) for kind, rows in sorted(signal_groups.items())]
        candidate_data = [_candidate_parts(e) for e in candidate_events]
        sides = sorted({str(c.get("side")) for c in candidate_data if c.get("side")})
        pointers = {key: sorted({str(c[key]) for c in candidate_data if c.get(key) is not None})
                    for key in ("ownerPointer", "componentPointer")}
        probes = sorted({str(e.get("probeId")) for e in candidate_events if e.get("probeId")})
        contradictions = sorted({item for signal in signals for item in signal["contradictions"]})
        phases = {str(e.get("phase", "")).upper() for e in candidate_events}
        if "FAST_TRAVEL" in phases and "POST_TRAVEL" in phases:
            travel = "stable" if any(e.get("phase", "").upper() == "POST_TRAVEL" for e in candidate_events) else "lost"
        elif "POST_TRAVEL" in phases:
            travel = "reacquired"
        else:
            travel = "unknown"
        candidates.append({
            "identity": {identity_kind: identity_value},
            "localPlayerOwnership": "EXPERIMENTAL" if len(probes) > 1 or len(signals) > 1 else "UNSOLVED",
            "signals": signals,
            "travelContinuity": travel,
            "clientServer": {"observedSides": sides, "possibleDuplication": len(sides) > 1},
            "pointers": pointers,
            "evidenceSources": probes,
            "contradictions": contradictions,
        })
    observed_phases = sorted({str(e.get("phase")).upper() for e in valid if e.get("phase")})
    return {"schema": REPORT_SCHEMA, "sessions": sessions, "eventCount": len(valid),
            "candidateCount": len(candidates), "candidates": candidates,
            "observedPhases": observed_phases,
            "analysisStatus": "EXPERIMENTAL_CANDIDATES_FOUND" if candidates else INSUFFICIENT,
            "diagnostics": sorted(list(diagnostics), key=lambda d: (str(d.get("code")), d.get("line") or 0)),
            "evidenceNotice": "Behavioral correlation is experimental and is not proof of ownership or authority."}


def analyze_file(path: Path) -> dict[str, Any]:
    events, diagnostics = load_jsonl(path)
    return analyze_events(events, diagnostics)


def render_text(report: dict[str, Any]) -> str:
    lines = ["Player Discovery Report", "=======================",
             f"Events: {report['eventCount']}  Candidates: {report['candidateCount']}", ""]
    for candidate in report["candidates"]:
        identity = next(iter(candidate["identity"].items()))
        lines.append(f"Candidate {identity[0]}={identity[1]}")
        for signal in candidate["signals"]:
            lines.append(f"  {signal['candidateType']}: {signal['status']}")
        lines.append(f"  Travel continuity: {candidate['travelContinuity']}")
        for contradiction in candidate["contradictions"]:
            lines.append(f"  Contradiction: {contradiction}")
        lines.append("")
    lines.append(report["evidenceNotice"])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=root / "bridge" / "player_discovery.jsonl")
    parser.add_argument("--output", type=Path, default=root / "bridge" / "player_discovery_report.json")
    parser.add_argument("--text-output", type=Path)
    args = parser.parse_args()
    report = analyze_file(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.text_output:
        args.text_output.parent.mkdir(parents=True, exist_ok=True)
        args.text_output.write_text(render_text(report), encoding="utf-8")
    print(f"events={report['eventCount']} candidates={report['candidateCount']}")
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
