"""Conservative interpretation of generated runtime-probe evidence."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
from datetime import datetime, timezone


def inspect_probe(log_path: Path, marker: str, baseline_mtime: float | None = None,
                  require_fresh: bool = False) -> dict[str, Any]:
    """Read only fresh log evidence for one probe; never infer success from stale logs."""
    path = Path(log_path)
    result: dict[str, Any] = {
        "log": str(path), "marker": marker, "status": "missing", "events": [],
    }
    if require_fresh and baseline_mtime is None:
        result["status"] = "freshness_baseline_required"
        return result
    if not path.is_file():
        return result
    stat = path.stat()
    result["modified"] = stat.st_mtime
    if baseline_mtime is not None and stat.st_mtime <= baseline_mtime:
        result["status"] = "stale_log"
        return result
    custom_prefix = marker.strip() if str(marker).strip().startswith("[") else None
    prefixes = tuple(item for item in (
        custom_prefix,
        f"[CC-MINIMAL-CLONE:{marker}]",
        f"[CC-REGISTRY-CLONE:{marker}]",
        f"[CC-RESOURCE-METADATA:{marker}]",
        "[CC-ENEMY-ARSENAL-ENUM]",
        f"[CC-ENEMY-ARSENAL-READ:{marker}]",
        f"[CC-ENEMY-ARSENAL-GRAPH:{marker}]",
        f"[CC-ENEMY-ARSENAL-DEPS:{marker}]",
        f"[CC-ENEMY-ARSENAL-SEQ:{marker}]",
        f"[CC-ENEMY-BEHAVIOR-ACTION:{marker}]",
        f"[CC-ENEMY-BEHAVIOR-HELPER:{marker}]",
        f"[CC-ENEMY-ARSENAL-SCAN:{marker}]",
        f"[CC-ACTION-SEQUENCE-RESOURCE:{marker}]",
        f"[CC-ACTOR-SEQUENCE-CLONE:{marker}]",
        f"[CC-JOURNAL-SCHEMA:{marker}]",
        f"[CC-KNOWLEDGE-SCHEMA:{marker}]",
        f"[CC-JOURNAL-CLONE:{marker}]",
        f"[CC-JOURNAL-QUEST-CREATE:{marker}]",
    ) if item)
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        candidates = [line]
        try:
            payload = json.loads(line)
            if baseline_mtime is not None and isinstance(payload, dict):
                timestamp = payload.get("timestamp")
                if isinstance(timestamp, str):
                    try:
                        observed = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
                        if observed <= baseline_mtime:
                            continue
                    except ValueError:
                        pass
            message = payload.get("fields", {}).get("message") if isinstance(payload, dict) else None
            if isinstance(message, str):
                candidates.insert(0, message)
        except json.JSONDecodeError:
            pass
        for prefix in prefixes:
            for candidate in candidates:
                if prefix in candidate:
                    result["events"].append(candidate[candidate.index(prefix) + len(prefix):].strip())
                    break
            else:
                continue
            break
    events = result["events"]
    if not events:
        result["status"] = "no_probe_events"
    elif any("REGISTRY|" in event and "->" in event and
             event.split("REGISTRY|", 1)[1].split("->", 1)[0] !=
             event.split("REGISTRY|", 1)[1].split("->", 1)[1].split("|", 1)[0]
             for event in events):
        if any("INDEX_LOOKUP|true" in event for event in events):
            result["status"] = "registry_indexed"
        else:
            result["status"] = "registry_grew_lookup_unverified"
    elif custom_prefix and any(event.startswith("REGISTERED|") for event in events) and any(event.startswith("DISCOVERED_CLONE|") for event in events):
        result["status"] = "furniture_clone_registered"
    elif any("CLONED_ITEM|" in event for event in events):
        result["status"] = "clone_registered"
    elif any(event == "RESULT|identity_clone_registered" for event in events):
        result["status"] = "actor_sequence_identity_clone_registered"
    elif any(event == "RESULT|identity_clone_and_attack_attachment_tested" for event in events):
        result["status"] = "actor_sequence_attack_attachment_tested"
    elif any(event.startswith("RESOURCE_COUNT|") for event in events) and any(event.startswith("QUEST_COUNT|") for event in events):
        result["status"] = "journal_schema_inventory_verified"
    elif any(event == "RESULT|knowledge_schema_inventory_verified" for event in events):
        result["status"] = "knowledge_schema_inventory_verified"
    elif any(event == "RESULT|journal_identity_clone_registered" for event in events):
        result["status"] = "journal_identity_clone_registered"
    elif any(event == "RESULT|journal_live_attachment_runtime_verified" for event in events):
        result["status"] = "journal_live_attachment_runtime_verified"
    elif any(event == "RESULT|journal_registry_clone_insert_verified" for event in events):
        result["status"] = "journal_registry_clone_insert_verified"
    elif any(event == "RESULT|standalone_quest_resource_created" for event in events):
        result["status"] = "standalone_quest_resource_created"
    elif any(event.startswith("DATA|ok=true") for event in events) and any(event.startswith("ARSENAL_COUNT|") for event in events):
        result["status"] = "payload_read_verified"
    elif any(event.startswith("RESOURCE|") for event in events) and any(event.startswith("COUNT|") for event in events):
        result["status"] = "action_sequence_resource_inventory_verified"
    elif any(event.startswith("FIELD|") and "|key=" in event for event in events) and any(event.startswith("FIELD_COUNT|") for event in events):
        result["status"] = "graph_entry_read_verified"
    elif any(event.startswith("VALUE|") for event in events) and any(event.startswith("FIRST|") for event in events):
        result["status"] = "dependency_identity_read_verified"
    elif any(event.startswith("ATTACK|ok=true") for event in events) and any(event.startswith("BEHAVIOR|ok=true") for event in events):
        result["status"] = "sequence_graph_boundary_verified"
    elif any(event.startswith("FIRST|behavior.actions|ok=true|type=userdata") for event in events):
        result["status"] = "mapped_variant_boundary_observed"
    elif any(event.startswith("SUMMARY|") and "|populated=" in event for event in events):
        result["status"] = "attack_donor_scan_verified"
    elif any(event.startswith("RESULT|ok=true") for event in events) and any(event == "COUNT|0" for event in events):
        result["status"] = "action_sequence_resource_empty"
    elif any(event.startswith("RESULT|ok=true") for event in events) and "behavior_helper_probe" in marker:
        result["status"] = "helper_probe_inconclusive"
    elif any(event.startswith("API|") for event in events):
        if any(event.startswith("COUNT|") for event in events) and any(event.startswith("RESULT|") for event in events):
            result["status"] = "metadata_enumeration_verified"
        elif any(event.startswith("IDENTITY|") for event in events):
            result["status"] = "metadata_lookup_verified"
        elif any(event.startswith("AFTER_CALL|ok=true") for event in events):
            result["status"] = "metadata_call_completed"
        else:
            result["status"] = "metadata_api_exposed"
    elif any(event.startswith("RESULT|ok=true") for event in events) and any(event.startswith("COUNT|") for event in events):
        result["status"] = "metadata_enumeration_verified"
    elif any("REGISTER|false|" in event for event in events):
        result["status"] = "registration_failed"
    elif any("DONOR|false" in event for event in events):
        result["status"] = "donor_not_found"
    else:
        result["status"] = "inconclusive"
    return result
