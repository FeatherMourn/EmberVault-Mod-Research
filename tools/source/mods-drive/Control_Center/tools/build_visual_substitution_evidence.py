"""Build structured visual-substitution evidence from one bounded EML log window."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build(log_path: Path, probe_id: str, start: int = 0, end: int | None = None,
          build_id: str | None = None, probe_uninstalled: bool = False,
          stable_profile_restored: bool = False, assignment_only: bool = False) -> dict:
    raw = log_path.read_bytes()
    window = raw[start:end]
    text = window.decode("utf-8", errors="replace")
    def messages(marker: str) -> list[str]:
        return [line for line in text.splitlines() if marker in line]
    assignments = messages("VISUAL_ASSIGNMENT")
    registrations = messages("REGISTERED|itemId=")
    placements = messages("PLACED_ENTITY|")
    panic = "panic" in text.lower() or "fatal error" in text.lower()
    assignment = assignments[-1] if assignments else ""
    before = after = ""
    if "before=" in assignment:
        before = assignment.split("before=", 1)[1].split("|", 1)[0]
    if "after=" in assignment:
        after = assignment.split("after=", 1)[1].split("\"", 1)[0].split("}", 1)[0]
    return {
        "schema": "control_center.registered_visual_substitution_fresh_evidence.v1",
        "date": "generated",
        "build": build_id,
        "probe_id": probe_id,
        "log": str(log_path.resolve()),
        "log_from_byte": start,
        "log_to_byte": end if end is not None else len(raw),
        "fresh_session_observed": bool(text.strip()),
        "replacement_render_model_guid": after or None,
        "visual_assignment": {"ok": bool(assignments), "before": before or None, "after": after or None},
        "item_registered": bool(registrations),
        "recipe_registered": bool(registrations),
        "placed_entity_reference": placements[-1].split("PLACED_ENTITY|", 1)[-1].strip() if placements else None,
        "panic_observed": panic,
        "probe_uninstalled": probe_uninstalled,
        "stable_profile_restored": stable_profile_restored,
        "live_isolation_ready": stable_profile_restored,
        "state": "experimental",
        "evidence_scope": "assignment_only" if assignment_only else "full_probe",
        "assignment_boundary": (
            "Runtime model-object assignment only; this session did not establish fresh clone registration, catalog rendering, placed-object rendering, or save persistence."
            if assignment_only else None
        ),
        "limitations": [
            "Human-visible placed-object replacement appearance requires a screenshot.",
            "Fresh-launch save persistence requires a second-session check.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--probe-id", required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int)
    parser.add_argument("--build")
    parser.add_argument("--probe-uninstalled", action="store_true")
    parser.add_argument("--stable-profile-restored", action="store_true")
    parser.add_argument("--assignment-only", action="store_true",
                        help="Record a bounded runtime assignment result without requiring clone registration evidence")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.log, args.probe_id, args.start, args.end, args.build,
                   args.probe_uninstalled, args.stable_profile_restored, args.assignment_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Generated visual-substitution evidence: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
