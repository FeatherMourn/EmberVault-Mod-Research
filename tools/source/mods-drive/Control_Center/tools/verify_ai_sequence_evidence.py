"""Fail-closed verifier for isolated ActorSequence clone/attachment evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "control_center.ai_sequence_evidence_verification.v1"
DONOR = "a837f190-d163-4ef5-a48e-3ea7caac7296"
CLONE = "c8f7a8a3-6f6f-4ae9-b15e-30fd2c5c7e11"


def _load(path: Path, errors: list[str], label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        errors.append(f"{label}: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{label}: evidence root must be an object")
        return {}
    return data


def _event_set(data: dict, errors: list[str], label: str) -> set[str]:
    events = data.get("events")
    if not isinstance(events, list) or not all(isinstance(item, str) for item in events):
        errors.append(f"{label}: events must be a string array")
        return set()
    return set(events)


def _require(events: set[str], event: str, errors: list[str], label: str) -> None:
    if event not in events:
        errors.append(f"{label}: missing event {event}")


def verify(graph_path: Path, clone_path: Path, attachment_path: Path,
           restore_paths: list[Path], expected_build: str) -> dict:
    errors: list[str] = []
    graph = _load(graph_path, errors, "graph")
    clone = _load(clone_path, errors, "clone")
    attachment = _load(attachment_path, errors, "attachment")

    expected_markers = {
        "graph": f"enemy_action_sequence_resource_probe_{expected_build}",
        "clone": f"actor_sequence_identity_clone_{expected_build}",
        "attachment": f"actor_sequence_identity_clone_{expected_build}",
    }
    for label, data in (("graph", graph), ("clone", clone), ("attachment", attachment)):
        if data.get("marker") != expected_markers[label]:
            errors.append(f"{label}: build-pinned marker mismatch")
        if not isinstance(data.get("log"), str) or not data["log"].endswith(".eml.log"):
            errors.append(f"{label}: runtime log path is missing")

    graph_events = _event_set(graph, errors, "graph")
    for event in (
        f"MATCH|key=1450|resourceId={DONOR}",
        "EVENT_COUNT|41",
        "MATCH_COUNT|1",
    ):
        _require(graph_events, event, errors, "graph")
    event_types = [event for event in graph_events if event.startswith("EVENT_TYPE|index=")]
    indexes: set[int] = set()
    for event in event_types:
        try:
            indexes.add(int(event.split("|index=", 1)[1].split("|", 1)[0]))
        except ValueError:
            errors.append(f"graph: invalid event index in {event}")
    if indexes != set(range(1, 42)):
        errors.append("graph: expected exactly indexed event types 1 through 41")
    if graph.get("status") != "action_sequence_resource_inventory_verified":
        errors.append("graph: status mismatch")

    clone_events = _event_set(clone, errors, "clone")
    for event in (
        f"DONOR|guid={DONOR}|sequences=1|events=41",
        "DONOR_PRESERVED|true",
        "PARITY|sequences=true|events=true|types=true",
        "ATTACHMENT|behavior=false|attack=false|spawn=false",
        "RESULT|identity_clone_registered",
    ):
        _require(clone_events, event, errors, "clone")
    if clone.get("status") != "actor_sequence_identity_clone_registered":
        errors.append("clone: status mismatch")

    attachment_events = _event_set(attachment, errors, "attachment")
    for event in (
        f"DONOR|guid={DONOR}|sequences=1|events=41",
        "CLONE_ID_WRITE|ok=true|error=nil",
        f"CLONE|guid={CLONE}|resourceId={CLONE}|sequences=1|events=41",
        "DONOR_PRESERVED|true",
        "PARITY|sequences=true|events=true|types=true",
        f"ATTACHMENT|arsenal=cd861d95-a79c-4c11-8b48-8fae34a4156c|attack=1|before={DONOR}|after={CLONE}",
        "ATTACHMENT_RESULT|ok=true|error=nil",
        "RESULT|identity_clone_and_attack_attachment_tested",
    ):
        _require(attachment_events, event, errors, "attachment")
    if attachment.get("status") != "actor_sequence_attack_attachment_tested":
        errors.append("attachment: status mismatch")

    restored = set()
    for index, path in enumerate(restore_paths):
        restore = _load(path, errors, f"restore[{index}]")
        if restore.get("mode") != "restore" or not restore.get("backup_id"):
            errors.append(f"restore[{index}]: restore record is incomplete")
        if isinstance(restore.get("identity"), str):
            restored.add(restore["identity"])
    if expected_markers["clone"] not in restored:
        errors.append("restore evidence does not cover the actor-sequence probe")

    return {
        "schema": SCHEMA,
        "valid": not errors,
        "state": "research-only",
        "promotion_ready": False,
        "verified_gates": {
            "event_graph_inventory_41": not any(error.startswith("graph:") for error in errors),
            "donor_preserving_identity_clone": not any(error.startswith("clone:") for error in errors),
            "isolated_attack_reference_attachment": not any(error.startswith("attachment:") for error in errors),
            "probe_restore": not any(error.startswith("restore") for error in errors),
        },
        "limitations": [
            "no changed AI behavior was observed in game",
            "no new enemy archetype or spawn registration is verified",
            "animation, navigation, persistence, and multiplayer authority are unverified",
        ],
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", type=Path)
    parser.add_argument("clone", type=Path)
    parser.add_argument("attachment", type=Path)
    parser.add_argument("restores", nargs="+", type=Path)
    parser.add_argument("--expected-build", required=True)
    args = parser.parse_args()
    result = verify(args.graph, args.clone, args.attachment, args.restores, args.expected_build)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
