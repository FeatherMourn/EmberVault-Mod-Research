"""Capture-only recorded structure model with lossless Q32.32 coordinates."""
from __future__ import annotations

import json
import math
import struct
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from .coordinates import (Q32_SCALE, coerce_raw_vector, coordinate_metadata,
                              decode_world, relative_raw, relative_world)
except ImportError:  # direct unittest/CLI import from this directory
    from coordinates import (Q32_SCALE, coerce_raw_vector, coordinate_metadata,
                             decode_world, relative_raw, relative_world)

SCHEMA = "architect.structure.v1"
GAME_BUILD = 1076226
ARCHITECT_VERSION = "0.29.1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _vec(values: Any, n: int) -> list[float]:
    if not isinstance(values, (list, tuple)) or len(values) < n:
        return [0.0] * n
    return [_num(values[i]) for i in range(n)]


def _finite_vec(values: list[float]) -> bool:
    return all(math.isfinite(v) for v in values)


def _bits_to_float(values: Any, n: int) -> list[float] | None:
    if not isinstance(values, (list, tuple)) or len(values) < n:
        return None
    try:
        return [struct.unpack("<f", struct.pack("<I", int(values[i]) & 0xFFFFFFFF))[0] for i in range(n)]
    except (TypeError, ValueError, struct.error, OverflowError):
        return None


def _event_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("observer") != "building_place" or row.get("status") not in (None, "observed"):
        return None
    payload = row.get("payload")
    if not isinstance(payload, dict) or payload.get("trackingItemId") is None:
        return None
    return payload


def _logical_id(row: dict[str, Any]) -> Any:
    correlation = row.get("correlation")
    if isinstance(correlation, dict) and correlation.get("candidateLogicalPlacementId") is not None:
        return correlation.get("candidateLogicalPlacementId")
    return None


def _build_key(row: dict[str, Any]) -> str | None:
    logical = _logical_id(row)
    return None if logical is None else f"{row.get('sessionId', '')}:{logical}"


def _raw_position(payload: dict[str, Any]) -> tuple[list[int], str]:
    if isinstance(payload.get("grid"), (list, tuple)):
        return coerce_raw_vector(payload["grid"]), "grid_q32_32"
    return coerce_raw_vector(payload.get("position")), "position_legacy_q32_32"


def _quat_rotate(q: list[float], v: list[float]) -> list[float]:
    x, y, z, w = q
    t = [2.0 * (y * v[2] - z * v[1]), 2.0 * (z * v[0] - x * v[2]), 2.0 * (x * v[1] - y * v[0])]
    return [v[0] + w * t[0] + (y * t[2] - z * t[1]), v[1] + w * t[1] + (z * t[0] - x * t[2]), v[2] + w * t[2] + (x * t[1] - y * t[0])]


