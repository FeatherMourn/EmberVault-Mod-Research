"""Fail-closed verifier for the isolated quest prototype evidence chain."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "control_center.quest_prototype_evidence_verification.v1"


def _load(path: Path, errors: list[str], label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        errors.append(f"{label}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label}: evidence root must be an object")
        return {}
    return value


def _events(data: dict, errors: list[str], label: str) -> set[str]:
    events = data.get("events")
    if not isinstance(events, list) or not all(isinstance(item, str) for item in events):
        errors.append(f"{label}: events must be a string array")
        return set()
    return set(events)


def _require(events: set[str], expected: str, errors: list[str], label: str) -> None:
    if expected not in events:
        errors.append(f"{label}: missing event {expected}")


def verify(standalone_path: Path, registry_path: Path, live_path: Path,
           restore_paths: list[Path], expected_build: str) -> dict:
    errors: list[str] = []
    standalone = _load(standalone_path, errors, "standalone")
    registry = _load(registry_path, errors, "registry")
    live = _load(live_path, errors, "live")

    expected_markers = {
        "standalone": f"journal_quest_resource_create_probe_{expected_build}",
        "registry": f"journal_registry_identity_clone_{expected_build}",
        "live": f"journal_registry_identity_clone_{expected_build}",
    }
    for label, data in (("standalone", standalone), ("registry", registry), ("live", live)):
        if data.get("marker") != expected_markers[label]:
            errors.append(f"{label}: build-pinned marker mismatch")
        if not isinstance(data.get("log"), str) or not data["log"].endswith(".eml.log"):
            errors.append(f"{label}: runtime log path is missing")

    standalone_events = _events(standalone, errors, "standalone")
    for event in (
        "EDIT|ok=true|error=nil|new_entry_id=3987654701",
        "READBACK|guid=e7d6d3a5-9708-47c7-8c7d-78b2a3c88d41|data_type=userdata|entryId=3987654701",
        "DONOR_IDENTITY_PRESERVED|true",
        "ATTACHMENT|registry=false|save=false|knowledge=false",
        "RESULT|standalone_quest_resource_created",
    ):
        _require(standalone_events, event, errors, "standalone")
    if standalone.get("status") != "standalone_quest_resource_created":
        errors.append("standalone: status mismatch")

    registry_events = _events(registry, errors, "registry")
    for event in (
        "DONOR_PRESERVED|true",
        "PARITY|quests=true",
        "INSERT|ok=true|error=nil|clone_quests=169|donor_quests=168",
        "ATTACHMENT|live_registry=false|save=false|knowledge=false",
        "REGISTRY_COUNT|2",
        "RESULT|journal_registry_clone_insert_verified",
    ):
        _require(registry_events, event, errors, "registry")
    if registry.get("status") != "journal_registry_clone_insert_verified":
        errors.append("registry: status mismatch")

    live_events = _events(live, errors, "live")
    for event in (
        "DONOR_PRESERVED|true",
        "INSERT|ok=true|error=nil|clone_quests=169|donor_quests=168",
        "LIVE_ATTACH|ok=true|error=nil|donor_quests=169",
        "RESULT|journal_live_attachment_runtime_verified",
    ):
        _require(live_events, event, errors, "live")
    if live.get("status") != "journal_live_attachment_runtime_verified":
        errors.append("live: status mismatch")

    restored_identities: set[str] = set()
    for index, path in enumerate(restore_paths):
        restore = _load(path, errors, f"restore[{index}]")
        if restore.get("mode") != "restore" or not restore.get("backup_id"):
            errors.append(f"restore[{index}]: restore record is incomplete")
        identity = restore.get("identity")
        if isinstance(identity, str):
            restored_identities.add(identity)
    required_identities = set(expected_markers.values())
    if not required_identities.issubset(restored_identities):
        errors.append("restore evidence does not cover both quest probe identities")

    limitations = [
        "visible journal presentation is not verified",
        "save persistence is not verified",
        "quest completion and rewards are not verified",
        "multiplayer authority is not verified",
    ]
    return {
        "schema": SCHEMA,
        "valid": not errors,
        "state": "research-only",
        "promotion_ready": False,
        "verified_gates": {
            "standalone_creation_and_identity_edit": not any(e.startswith("standalone:") for e in errors),
            "donor_preserving_typed_registry_insertion": not any(e.startswith("registry:") for e in errors),
            "isolated_runtime_attachment": not any(e.startswith("live:") for e in errors),
            "probe_restore_records": not any(e.startswith("restore") for e in errors),
        },
        "limitations": limitations,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("standalone", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument("live", type=Path)
    parser.add_argument("restores", nargs="+", type=Path)
    parser.add_argument("--expected-build", required=True)
    args = parser.parse_args()
    result = verify(args.standalone, args.registry, args.live, args.restores, args.expected_build)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
