"""Offline analysis of Architect semantic bridge captures."""
from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

INPUT_NAMES = (
    "semantic_actions.jsonl", "semantic_action_status.json", "native_status.json",
    "native_runtime.log", "building_capture.json", "upstream_trace.json",
    "inventory_move_caller_scan.json", "inventory_move_pointer_site_scan.json",
    "inventory_transfer_consumer_scan.json", "create_building_item_static_map.json",
    "client_player_input_static_map.json",
    "structure_recorder_status.json", "structure_editor_status.json",
    "single_placement_carrier_status.json",
)
PROJECT_STATES = {"PROVEN", "INFERRED", "EXPERIMENTAL", "UNSOLVED", "DISPROVEN"}
CAPTURE_STATES = {"SUPPORTED_BY_CAPTURE", "CONTRADICTED_BY_CAPTURE", "INSUFFICIENT_EVIDENCE"}
SUPPORTED_EXE_SHA256 = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"


def as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 16 if value.lower().startswith("0x") else 10)
        except ValueError:
            return None
    return None


def nested(obj: Any, *path: str, default=None):
    for key in path:
        if not isinstance(obj, dict) or key not in obj:
            return default
        obj = obj[key]
    return obj


def read_json(path: Path, warnings: list[dict]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        warnings.append({"code": "MALFORMED_JSON", "file": path.name, "detail": str(exc)})
        return None


def read_jsonl(path: Path, warnings: list[dict]) -> list[dict]:
    rows = []
    try:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError as exc:
        warnings.append({"code": "UNREADABLE_JSONL", "file": path.name, "detail": str(exc)})
        return rows
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
            else:
                warnings.append({"code": "NON_OBJECT_JSONL", "file": path.name, "line": number})
        except json.JSONDecodeError as exc:
            warnings.append({"code": "MALFORMED_JSONL_LINE", "file": path.name,
                             "line": number, "detail": str(exc)})
    return rows


def discover_id_index(root: Path, warnings: list[dict]) -> tuple[dict[int, str], list[str]]:
    """Load only explicit local id/name JSON maps; never infer names from prose."""
    names: dict[int, str] = {}
    sources = []
    patterns = ("*item*index*.json", "*material*index*.json", "*kfc*index*.json")
    candidates = sorted({p for pattern in patterns for p in root.rglob(pattern)
                         if "bridge" not in {part.lower() for part in p.parts}})
    for path in candidates[:32]:
        value = read_json(path, warnings)
        if not isinstance(value, (dict, list)):
            continue
        rows = value.items() if isinstance(value, dict) else enumerate(value)
        added = 0
        for key, row in rows:
            if isinstance(row, str):
                ident, name = as_int(key), row
            elif isinstance(row, dict):
                ident = as_int(row.get("itemId", row.get("materialId", row.get("id"))))
                name = row.get("name") or row.get("displayName")
            else:
                continue
            if ident is not None and isinstance(name, str) and name:
                names.setdefault(ident, name); added += 1
        if added:
            sources.append(str(path))
    sqlite_path=root/"data"/"architect_game_data_1076226.sqlite"
    if sqlite_path.is_file():
        try:
            db=sqlite3.connect(sqlite_path)
            for ident,name in db.execute("SELECT item_id,debug_name FROM items WHERE debug_name IS NOT NULL"):
                names.setdefault(int(ident),name)
            db.close();sources.append(str(sqlite_path.resolve()))
        except sqlite3.Error as exc:
            warnings.append({"code":"DATA_INDEX_UNREADABLE","file":str(sqlite_path),"detail":str(exc)})
    return names, sources


def discover_blueprint_index(root: Path, warnings: list[dict]) -> dict[int, dict[str, Any]]:
    """Load explicit ArchitectDataIndex catalog rows for offline enrichment."""
    path = root / "bridge" / "build_catalog.json"
    value = read_json(path, warnings) if path.is_file() else None
    if not isinstance(value, dict):
        return {}
    result: dict[int, dict[str, Any]] = {}
    for row in value.get("items", []):
        if not isinstance(row, dict):
            continue
        ident = as_int(row.get("itemId"))
        if ident is not None:
            result.setdefault(ident, row)
    return result


def check(name: str, applicable: bool, passed: bool | None, evidence: dict) -> dict:
    state = "INSUFFICIENT_EVIDENCE" if not applicable or passed is None else (
        "SUPPORTED_BY_CAPTURE" if passed else "CONTRADICTED_BY_CAPTURE")
    return {"check": name, "captureAssessment": state, "evidence": evidence}


def stack(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def inventory_operation(event: dict) -> dict:
    pre, post = stack(event.get("pre")), stack(event.get("post"))
    source = stack(event.get("sourceCandidate"))
    destination = stack(event.get("destinationSlot"))
    amount = as_int(event.get("candidateAmountRaw", event.get("transferAmount")))
    path = event.get("postPath")
    pre_count, post_count = as_int(pre.get("count")), as_int(post.get("count"))
    validations = []
    is_merge = path in {"existing_item_merge", "merge"}
    is_empty = path in {"empty_destination_initialization", "empty_initialization"}
    validations.append(check("merge_count_arithmetic", is_merge,
                             None if None in (pre_count, amount, post_count) else post_count == pre_count + amount,
                             {"destinationPreCount": pre_count, "transferAmount": amount,
                              "destinationPostCount": post_count}))
    validations.append(check("empty_initialization_arithmetic", is_empty,
                             None if None in (pre_count, amount, post_count) else
                             pre_count == 0 and post_count == amount,
                             {"destinationPreCount": pre_count, "transferAmount": amount,
                              "destinationPostCount": post_count}))
    ptr = as_int(event.get("candidatePointer"))
    base = as_int(destination.get("inventoryBase", event.get("candidateInventoryBase")))
    slot_index = as_int(destination.get("slotIndex", event.get("candidateSlotIndex")))
    validations.append(check("destination_stack_address_equation", all(x is not None for x in (ptr, base, slot_index)),
                             None if None in (ptr, base, slot_index) else ptr == base + slot_index * 0x0C,
                             {"stackAddress": event.get("candidatePointer"), "inventoryBase":
                              destination.get("inventoryBase", event.get("candidateInventoryBase")),
                              "slotIndex": slot_index, "stride": "0x0C"}))
    source_ptr = as_int(source.get("pointer", event.get("sourcePointer")))
    source_base = as_int(source.get("inventoryBase", event.get("sourceInventoryBase")))
    source_slot = as_int(source.get("slotIndex", event.get("sourceSlotIndex")))
    validations.append(check("source_stack_address_equation",
                             all(x is not None for x in (source_ptr, source_base, source_slot)),
                             None if None in (source_ptr, source_base, source_slot) else
                             source_ptr == source_base + source_slot * 0x0C,
                             {"stackAddress": source.get("pointer", event.get("sourcePointer")),
                              "inventoryBase": source.get("inventoryBase", event.get("sourceInventoryBase")),
                              "slotIndex": source_slot, "stride": "0x0C"}))
    return {
        "eventSequence": event.get("eventSequence"), "tickMs": event.get("tickMs"), "postPath": path,
        "candidateInventoryOperationId": event.get("candidateInventoryOperationId"),
        "sourcePre": None,
        "sourceIntermediate": source.get("pre"),
        "sourceAtDestinationCompletion": source.get("postAtDestinationCompletion", source.get("post")),
        "destinationPre": pre, "transferAmount": amount, "destinationPost": post,
        "itemId": post.get("itemId", pre.get("itemId", event.get("candidateR14ItemId"))),
        "pide": post.get("pide", pre.get("pide")), "callerRva": event.get("returnRva"),
        "threadId": event.get("threadId"), "sourcePointer": source.get("pointer", event.get("sourcePointer")),
        "destinationPointer": event.get("candidatePointer"), "sourceSlot": {
            "inventoryBase": source.get("inventoryBase"), "slotIndex": source.get("slotIndex"),
            "inventorySlotId": source.get("inventorySlotId")},
        "destinationSlot": {"inventoryBase": destination.get("inventoryBase"),
                            "slotIndex": destination.get("slotIndex"),
                            "inventorySlotId": destination.get("inventorySlotId")},
        "validations": validations,
    }


def building_groups(events: list[dict], id_names: dict[int, str], blueprint_index: dict[int, dict[str, Any]] | None = None) -> list[dict]:
    blueprint_index = blueprint_index or {}
    groups: dict[Any, list[dict]] = defaultdict(list)
    for index, event in enumerate(events):
        logical = nested(event, "correlation", "candidateLogicalPlacementId", default=f"unpaired-{index}")
        groups[logical].append(event)
    result = []
    for logical, rows in groups.items():
        ticks = [as_int(row.get("tickMs")) for row in rows]
        ticks = [x for x in ticks if x is not None]
        payloads = [row.get("payload") for row in rows]
        raw_equal = len(rows) == 2 and payloads[0] == payloads[1]
        semantic_payloads = [{k: v for k, v in payload.items() if k != "context"}
                             if isinstance(payload, dict) else payload for payload in payloads]
        equal = len(rows) == 2 and semantic_payloads[0] == semantic_payloads[1]
        material = nested(rows[0], "payload", "material")
        item = nested(rows[0], "payload", "trackingItemId")
        item_id = as_int(item)
        catalog = blueprint_index.get(item_id, {}) if item_id is not None else {}
        result.append({"candidateLogicalPlacementId": logical, "recordCount": len(rows),
                       "pairPayloadEqual": equal, "rawPayloadEqualIncludingContext": raw_equal,
                       "pairComparisonPolicy": "all payload fields except context; context is reported separately",
                       "pairTimingMs": max(ticks) - min(ticks) if len(ticks) > 1 else None,
                       "threads": [r.get("threadId") for r in rows],
                       "contexts": [nested(r, "payload", "context") for r in rows],
                       "callers": [nested(r, "addressEvidence", "callerRva") for r in rows],
                       "returns": [nested(r, "addressEvidence", "returnAddress") for r in rows],
                       "sideClassification": None,
                       "resolvedIds": {"material": id_names.get(as_int(material)),
                                       "trackingItemId": id_names.get(item_id)},
                       "blueprintIdentity": {"itemId": item_id,
                                              "debugName": catalog.get("debugName"),
                                              "blueprintRegistryIdentity": catalog.get("blueprints", []),
                                              "dimensions": [b.get("dimensions") for b in catalog.get("blueprints", []) if isinstance(b, dict)],
                                              "classification": catalog.get("classification"),
                                              "snapFamily": None,
                                              "snapFamilyStatus": "UNRESOLVED"},
                       "rawRecords": rows})
    return result


def carrier_attempt_summary(events: list[dict]) -> dict:
    """Summarize experimental carrier records without implying world authority."""
    attempts = [e for e in events if e.get("observer") == "building_carrier_attempt"]
    building = [e for e in events if e.get("observer") == "building_place"]
    rows = []
    for event in attempts:
        original = as_int(event.get("originalTrackingItemId"))
        desired = as_int(event.get("desiredTrackingItemId"))
        observed = as_int(event.get("observedTrackingItemId"))
        build_id = nested(event, "build", "buildId")
        negative_evidence = (
            build_id == "architect-v031-single-placement-carrier-20260915-a" or
            (original == 948722226 and desired == 950598916)
        )
        restored = event.get("restorationSucceeded") is True
        argument_supported = desired is not None and observed == desired and original is not None and restored
        tick = as_int(event.get("tickMs"))
        candidates = []
        if tick is not None:
            for raw in building:
                raw_tick = as_int(raw.get("tickMs"))
                if raw_tick is not None and abs(raw_tick - tick) <= 1000:
                    candidates.append((abs(raw_tick - tick), raw))
        correlated = min(candidates, key=lambda pair: pair[0])[1] if candidates else None
        rows.append({
            "operationId": event.get("operationId"),
            "planPlacementId": event.get("planPlacementId"),
            "stage": event.get("stage"),
            "eventOrdinal": event.get("eventOrdinal"),
            "threadId": event.get("threadId"),
            "originalTrackingItemId": original,
            "desiredTrackingItemId": desired,
            "observedTrackingItemId": observed,
            "restorationSucceeded": restored,
            "correlatedBuildingEventSequence": correlated.get("eventSequence") if correlated else None,
            "correlatedLogicalPlacementId": nested(correlated, "correlation", "candidateLogicalPlacementId") if correlated else None,
            "correlationAssessment": "NEAREST_BUILDING_EVENT_WITHIN_1S" if correlated else "INSUFFICIENT_EVIDENCE",
            "argumentSubstitutionAssessment": (
                "SUPPORTED_BY_CAPTURE" if argument_supported else "CONTRADICTED_BY_CAPTURE"
            ),
            # The native rows establish only the local argument write.  The
            # negative world-geometry conclusion is a separately documented,
            # user-confirmed v0.31 result and is never inferred from these
            # rows alone.
            "localArgumentMutation": "SUPPORTED_BY_CAPTURE" if argument_supported else "NOT_SUPPORTED",
            "logicalPairMutated": "SUPPORTED_BY_CAPTURE" if argument_supported else "NOT_SUPPORTED",
            "worldGeometryMatchesDesiredItem": "CONTRADICTED_BY_USER_CONFIRMED_RUNTIME_RESULT" if negative_evidence else "INSUFFICIENT_EVIDENCE",
            "trackingItemIdHelperArgumentGeometryAuthority": "DISPROVEN_BUILD_1076226" if negative_evidence else "UNSOLVED",
            "worldAuthorityAssessment": "DISPROVEN_BUILD_1076226" if negative_evidence else "INSUFFICIENT_EVIDENCE",
            "negativeResultEvidence": "docs/research/SinglePlacementCarrier-v1.md; user-confirmed v0.31 live capture" if negative_evidence else None,
            "result": event.get("result"),
            "rawEvent": event,
        })
    return {
        "attemptCount": len(rows),
        "attempts": rows,
        "worldAuthority": "DISPROVEN_BUILD_1076226" if any(r["worldAuthorityAssessment"] == "DISPROVEN_BUILD_1076226" for r in rows) else "INSUFFICIENT_EVIDENCE",
        "localArgumentMutation": "SUPPORTED_BY_CAPTURE" if rows and all(r["localArgumentMutation"] == "SUPPORTED_BY_CAPTURE" for r in rows) else ("NOT_SUPPORTED" if rows else "NO_ATTEMPTS"),
        "logicalPairMutated": "SUPPORTED_BY_CAPTURE" if len(rows) >= 2 else ("INSUFFICIENT_EVIDENCE" if rows else "NO_ATTEMPTS"),
        "worldGeometryMatchesDesiredItem": "CONTRADICTED_BY_USER_CONFIRMED_RUNTIME_RESULT" if any(r["worldGeometryMatchesDesiredItem"] == "CONTRADICTED_BY_USER_CONFIRMED_RUNTIME_RESULT" for r in rows) else "INSUFFICIENT_EVIDENCE",
        "trackingItemIdHelperArgumentGeometryAuthority": "DISPROVEN_BUILD_1076226" if any(r["trackingItemIdHelperArgumentGeometryAuthority"] == "DISPROVEN_BUILD_1076226" for r in rows) else "INSUFFICIENT_EVIDENCE",
        "negativeResultEvidence": "docs/research/SinglePlacementCarrier-v1.md; user-confirmed v0.31 live capture" if any(r.get("negativeResultEvidence") for r in rows) else None,
        "policy": "Argument writes are not geometry authority; the v0.31 world result is explicitly user-confirmed and documented, not inferred from native rows.",
    }


def recorded_structure_summary(project_root: Path, warnings: list[dict]) -> dict:
    """Summarize saved capture-only structures without implying replay support."""
    directory = project_root / "blueprints" / "recorded"
    rows = []
    if not directory.is_dir():
        return {"files": [], "validCount": 0, "invalidCount": 0, "replayCapability": "none"}
    for path in sorted(directory.glob("*.architect.json")):
        try:
            from tools.StructureRecorder.recorder import load_blueprint
            session = load_blueprint(path)
            stats = session.statistics()
            coordinate = {"encoding": "signed_q32_32", "scale": 4294967296,
                          "rawPositionsLossless": all(isinstance(p.get("raw", {}).get("position"), list) and all(isinstance(v, int) and not isinstance(v, bool) for v in p["raw"]["position"]) for p in session.placements),
                          "migration": "native_v0.29_float_positions_accepted_only_when_exact_integral"}
            rows.append({"file": path.name, "name": session.name, "recordingId": session.recording_id, "placementCount": len(session.placements), "statistics": stats, "coordinateSystem": coordinate, "recordingWindow": {"sourceSessionId": session.source_session_id, "startRawEventSequence": session.start_raw_event_sequence, "endRawEventSequence": session.end_raw_event_sequence}, "provenanceCounters": {k: stats.get(k) for k in ("semanticStreamEventsObserved", "buildingRawEventsInRecordingWindow", "pairedBuildingRawEvents", "logicalPlacementsRecorded", "ambiguousRawEvents", "ignoredNonBuildingEvents")}, "counterEvidence": session.counter_evidence, "snapCoverage": {"status": stats.get("snapResolutionStatus"), "families": stats.get("snapFamilyCounts")}, "state": session.state, "validation": "valid"})
        except Exception as exc:
            warnings.append({"code": "MALFORMED_RECORDED_STRUCTURE", "file": path.name, "detail": str(exc)})
            rows.append({"file": path.name, "validation": "invalid"})
    return {"files": rows, "validCount": sum(r.get("validation") == "valid" for r in rows), "invalidCount": sum(r.get("validation") == "invalid" for r in rows), "replayCapability": "none_capture_only"}


def placement_plan_summary(project_root: Path, warnings: list[dict]) -> dict:
    """Inspect offline placement plans without implying execution support."""
    directory = project_root / "blueprints" / "plans"
    rows = []
    if not directory.is_dir():
        return {"files": [], "validCount": 0, "invalidCount": 0, "replayAvailable": False, "worldMutationAvailable": False}
    for path in sorted(directory.glob("*.architect-plan.json")):
        try:
            try:
                from tools.StructureEditor.plans import load_plan
            except ImportError:
                from StructureEditor.plans import load_plan
            plan = load_plan(path); value = plan.to_dict()
            rows.append({"file": path.name, "name": plan.name, "placementPlanId": plan.placementPlanId,
                         "sourceStructure": plan.sourceStructure, "statistics": plan.statistics(),
                         "validation": value["validation"], "compatibility": value["compatibility"],
                         "replayAvailable": False, "worldMutationAvailable": False})
        except Exception as exc:
            warnings.append({"code": "MALFORMED_PLACEMENT_PLAN", "file": path.name, "detail": str(exc)})
            rows.append({"file": path.name, "validation": "invalid"})
    return {"files": rows, "validCount": sum(isinstance(r.get("validation"), dict) and r["validation"].get("valid") for r in rows), "invalidCount": sum(r.get("validation") == "invalid" for r in rows), "replayAvailable": False, "worldMutationAvailable": False}


def create_building_item_action(event: dict, id_names: dict[int, str]) -> dict:
    """Normalize a future/native create-item observation without promoting it.

    The native observer is intentionally disabled until its consumer boundary is
    proven.  This parser accepts both the planned ``action`` envelope and the
    flat field names so a later capture can be analyzed without changing the
    schema again.
    """
    action = event.get("action") if isinstance(event.get("action"), dict) else {}
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    source = {**payload, **action, **event}
    version = as_int(source.get("versionRaw", source.get("versionData")))
    selected_index = as_int(source.get("selectedIndexRaw", source.get("selectedIndex")))
    item_id = as_int(source.get("itemIdRaw", source.get("itemId")))
    return {
        "eventSequence": event.get("eventSequence", event.get("rawEventSequence")),
        "tickMs": as_int(event.get("tickMs")),
        "threadId": event.get("threadId"),
        "consumerRva": event.get("consumerRva"),
        "actionPointer": event.get("actionPointer"),
        "versionRaw": version,
        "selectedIndexRaw": selected_index,
        "itemIdRaw": item_id,
        "resolvedItemInfo": id_names.get(item_id) if item_id is not None else None,
        "candidateConsumedVersion": event.get("candidateConsumedVersion"),
        "lifecycle": event.get("lifecycle", "unknown"),
        "rawEvent": event,
    }


def correlate_create_actions(actions: list[dict], building_events: list[dict]) -> list[dict]:
    """Pair action observations with nearby placement records conservatively."""
    result = []
    for action in actions:
        action_tick = action.get("tickMs")
        action_item = action.get("itemIdRaw")
        candidates = []
        for event in building_events:
            tick = as_int(event.get("tickMs"))
            item = as_int(nested(event, "payload", "trackingItemId"))
            if action_tick is None or tick is None:
                continue
            delta = abs(tick - action_tick)
            if delta <= 5000:
                candidates.append((delta, event, item))
        nearest = min(candidates, key=lambda row: row[0]) if candidates else None
        if nearest is None:
            result.append({"actionEventSequence": action.get("eventSequence"),
                           "placementEventSequence": None,
                           "timingDeltaMs": None,
                           "itemIdMatchesTrackingItemId": None,
                           "threadRelationship": "unavailable",
                           "confidence": "INSUFFICIENT_EVIDENCE"})
            continue
        delta, event, placement_item = nearest
        result.append({"actionEventSequence": action.get("eventSequence"),
                       "placementEventSequence": event.get("rawEventSequence", event.get("eventSequence")),
                       "timingDeltaMs": delta,
                       "itemIdMatchesTrackingItemId": (action_item is not None and placement_item is not None and action_item == placement_item),
                       "threadRelationship": "same_thread" if action.get("threadId") == event.get("threadId") else "different_or_unknown_thread",
                       "confidence": "INSUFFICIENT_EVIDENCE",
                       "reason": "nearest committed placement is reported; lifecycle/causal ownership is not inferred"})
    return result


def client_player_input_snapshot(event: dict) -> dict:
    """Normalize an optional future parent-input observation.

    v0.22 intentionally installs no parent observer.  Keeping this parser
    schema-ready lets a later, independently justified observer be analyzed
    without treating a single action-shaped pointer as proof of ownership.
    """
    source = {}
    for key in ("snapshot", "clientPlayerInput", "payload"):
        value = event.get(key)
        if isinstance(value, dict):
            source.update(value)
    source.update(event)
    return {
        "eventSequence": event.get("eventSequence"),
        "tickMs": as_int(event.get("tickMs")),
        "threadId": event.get("threadId"),
        "candidateBase": event.get("candidateBase", source.get("base")),
        "inventoryTransferActionAddress": source.get("inventoryTransferActionAddress"),
        "createBuildingItemActionAddress": source.get("createBuildingItemActionAddress"),
        "buildingStockCycleActionAddress": source.get("buildingStockCycleActionAddress"),
        "inventoryTransferVersion": as_int(source.get("inventoryTransferVersion")),
        "createBuildingItemVersion": as_int(source.get("createBuildingItemVersion")),
        "createBuildingItemSelectedIndex": as_int(source.get("createBuildingItemSelectedIndex")),
        "createBuildingItemId": as_int(source.get("createBuildingItemId")),
        "buildingStockCycleVersion": as_int(source.get("buildingStockCycleVersion")),
        "validation": source.get("validation") if isinstance(source.get("validation"), dict) else {},
        "rawEvent": event,
    }


def analyze(input_dir: Path, project_root: Path | None = None) -> dict:
    input_dir = input_dir.resolve()
    project_root = (project_root or input_dir.parent).resolve()
    warnings: list[dict] = []
    present = [name for name in INPUT_NAMES if (input_dir / name).is_file()]
    events = read_jsonl(input_dir / "semantic_actions.jsonl", warnings) if "semantic_actions.jsonl" in present else []
    documents = {name: read_json(input_dir / name, warnings) for name in present if name.endswith(".json")}
    log = ""
    if "native_runtime.log" in present:
        log = (input_dir / "native_runtime.log").read_text(encoding="utf-8-sig", errors="replace")
    sessions: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        sessions[str(event.get("sessionId") or "MISSING_SESSION_ID")].append(event)
    status_session = nested(documents.get("semantic_action_status.json"), "sessionId")
    artifact_sessions = {name: value.get("sessionId") for name, value in documents.items()
                         if isinstance(value, dict) and value.get("sessionId")}
    all_sessions = set(sessions) | set(artifact_sessions.values())
    current = status_session or (max(sessions, key=lambda key: max(
        [as_int(e.get("tickMs")) or -1 for e in sessions[key]], default=-1)) if sessions else None)
    if len(all_sessions) > 1:
        warnings.append({"code": "MIXED_SESSIONS", "sessions": sorted(all_sessions)})
    stale = sorted(name for name, session in artifact_sessions.items() if current and session != current)
    if stale:
        warnings.append({"code": "STALE_SESSION_ARTIFACTS", "currentSessionId": current, "files": stale})
    id_names, id_sources = discover_id_index(project_root, warnings)
    blueprint_index = discover_blueprint_index(project_root, warnings)
    session_rows = []
    for session_id in sorted(all_sessions):
        rows = sessions.get(session_id, [])
        builds = {(nested(e, "build", "version"), nested(e, "build", "buildId")) for e in rows if e.get("build")}
        building = [e for e in rows if e.get("observer") == "building_place"]
        inventory = [inventory_operation(e) for e in rows
                     if e.get("observer") == "inventory_move_pointer_probe" and
                     e.get("recordType") != "pre_operation_snapshot"]
        actions=[e for e in rows if e.get("observer")=="inventory_transfer_action_consumer"]
        create_actions = [create_building_item_action(e, id_names) for e in rows
                          if e.get("observer") == "create_building_item_action"]
        carrier = carrier_attempt_summary(rows)
        parent_snapshots = [client_player_input_snapshot(e) for e in rows
                            if e.get("observer") in {"client_player_input_snapshot", "client_player_input_parent"}]
        correlations=[]
        for action_event in actions:
            action=action_event.get("action") or {};op_id=action_event.get("candidateInventoryOperationId")
            candidates=[op for op in inventory if op_id is not None and op.get("candidateInventoryOperationId")==op_id]
            action_type=as_int(action.get("typeRaw"));action_amount=as_int(action.get("amount"))
            if not candidates:
                candidates=[op for op in inventory if op.get("threadId")==action_event.get("threadId") and
                            ((action_type==3 and op.get("transferAmount")==action_amount) or
                             (action_type!=3 and action_amount==0)) and
                            as_int(op.get("tickMs")) is not None and
                            abs(as_int(op.get("tickMs"))-as_int(action_event.get("tickMs"))) <= 1000]
                if candidates:
                    nearest=min(abs(as_int(op.get("tickMs"))-as_int(action_event.get("tickMs"))) for op in candidates)
                    candidates=[op for op in candidates if abs(as_int(op.get("tickMs"))-as_int(action_event.get("tickMs")))==nearest]
            operation=candidates[0] if len(candidates)==1 else None
            source_slot=as_int(nested(action,"sourceSlotId","slotIndexRaw"));target_slot=as_int(nested(action,"targetSlotId","slotIndexRaw"))
            if action_type==3:
                amount_check=check("split_action_amount_equals_effective",operation is not None,operation is not None and action_amount==operation.get("transferAmount"),{"actionAmountRaw":action_amount,"effectiveTransferAmount":operation.get("transferAmount") if operation else None})
            else:
                amount_check=check("operation_type_dependent_amount",operation is not None,operation is not None and action_amount==0,{"actionAmountRaw":action_amount,"effectiveTransferAmount":operation.get("transferAmount") if operation else None,"interpretation":"zero raw action amount; effective full-stack count is observed downstream"})
            correlations.append({"candidateInventoryOperationId":op_id,"actionEventSequence":action_event.get("eventSequence"),"action":action,"actionAmountRaw":action_amount,"effectiveTransferAmount":operation.get("transferAmount") if operation else None,"itemName":id_names.get(operation.get("itemId")) if operation else None,"downstreamOperation":operation,"checks":[amount_check,check("source_slot_matches",operation is not None and source_slot is not None and operation["sourceSlot"].get("slotIndex") is not None,operation is not None and source_slot==as_int(operation["sourceSlot"].get("slotIndex")),{"action":source_slot,"downstream":operation["sourceSlot"].get("slotIndex") if operation else None}),check("target_slot_matches",operation is not None and target_slot is not None and operation["destinationSlot"].get("slotIndex") is not None,operation is not None and target_slot==as_int(operation["destinationSlot"].get("slotIndex")),{"action":target_slot,"downstream":operation["destinationSlot"].get("slotIndex") if operation else None})],"candidateConsumedVersion":action_event.get("candidateConsumedVersion")})
        session_rows.append({"sessionId": session_id, "isCurrent": session_id == current,
                             "eventCount": len(rows), "observerCounts": dict(sorted(Counter(
                                 e.get("observer", "missing") for e in rows).items())),
                             "buildsInEvents": [{"version": a, "buildId": b} for a, b in sorted(builds)],
                             "previewOrCancelOnlyCandidate": len(building) == 0,
                             "buildingOperations": building_groups(building, id_names, blueprint_index),
                             "singlePlacementCarrier": carrier,
                             "createBuildingItemActions": create_actions,
                             "createActionPlacementCorrelations": correlate_create_actions(create_actions, building),
                             "clientPlayerInputSnapshots": parent_snapshots,
                             "inventoryOperations": inventory,"inventoryTransferActions":actions,
                             "actionOperationCorrelations":correlations,
                             "typeDistribution":dict(sorted(Counter(str(nested(e,"action","typeRaw")) for e in actions).items()))})
    semantic_status = documents.get("semantic_action_status.json") or {}
    native_status = documents.get("native_status.json") or {}
    create_static = documents.get("create_building_item_static_map.json") or {}
    client_input_static = documents.get("client_player_input_static_map.json") or {}
    executable_hashes = set()
    for value in documents.values():
        if not isinstance(value, dict):
            continue
        candidates = [value.get("executableSha256"), nested(value, "executable", "sha256"),
                      nested(value, "build", "executableSha256"), nested(value, "build", "sha256")]
        executable_hashes.update(str(x).upper() for x in candidates if isinstance(x, str) and len(x) == 64)
    hash_compatibility = (None if not executable_hashes else
                          all(x == SUPPORTED_EXE_SHA256 for x in executable_hashes))
    if hash_compatibility is False:
        warnings.append({"code": "BUILD_HASH_MISMATCH", "observed": sorted(executable_hashes),
                         "supported": SUPPORTED_EXE_SHA256})
    identities = {(value.get("version"), value.get("buildId")) for value in documents.values()
                  if isinstance(value, dict) and value.get("version") and value.get("buildId")}
    build = semantic_status.get("build", {})
    if build.get("version") and build.get("buildId"):
        identities.add((build["version"], build["buildId"]))
    if len(identities) > 1:
        warnings.append({"code": "MIXED_BUILD_IDENTITIES", "identities":
                         [{"version": x, "buildId": y} for x, y in sorted(identities)]})
    hook_states = {}
    for name, observer in sorted((semantic_status.get("observers") or {}).items()):
        if isinstance(observer, dict):
            hook_states[name] = observer.get("runtime", {})
    validations = [v for s in session_rows for op in s["inventoryOperations"] for v in op["validations"]]+[v for s in session_rows for c in s["actionOperationCorrelations"] for v in c["checks"]]
    caller_counts = Counter(op.get("callerRva") for s in session_rows for op in s["inventoryOperations"]
                            if op.get("callerRva"))
    return {
        "schemaVersion": 1, "tool": "Architect Semantic Capture Analyzer",
        "analysisMode": "OFFLINE_ONLY", "inputDirectory": str(input_dir), "filesPresent": present,
        "filesMissing": [name for name in INPUT_NAMES if name not in present],
        "sessionSummary": {"currentSessionId": current, "sessionIds": sorted(all_sessions),
                           "mixedSessions": len(all_sessions) > 1, "staleArtifacts": stale,
                           "runtimeVersion": semantic_status.get("build", {}).get("version", native_status.get("version")),
                           "buildId": semantic_status.get("build", {}).get("buildId", native_status.get("buildId")),
                           "buildSupported": nested(semantic_status, "build", "supported"),
                           "fingerprintValidated": native_status.get("buildFingerprintValidated"),
                           "executableSha256Observed": sorted(executable_hashes),
                           "supportedExecutableSha256": SUPPORTED_EXE_SHA256,
                           "executableHashCompatibility": hash_compatibility,
                           "hookStates": hook_states,
                           "cleanShutdown": nested(semantic_status, "observers", "building_place", "runtime", "stoppedCleanly"),
                           "declaredEventCount": semantic_status.get("eventCount"),
                           "declaredDroppedEventCount": semantic_status.get("droppedEventCount")},
        "sessions": session_rows,
        "singlePlacementCarrier": {
            "attemptCount": sum(s["singlePlacementCarrier"]["attemptCount"] for s in session_rows),
            "worldAuthority": "DISPROVEN_BUILD_1076226" if any(a["worldAuthorityAssessment"] == "DISPROVEN_BUILD_1076226" for s in session_rows for a in s["singlePlacementCarrier"]["attempts"]) else "INSUFFICIENT_EVIDENCE",
            "trackingItemIdHelperArgumentGeometryAuthority": "DISPROVEN_BUILD_1076226" if any(a["trackingItemIdHelperArgumentGeometryAuthority"] == "DISPROVEN_BUILD_1076226" for s in session_rows for a in s["singlePlacementCarrier"]["attempts"]) else "INSUFFICIENT_EVIDENCE",
            "attempts": [a for s in session_rows for a in s["singlePlacementCarrier"]["attempts"]],
        },
        "recordedStructures": recorded_structure_summary(project_root, warnings), "placementPlans": placement_plan_summary(project_root, warnings), "fieldValidation": {
            "counts": dict(sorted(Counter(v["captureAssessment"] for v in validations).items())),
            "checks": validations},
        "pointerTopology": [{"sessionId": s["sessionId"], "eventSequence": op["eventSequence"],
                             "sourcePointer": op["sourcePointer"], "destinationPointer": op["destinationPointer"],
                             "sourceSlot": op["sourceSlot"], "destinationSlot": op["destinationSlot"]}
                            for s in session_rows for op in s["inventoryOperations"]],
        "callerDistribution": dict(sorted(caller_counts.items())), "warnings": warnings,
        "idResolution": {"sources": id_sources, "resolvedCount": len(id_names),
                         "blueprintCatalogRows": len(blueprint_index),
                         "policy": "Raw IDs remain unresolved when no explicit local index exists; blueprint metadata comes only from explicit ArchitectDataIndex rows."},
        "createBuildingItemStatic": {
            "status": nested(create_static, "staticConclusion", "status"),
            "consumerFound": nested(create_static, "staticConclusion", "consumerFound"),
            "observerInstall": nested(create_static, "observerDecision", "install"),
            "fingerprintMatches": nested(create_static, "executable", "fingerprintMatches"),
        },
        "clientPlayerInputStatic": {
            "reflectionStatus": nested(client_input_static, "statusModel", "ClientPlayerInput_reflection"),
            "liveIdentityStatus": nested(client_input_static, "statusModel", "ClientPlayerInput_live_identity"),
            "observerInstalled": nested(client_input_static, "candidateClientPlayerInput", "observerInstall"),
            "fingerprintMatches": nested(client_input_static, "build", "fingerprintMatches"),
            "firstUnresolvedPointerTransition": nested(client_input_static, "knownInventoryTransferAnchor", "firstUnresolvedPointerTransition"),
        },
        "projectStatusTerminology": sorted(PROJECT_STATES), "captureAssessmentTerminology": sorted(CAPTURE_STATES),
        "statusRecommendations": confidence_recommendations(validations),
        "unresolvedMappings": ["CreateBuildingItemAction native consumer and dispatch boundary",
                               "ClientPlayerInput live owner of RSI+0x08 InventoryTransferAction",
                               "ClientPlayerInput producer/copy edge and parent pointer transition",
                               "CreateBuildingItemAction lifecycle (selection/preview/cancel/commit)",
                               "CreateBuildingItemAction.itemId ↔ BuildingPlaceEvent.trackingItemId causality",
                               "client/server side identity", "inventory ownership",
                               "final source post-state when only intermediate snapshots exist",
                               "concrete R14 type unless independently established"],
        "recommendedNextEvidence": recommendations(session_rows, warnings),
        "logSummary": {"lineCount": len(log.splitlines()),
                       "versionsMentioned": sorted(set(re.findall(r"\b\d+\.\d+\.\d+\b", log)))},
    }


def confidence_recommendations(validations: list[dict]) -> list[dict]:
    result = []
    for name in sorted({v["check"] for v in validations}):
        states = [v["captureAssessment"] for v in validations if v["check"] == name]
        if "CONTRADICTED_BY_CAPTURE" in states:
            recommendation = "review current project status; capture contradicts this relationship"
        elif "SUPPORTED_BY_CAPTURE" in states:
            recommendation = "capture supports the relationship; retain project status pending required independent validation"
        else:
            recommendation = "no project status change; insufficient capture evidence"
        result.append({"hypothesis": name, "captureAssessments": dict(Counter(states)),
                       "recommendedProjectStatusChange": None, "explanation": recommendation})
    return result


def recommendations(sessions: list[dict], warnings: list[dict]) -> list[str]:
    result = []
    if any(w["code"] in {"MIXED_SESSIONS", "STALE_SESSION_ARTIFACTS"} for w in warnings):
        result.append("Collect a clean bridge bundle from one fresh runtime session.")
    if not any(s["buildingOperations"] for s in sessions):
        result.append("Capture one committed placement after a preview/cancel control.")
    if not any(s["inventoryOperations"] for s in sessions):
        result.append("Capture the controlled 37 -> 13/24 -> move -> merge inventory sequence.")
    if not any(s["createBuildingItemActions"] for s in sessions):
        result.append("CreateBuildingItemAction observer is disabled; first resolve its native consumer statically before a live selection/preview/cancel/commit test.")
    if not result:
        result.append("Collect a v0.18 bundle with source slot/base fields to validate source and destination address equations live.")
    return result


def render_markdown(report: dict) -> str:
    summary = report["sessionSummary"]
    lines = ["# Latest Semantic Capture Report", "", "## Session summary", "",
             f"- Current session: `{summary['currentSessionId']}`",
             f"- Runtime: `{summary['runtimeVersion']}` / `{summary['buildId']}`",
             f"- Build supported: `{summary['buildSupported']}`; fingerprint validated: `{summary['fingerprintValidated']}`",
             f"- Mixed sessions: `{summary['mixedSessions']}`; clean shutdown: `{summary['cleanShutdown']}`",
             f"- Declared events/drops: `{summary['declaredEventCount']}` / `{summary['declaredDroppedEventCount']}`", ""]
    for session in report["sessions"]:
        lines += [f"## Session `{session['sessionId']}`", "",
                  f"Events: {session['eventCount']}. Preview/cancel-only candidate: `{session['previewOrCancelOnlyCandidate']}`.", "",
                  "### Building operations", ""]
        if not session["buildingOperations"]: lines.append("No building-place records.")
        for op in session["buildingOperations"]:
            lines.append(f"- Logical `{op['candidateLogicalPlacementId']}`: {op['recordCount']} record(s), payload equal `{op['pairPayloadEqual']}`, delta `{op['pairTimingMs']}` ms, threads `{op['threads']}`. No side classification assigned.")
            identity = op.get("blueprintIdentity", {})
            if identity.get("itemId") is not None:
                lines.append(f"  - Blueprint identity: item `{identity['itemId']}`, debugName `{identity.get('debugName')}`, dimensions `{identity.get('dimensions')}`, classification `{identity.get('classification')}`, snap-family `{identity.get('snapFamilyStatus')}`.")
        lines += ["", "### Inventory operations", ""]
        if not session["inventoryOperations"]: lines.append("No completed inventory records.")
        for op in session["inventoryOperations"]:
            states = ", ".join(f"{v['check']}={v['captureAssessment']}" for v in op["validations"])
            lines.append(f"- Event `{op['eventSequence']}` `{op['postPath']}`: destination `{op['destinationPre'].get('count')}` + `{op['transferAmount']}` -> `{op['destinationPost'].get('count')}`, caller `{op['callerRva']}`, thread `{op['threadId']}`. {states}.")
        lines += ["", "### InventoryTransferAction observations", ""]
        if not session["inventoryTransferActions"]: lines.append("No consumer-entry action records.")
        for correlation in session["actionOperationCorrelations"]:
            action=correlation["action"];states=", ".join(f"{v['check']}={v['captureAssessment']}" for v in correlation["checks"])
            lines.append(f"- Operation `{correlation['candidateInventoryOperationId']}`: type `{action.get('typeRaw')}`, actionAmountRaw `{correlation.get('actionAmountRaw')}`, effectiveTransferAmount `{correlation.get('effectiveTransferAmount')}`, item `{correlation.get('itemName')}`. {states}.")
        lines += ["", "### CreateBuildingItemAction observations", ""]
        if not session["createBuildingItemActions"]:
            lines.append("No create-building-item action records; native consumer observer remains disabled until static proof.")
        for action in session["createBuildingItemActions"]:
            lines.append(f"- Sequence `{action['eventSequence']}`: version `{action['versionRaw']}`, selectedIndex `{action['selectedIndexRaw']}`, itemId `{action['itemIdRaw']}` ({action['resolvedItemInfo']}); lifecycle `{action['lifecycle']}`.")
        for correlation in session["createActionPlacementCorrelations"]:
            lines.append(f"- Action `{correlation['actionEventSequence']}` nearest placement `{correlation['placementEventSequence']}`, delta `{correlation['timingDeltaMs']}` ms, item equality `{correlation['itemIdMatchesTrackingItemId']}`, confidence `{correlation['confidence']}`.")
        lines += ["", "### ClientPlayerInput parent observations", ""]
        if not session["clientPlayerInputSnapshots"]:
            lines.append("No parent-input observations; live ClientPlayerInput identity remains UNSOLVED.")
        for snapshot in session["clientPlayerInputSnapshots"]:
            lines.append(f"- Sequence `{snapshot['eventSequence']}` base `{snapshot['candidateBase']}`, inventory action `{snapshot['inventoryTransferActionAddress']}`, create version `{snapshot['createBuildingItemVersion']}`, item `{snapshot['createBuildingItemId']}`.")
        lines.append("")
    lines += ["## Caller distribution", ""]
    if report["callerDistribution"]:
        lines.extend(f"- `{caller}`: {count}" for caller, count in report["callerDistribution"].items())
    else: lines.append("No completed inventory callers observed.")
    lines += ["", "## Warnings", ""]
    lines.extend([f"- `{w['code']}`: {json.dumps(w, sort_keys=True)}" for w in report["warnings"]] or ["No parser/session warnings."])
    lines += ["", "## Unresolved mappings", ""] + [f"- {x}" for x in report["unresolvedMappings"]]
    lines += ["", "## Recommended next evidence", ""] + [f"- {x}" for x in report["recommendedNextEvidence"]]
    return "\n".join(lines) + "\n"