def _translated_volume(position: list[float], lo: list[float], hi: list[float], orientation: list[float]) -> dict[str, Any]:
    corners = [[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    identity = abs(orientation[0]) < 1e-6 and abs(orientation[1]) < 1e-6 and abs(orientation[2]) < 1e-6 and abs(abs(orientation[3]) - 1.0) < 1e-6
    rotated = corners if identity else [_quat_rotate(orientation, corner) for corner in corners]
    points = [[position[i] + corner[i] for i in range(3)] for corner in rotated]
    return {"min": [min(point[i] for point in points) for i in range(3)], "max": [max(point[i] for point in points) for i in range(3)], "transform": "translation_identity" if identity else "translation_plus_quaternion_corner_transform_inferred", "rotationBoundsConfidence": "PROVEN_FOR_IDENTITY" if identity else "INFERRED"}


def _migrate_placement(p: dict[str, Any]) -> dict[str, Any]:
    raw = p.get("raw") if isinstance(p, dict) else None
    if not isinstance(raw, dict):
        return p
    try:
        raw_position = coerce_raw_vector(raw.get("gridRaw", raw.get("position")))
    except ValueError:
        return p
    raw["position"] = raw_position
    raw["positionRaw"] = raw_position[:]
    if not isinstance(raw.get("gridRaw"), list):
        raw["gridRaw"] = raw_position[:]
    p.setdefault("rawEvidence", {"trackingItemId": raw.get("trackingItemId"), "material": raw.get("material"), "positionRaw": raw_position[:], "gridRaw": raw.get("gridRaw"), "orientationBitsRaw": raw.get("orientationBitsRaw"), "volumeMinBitsRaw": raw.get("volumeMinBitsRaw"), "volumeMaxBitsRaw": raw.get("volumeMaxBitsRaw")})
    p.setdefault("canonical", {})
    return p


@dataclass
class RecordingSession:
    recording_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Recording"
    game_build: int = GAME_BUILD
    source_session_id: str | None = None
    start_raw_event_sequence: int | None = None
    end_raw_event_sequence: int | None = None
    start_timestamp: str = field(default_factory=_now)
    stop_timestamp: str | None = None
    state: str = "recording"
    origin_mode: str = "first_committed_position"
    origin_placement_sequence: int | None = None
    placements: list[dict[str, Any]] = field(default_factory=list)
    ambiguous_raw_events: int = 0
    raw_event_count: int = 0
    semantic_stream_events_observed: int = 0
    building_raw_events_in_recording_window: int = 0
    paired_building_raw_events: int = 0
    ignored_non_building_events: int = 0
    snap_resolution_status: str = "unresolved_without_explicit_item_snap_link"
    counter_evidence: str = "counted_from_unique_stream_sequences"
    _seen_stream_keys: set[str] = field(default_factory=set, repr=False)
    _logical_raw_counts: dict[str, int] = field(default_factory=dict, repr=False)

    def ingest(self, rows: Iterable[dict[str, Any]]) -> int:
        seen_placements = {p.get("logicalPlacementKey") for p in self.placements}
        added = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            sequence_value = row.get("rawEventSequence", row.get("eventSequence"))
            try: sequence = int(sequence_value)
            except (TypeError, ValueError): sequence = None
            if self.start_raw_event_sequence is not None and sequence is not None and sequence <= self.start_raw_event_sequence:
                continue
            identity = f"seq:{sequence}" if sequence is not None else "row:" + json.dumps(row, sort_keys=True, separators=(",", ":"), default=str)
            if identity in self._seen_stream_keys:
                continue
            self._seen_stream_keys.add(identity)
            self.semantic_stream_events_observed += 1
            if sequence is not None: self.end_raw_event_sequence = max(self.end_raw_event_sequence or sequence, sequence)
            payload = _event_payload(row)
            if payload is None:
                self.ignored_non_building_events += 1
                continue
            self.building_raw_events_in_recording_window += 1
            self.raw_event_count = self.building_raw_events_in_recording_window
            sid = row.get("sessionId")
            if self.source_session_id is None: self.source_session_id = sid
            if sid != self.source_session_id:
                self.state = "cancelled"; self.ambiguous_raw_events += 1; continue
            key = _build_key(row)
            if key is None:
                self.ambiguous_raw_events += 1; continue
            count = self._logical_raw_counts.get(key, 0) + 1
            self._logical_raw_counts[key] = count
            if count == 2: self.paired_building_raw_events += 2
            elif count > 2: self.paired_building_raw_events += 1
            if key in seen_placements: continue
            try: raw_position, position_source = _raw_position(payload)
            except ValueError:
                self.ambiguous_raw_events += 1; continue
            orientation_bits = payload.get("orientationBits")
            orientation = _vec(payload.get("orientation"), 4) if isinstance(payload.get("orientation"), (list, tuple)) else (_bits_to_float(orientation_bits, 4) or [0.0] * 4)
            vmin_bits, vmax_bits = payload.get("volumeMinBits"), payload.get("volumeMaxBits")
            vmin = _vec(payload.get("volumeMin"), 3) if isinstance(payload.get("volumeMin"), (list, tuple)) else (_bits_to_float(vmin_bits, 3) or [0.0] * 3)
            vmax = _vec(payload.get("volumeMax"), 3) if isinstance(payload.get("volumeMax"), (list, tuple)) else (_bits_to_float(vmax_bits, 3) or [0.0] * 3)
            if not (_finite_vec(orientation) and _finite_vec(vmin) and _finite_vec(vmax)):
                self.ambiguous_raw_events += 1
                continue
            raw_evidence = {"trackingItemId": int(payload.get("trackingItemId", 0)), "material": payload.get("material"), "positionRaw": raw_position[:], "gridRaw": (coerce_raw_vector(payload["grid"]) if isinstance(payload.get("grid"), (list, tuple)) else raw_position[:]), "orientationBitsRaw": orientation_bits, "volumeMinBitsRaw": vmin_bits, "volumeMaxBitsRaw": vmax_bits}
            p = {"sequence": len(self.placements) + 1, "logicalPlacementKey": key, "logicalPlacementId": _logical_id(row), "raw": {"trackingItemId": int(payload.get("trackingItemId", 0)), "material": payload.get("material"), "position": raw_position, "positionRaw": raw_position[:], "positionSource": position_source, "gridRaw": raw_evidence["gridRaw"], "orientation": orientation, "orientationBitsRaw": orientation_bits, "volumeMin": vmin, "volumeMax": vmax, "volumeMinBitsRaw": vmin_bits, "volumeMaxBitsRaw": vmax_bits, "ownerId": payload.get("ownerId")}, "rawEvidence": raw_evidence, "canonical": {}, "derived": {}, "enrichment": {}, "evidence": {"sessionId": sid, "rawEventSequence": sequence_value, "threadId": row.get("threadId"), "timestamp": row.get("timestamp"), "pair": row.get("correlation")}}
            self.placements.append(p); seen_placements.add(key); added += 1
        self._recompute_derived(); return added

    def _recompute_derived(self) -> None:
        if not self.placements:
            self.origin_placement_sequence = None; return
        origin = self.placements[0]["raw"].get("positionRaw", self.placements[0]["raw"]["position"])
        self.origin_placement_sequence = self.placements[0]["sequence"]
        for p in self.placements:
            raw = p["raw"]; pos = raw.get("positionRaw", raw["position"]); world = decode_world(pos); local_raw = relative_raw(pos, origin); local = relative_world(pos, origin)
            orientation = raw.get("orientation", [0.0, 0.0, 0.0, 1.0]); lo, hi = raw.get("volumeMin", [0.0] * 3), raw.get("volumeMax", [0.0] * 3)
            local_volume = _translated_volume(local, lo, hi, orientation); world_volume = _translated_volume(world, lo, hi, orientation)
            p["derived"].update({"worldPosition": world, "localPosition": local, "localPositionRaw": local_raw, "placementOrdinal": p["sequence"], "placementLocalVolume": local_volume, "placementWorldVolume": world_volume, "coordinateScale": Q32_SCALE})
            p["canonical"] = {"trackingItemId": raw.get("trackingItemId"), "material": raw.get("material"), "worldPosition": world, "localPosition": local, "orientation": orientation, "volumeMin": lo, "volumeMax": hi, "localVolume": local_volume, "worldVolume": world_volume}

    def set_window_end(self, sequence: int | None = None) -> None:
        if sequence is not None: self.end_raw_event_sequence = int(sequence)

    def stop(self) -> None:
        if self.state == "recording": self.stop_timestamp = _now(); self.state = "stopped"

    def cancel(self) -> None:
        self.stop_timestamp = _now(); self.state = "cancelled"

    def statistics(self) -> dict[str, Any]:
        items = Counter(str(p["raw"].get("trackingItemId")) for p in self.placements); materials = Counter(str(p["raw"].get("material")) for p in self.placements); classes = Counter(str(p.get("enrichment", {}).get("classification") or "unresolved") for p in self.placements); snaps = Counter(str(p.get("enrichment", {}).get("snapFamily") or "unresolved") for p in self.placements)
        points_min: list[float] | None = None; points_max: list[float] | None = None; world_min: list[float] | None = None; world_max: list[float] | None = None
        for p in self.placements:
            bounds = p.get("derived", {}).get("placementLocalVolume", {}); lo, hi = bounds.get("min"), bounds.get("max")
            if not isinstance(lo, list) or not isinstance(hi, list) or not (_finite_vec(lo) and _finite_vec(hi)): continue
            points_min = lo[:] if points_min is None else [min(points_min[i], lo[i]) for i in range(3)]; points_max = hi[:] if points_max is None else [max(points_max[i], hi[i]) for i in range(3)]
            world_bounds = p.get("derived", {}).get("placementWorldVolume", {}); wlo, whi = world_bounds.get("min"), world_bounds.get("max")
            if isinstance(wlo, list) and isinstance(whi, list) and _finite_vec(wlo) and _finite_vec(whi):
                world_min = wlo[:] if world_min is None else [min(world_min[i], wlo[i]) for i in range(3)]; world_max = whi[:] if world_max is None else [max(world_max[i], whi[i]) for i in range(3)]
        bounds = {"min": points_min, "max": points_max, "size": ([points_max[i] - points_min[i] for i in range(3)] if points_min and points_max else None), "basis": "translated_BuildingPlaceEvent_volumes_in_local_coordinates", "rotationPolicy": "identity_exact; quaternion_corner_transform_inferred_for_non_identity"}
        world_bounds = {"min": world_min, "max": world_max, "size": ([world_max[i] - world_min[i] for i in range(3)] if world_min and world_max else None), "basis": "translated_BuildingPlaceEvent_volumes_in_world_coordinates"}
        return {"logicalPlacementCount": len(self.placements), "uniqueItemIds": len(items), "itemCounts": dict(items), "uniqueMaterials": len(materials), "materialCounts": dict(materials), "classificationCounts": dict(classes), "snapFamilyCounts": dict(snaps), "snapResolutionStatus": self.snap_resolution_status, "bounds": bounds, "worldBounds": world_bounds, "ambiguousRawEvents": self.ambiguous_raw_events, "semanticStreamEventsObserved": self.semantic_stream_events_observed, "buildingRawEventsInRecordingWindow": self.building_raw_events_in_recording_window, "pairedBuildingRawEvents": self.paired_building_raw_events, "logicalPlacementsRecorded": len(self.placements), "ignoredNonBuildingEvents": self.ignored_non_building_events, "counterEvidence": self.counter_evidence}

    def to_dict(self) -> dict[str, Any]:
        first = self.placements[0]["raw"].get("positionRaw", self.placements[0]["raw"]["position"]) if self.placements else None
        return {"schema": SCHEMA, "schemaVersion": 1, "gameBuild": self.game_build, "coordinateSystem": coordinate_metadata(), "name": self.name, "recordingId": self.recording_id, "state": self.state, "startTimestamp": self.start_timestamp, "stopTimestamp": self.stop_timestamp, "sourceSessionId": self.source_session_id, "recordingWindow": {"sourceSessionId": self.source_session_id, "startRawEventSequence": self.start_raw_event_sequence, "endRawEventSequence": self.end_raw_event_sequence, "semantics": "rows strictly after start and through end when stopped"}, "origin": {"mode": self.origin_mode, "placementSequence": self.origin_placement_sequence, "position": first, "positionRaw": first, "worldPosition": (decode_world(first) if first else None)}, "placements": self.placements, "statistics": self.statistics(), "provenance": {"architectVersion": ARCHITECT_VERSION, "sourceObserver": "existing BuildingPlaceEvent semantic observer", "captureMode": "capture_only_no_replay_backend", "rawEventCount": self.raw_event_count, "semanticStreamEventsObserved": self.semantic_stream_events_observed, "buildingRawEventsInRecordingWindow": self.building_raw_events_in_recording_window, "pairedBuildingRawEvents": self.paired_building_raw_events, "logicalPlacementsRecorded": len(self.placements), "ambiguousBuildingRawEvents": self.ambiguous_raw_events, "ignoredNonBuildingEvents": self.ignored_non_building_events, "counterEvidence": self.counter_evidence, "startRawEventSequence": self.start_raw_event_sequence, "endRawEventSequence": self.end_raw_event_sequence, "seenEventSequences": sorted(int(k[4:]) for k in self._seen_stream_keys if k.startswith("seq:"))[-4096:], "logicalRawEventCounts": dict(list(self._logical_raw_counts.items())[-4096:])}}

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "RecordingSession":
        migrated = dict(obj); migrated["placements"] = [_migrate_placement(dict(p)) for p in obj.get("placements", [])]; validate_blueprint(migrated); origin = migrated.get("origin") or {}; provenance = migrated.get("provenance") or {}
        legacy_stream_count = provenance.get("rawEventCount", 0)
        explicit_building = provenance.get("buildingRawEventsInRecordingWindow")
        explicit_paired = provenance.get("pairedBuildingRawEvents")
        inferred_paired = (2 * len(migrated["placements"]) if migrated["placements"] and all((p.get("evidence", {}).get("pair") or {}).get("candidatePair") for p in migrated["placements"]) else 0)
        building_count = int(explicit_building if explicit_building is not None else (inferred_paired + int(provenance.get("ambiguousBuildingRawEvents", 0))))
        paired_count = int(explicit_paired if explicit_paired is not None else inferred_paired)
        semantic_count = int(provenance.get("semanticStreamEventsObserved", legacy_stream_count))
        ignored_count = int(provenance.get("ignoredNonBuildingEvents", max(0, semantic_count - building_count)))
        counter_evidence = provenance.get("counterEvidence", "legacy_rawEventCount_stream_total; pair_count_inferred_from_candidatePair") if explicit_building is None else "counted_from_unique_stream_sequences"
        session = cls(recording_id=migrated["recordingId"], name=migrated["name"], game_build=migrated["gameBuild"], source_session_id=migrated.get("sourceSessionId"), start_raw_event_sequence=provenance.get("startRawEventSequence"), end_raw_event_sequence=provenance.get("endRawEventSequence"), start_timestamp=migrated["startTimestamp"], stop_timestamp=migrated.get("stopTimestamp"), state=migrated["state"], origin_mode=origin.get("mode", "first_committed_position"), origin_placement_sequence=origin.get("placementSequence"), placements=migrated["placements"], raw_event_count=building_count, semantic_stream_events_observed=semantic_count, building_raw_events_in_recording_window=building_count, paired_building_raw_events=paired_count, ambiguous_raw_events=provenance.get("ambiguousBuildingRawEvents", provenance.get("ambiguousRawEvents", 0)), ignored_non_building_events=ignored_count, counter_evidence=counter_evidence)
        session._seen_stream_keys = {f"seq:{int(value)}" for value in provenance.get("seenEventSequences", [])}
        for p in session.placements:
            sequence = p.get("evidence", {}).get("rawEventSequence")
            if sequence is not None:
                try: session._seen_stream_keys.add(f"seq:{int(sequence)}")
                except (TypeError, ValueError): pass
            key = p.get("logicalPlacementKey")
            if key: session._logical_raw_counts.setdefault(key, 1)
        session._logical_raw_counts.update({str(k): int(v) for k, v in provenance.get("logicalRawEventCounts", {}).items()})
        if session.end_raw_event_sequence is None:
            sequences = []
            for placement in session.placements:
                try: sequences.append(int(placement.get("evidence", {}).get("rawEventSequence")))
                except (TypeError, ValueError): pass
            if sequences: session.end_raw_event_sequence = max(sequences)
        session._recompute_derived(); return session


def validate_blueprint(obj: dict[str, Any]) -> None:
    required = ("schema", "schemaVersion", "gameBuild", "name", "recordingId", "state", "startTimestamp", "origin", "placements", "statistics", "provenance")
    if not isinstance(obj, dict) or any(k not in obj for k in required): raise ValueError("missing required recorded-structure field")
    if obj["schema"] != SCHEMA or obj["schemaVersion"] != 1 or obj["gameBuild"] != GAME_BUILD: raise ValueError("unsupported recorded-structure schema/build")
    if obj["state"] not in {"idle", "recording", "stopped", "cancelled", "saved", "loaded"}: raise ValueError("invalid recording state")
    if not isinstance(obj["placements"], list): raise ValueError("placements must be an array")
    for p in obj["placements"]:
        raw = p.get("raw") if isinstance(p, dict) else None
        if not isinstance(raw, dict) or not isinstance(raw.get("position"), list) or len(raw["position"]) != 3 or not isinstance(raw.get("orientation"), list) or len(raw["orientation"]) != 4: raise ValueError("invalid placement raw transform")
        try: coerce_raw_vector(raw["position"])
        except ValueError as exc: raise ValueError("invalid raw Q32.32 position") from exc
        if not _finite_vec([_num(x) for x in raw["orientation"]]): raise ValueError("non-finite placement orientation")
        for field_name in ("volumeMin", "volumeMax"):
            if raw.get(field_name) is not None and (not isinstance(raw[field_name], list) or len(raw[field_name]) != 3 or not _finite_vec([_num(x) for x in raw[field_name]])):
                raise ValueError("non-finite placement volume")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists(): return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: row = json.loads(line)
            except json.JSONDecodeError: continue
            if isinstance(row, dict): rows.append(row)
    return rows


def ingest_semantic_jsonl(path: Path, session: RecordingSession) -> int:
    return session.ingest(read_jsonl(path))


def enrich_from_catalog(session: RecordingSession, catalog_path: Path) -> None:
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8")); entries = {int(e["itemId"]): e for e in catalog.get("items", []) if isinstance(e, dict) and e.get("itemId") is not None}
    except (OSError, ValueError, TypeError, KeyError): return
    for placement in session.placements:
        raw = placement["raw"]; item = entries.get(int(raw.get("trackingItemId", 0)))
        if item: placement["enrichment"].update({"debugName": item.get("debugName"), "itemInfoGuid": item.get("guid"), "classification": item.get("classification"), "blueprint": item.get("blueprints"), "snapFamily": item.get("snapFamily")})
        material_id = raw.get("material"); material = next((e for e in entries.values() if e.get("placeVoxelMaterialId") == material_id and material_id not in (None, 0)), None)
        if material: placement["enrichment"]["materialName"] = material.get("debugName")


def save_blueprint(session: RecordingSession, path: Path) -> None:
    obj = session.to_dict(); obj["state"] = "saved"; validate_blueprint(obj); path.parent.mkdir(parents=True, exist_ok=True); temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp"); temporary.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"); temporary.replace(path)


def load_blueprint(path: Path) -> RecordingSession:
    with path.open("r", encoding="utf-8") as f: return RecordingSession.from_dict(json.load(f))
