"""Offline ArchitectPlacementPlan model and bounded editor history."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import uuid
from pathlib import Path
from typing import Any, Iterable

try:
    from tools.StructureRecorder.recorder import RecordingSession, load_blueprint
except ImportError:  # direct CLI invocation
    from StructureRecorder.recorder import RecordingSession, load_blueprint
try:
    from .transforms import axis_quaternion, bounds_for_placement, transform_placement
except ImportError:
    from transforms import axis_quaternion, bounds_for_placement, transform_placement

SCHEMA = "architect.placement_plan.v1"
SCHEMA_VERSION = 1
HISTORY_LIMIT = 100


def _finite(value: Any) -> bool:
    if isinstance(value, (list, tuple)): return all(_finite(x) for x in value)
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _sha(path: Path | None) -> str | None:
    if path is None or not path.is_file(): return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""): digest.update(block)
    return digest.hexdigest()


def _new_id(prefix: str = "plan") -> str:
    return f"{prefix}-{uuid.uuid4()}"


class PlacementPlan:
    def __init__(self, *, name: str, source: dict[str, Any], placements: list[dict[str, Any]], pivot: dict[str, Any] | None = None, plan_id: str | None = None, history_limit: int = HISTORY_LIMIT):
        self.name, self.sourceStructure, self.placements = name, copy.deepcopy(source), copy.deepcopy(placements)
        self.placementPlanId = plan_id or _new_id(); self.pivot = copy.deepcopy(pivot or {"mode": "recording_origin", "position": [0.0, 0.0, 0.0]})
        self.history_limit = max(1, int(history_limit)); self._undo: list[dict[str, Any]] = []; self._redo: list[dict[str, Any]] = []
        self._source_snapshot = copy.deepcopy(self.placements); self._source_pivot = copy.deepcopy(self.pivot)
        self.recompute()

    @classmethod
    def from_recording(cls, recording: RecordingSession, source_path: Path | None = None, name: str | None = None) -> "PlacementPlan":
        placements = []
        for index, source in enumerate(recording.placements, 1):
            raw, derived = source.get("raw", {}), source.get("derived", {})
            source_enrichment = source.get("enrichment", {})
            useful_enrichment = {key: source_enrichment.get(key) for key in ("debugName", "itemInfoGuid", "classification", "snapFamily") if key in source_enrichment}
            placements.append({"planPlacementId": _new_id("placement"), "sourcePlacementSequence": source.get("sequence", index), "sourceLogicalPlacementId": source.get("logicalPlacementId"), "provenance": {"kind": "source", "sourcePlacementSequence": source.get("sequence", index)}, "derived": False, "enabled": True, "order": index, "itemId": raw.get("trackingItemId"), "material": raw.get("material"), "originalMaterial": raw.get("material"), "plannedMaterial": raw.get("material"), "localPosition": list(derived.get("localPosition", [0.0, 0.0, 0.0])), "orientationQuaternion": list(raw.get("orientation", [0.0, 0.0, 0.0, 1.0])), "localVolume": {"min": list(raw.get("volumeMin", [0.0, 0.0, 0.0])), "max": list(raw.get("volumeMax", [0.0, 0.0, 0.0]))}, "enrichment": useful_enrichment})
        source_data = {"schema": "architect.structure.v1", "recordingId": recording.recording_id, "sourceFilename": source_path.name if source_path else None, "sourceSha256": _sha(source_path), "gameBuild": recording.game_build}
        return cls(name=name or recording.name, source=source_data, placements=placements)

    @classmethod
    def load_source(cls, path: Path, name: str | None = None) -> "PlacementPlan":
        return cls.from_recording(load_blueprint(path), path, name)

    def _snapshot(self) -> dict[str, Any]: return {"placements": copy.deepcopy(self.placements), "pivot": copy.deepcopy(self.pivot)}
    def _record(self) -> None:
        self._undo.append(self._snapshot()); self._undo = self._undo[-self.history_limit:]; self._redo.clear()
    def _restore(self, snapshot: dict[str, Any]) -> None: self.placements, self.pivot = copy.deepcopy(snapshot["placements"]), copy.deepcopy(snapshot["pivot"]); self.recompute()

    def reset_to_source(self) -> None: self._record(); self.placements, self.pivot = copy.deepcopy(self._source_snapshot), copy.deepcopy(self._source_pivot); self.recompute()
    def undo(self) -> bool:
        if not self._undo: return False
        self._redo.append(self._snapshot()); self._restore(self._undo.pop()); return True
    def redo(self) -> bool:
        if not self._redo: return False
        self._undo.append(self._snapshot()); self._restore(self._redo.pop()); return True

    def _selected(self, selection: Iterable[str] | None, enabled_only: bool = False) -> list[dict[str, Any]]:
        wanted = set(selection or [p["planPlacementId"] for p in self.placements]); return [p for p in self.placements if p["planPlacementId"] in wanted and (not enabled_only or p.get("enabled", True))]
    def translate(self, dx: float, dy: float, dz: float, selection: Iterable[str] | None = None, enabled_only: bool = False) -> None:
        delta = [float(dx), float(dy), float(dz)]
        if not _finite(delta): raise ValueError("translation must be finite")
        self._record()
        for p in self._selected(selection, enabled_only): p["localPosition"] = [p["localPosition"][i] + delta[i] for i in range(3)]
        self.recompute()

    def rotate(self, axis: str, degrees: float, selection: Iterable[str] | None = None, pivot: Iterable[float] | None = None) -> None:
        pivot_value = list(pivot if pivot is not None else self.pivot.get("position", [0.0, 0.0, 0.0])); rotation = axis_quaternion(axis, degrees); self._record()
        for p in self._selected(selection):
            position, orientation = transform_placement(p["localPosition"], p["orientationQuaternion"], pivot_value, rotation)
            p["localPosition"], p["orientationQuaternion"] = list(position), list(orientation)
        self.recompute()

    def set_pivot(self, mode: str, position: Iterable[float] | None = None, selected_id: str | None = None) -> None:
        mode = mode.lower()
        if mode == "recording_origin": value = [0.0, 0.0, 0.0]
        elif mode == "bounds_center":
            b = self.statistics()["enabledPlacementsBounds"]; value = [((b["min"][i] + b["max"][i]) / 2) for i in range(3)] if b.get("min") else [0.0, 0.0, 0.0]
        elif mode == "selected_placement":
            selected = next((p for p in self.placements if p["planPlacementId"] == selected_id), None)
            if selected is None: raise ValueError("selected placement is required")
            value = selected["localPosition"]
        elif mode == "manual": value = list(position or [])
        else: raise ValueError("unknown pivot mode")
        if not _finite(value) or len(value) != 3: raise ValueError("pivot must contain three finite values")
        self._record(); self.pivot = {"mode": mode, "position": [float(x) for x in value]}; self.recompute()

    def rebase_local_origin(self, origin: Iterable[float]) -> None:
        shift = list(origin)
        if len(shift) != 3 or not _finite(shift): raise ValueError("origin must contain three finite values")
        self._record()
        for p in self.placements: p["localPosition"] = [p["localPosition"][i] - float(shift[i]) for i in range(3)]
        self.pivot["position"] = [self.pivot.get("position", [0, 0, 0])[i] - float(shift[i]) for i in range(3)]
        self.recompute()

    def set_enabled(self, enabled: bool, selection: Iterable[str] | None = None) -> None:
        self._record()
        for p in self._selected(selection): p["enabled"] = bool(enabled)
        self.recompute()
    def enable_all(self) -> None: self.set_enabled(True, None)

    def duplicate(self, selection: Iterable[str] | None = None) -> list[str]:
        self._record(); result = []
        for p in self._selected(selection):
            clone = copy.deepcopy(p); clone["planPlacementId"] = _new_id("placement"); clone["derived"] = True; clone["provenance"] = {"kind": "derived_from", "sourcePlanPlacementId": p["planPlacementId"]}; clone["order"] = len(self.placements) + 1; self.placements.append(clone); result.append(clone["planPlacementId"])
        self.recompute(); return result
    def delete(self, selection: Iterable[str] | None = None) -> None:
        wanted = set(selection or []); self._record(); self.placements = [p for p in self.placements if p["planPlacementId"] not in wanted]; self._renumber(); self.recompute()
    def _renumber(self) -> None:
        for i, p in enumerate(self.placements, 1): p["order"] = i
    def move(self, selection: str, direction: str) -> None:
        index = next((i for i,p in enumerate(self.placements) if p["planPlacementId"] == selection), None)
        if index is None: raise ValueError("placement not found")
        target = {"up": index-1, "down": index+1, "start": 0, "end": len(self.placements)-1}.get(direction)
        if target is None or target < 0 or target >= len(self.placements): return
        self._record(); item = self.placements.pop(index); self.placements.insert(target, item); self._renumber(); self.recompute()
    def move_up(self, selection: str) -> None: self.move(selection, "up")
    def move_down(self, selection: str) -> None: self.move(selection, "down")
    def move_start(self, selection: str) -> None: self.move(selection, "start")
    def move_end(self, selection: str) -> None: self.move(selection, "end")

    def substitute_material(self, material: int, selection: Iterable[str] | None = None, catalog: dict[int, dict[str, Any]] | None = None) -> None:
        if isinstance(material, bool) or not isinstance(material, int): raise ValueError("material must be an integer ID")
        if catalog is not None and material not in catalog: raise ValueError("unresolved material ID")
        self._record()
        for p in self._selected(selection): p["plannedMaterial"], p["material"] = material, material
        self.recompute()

    def mirror(self, axis: str, selection: Iterable[str] | None = None) -> None:
        axis = axis.lower(); index = {"x": 0, "y": 1, "z": 2}.get(axis)
        if index is None: raise ValueError("mirror axis must be x, y, or z")
        pivot = self.pivot.get("position", [0.0, 0.0, 0.0]); self._record()
        for p in self._selected(selection): p["localPosition"][index] = 2 * pivot[index] - p["localPosition"][index]
        self.recompute(); self._mirror_warning = "Layout Mirror (Experimental): mirrorReplayCompatibility=UNSOLVED"

    def recompute(self) -> None:
        for p in self.placements:
            bounds = bounds_for_placement(p["localPosition"], p["orientationQuaternion"], p["localVolume"]["min"], p["localVolume"]["max"])
            p["derivedBounds"] = bounds
        self._statistics = self._calc_stats()

    def _calc_bounds(self, placements: list[dict[str, Any]]) -> dict[str, Any]:
        if not placements: return {"min": None, "max": None, "size": None}
        mins = [min(p["derivedBounds"]["min"][i] for p in placements) for i in range(3)]; maxs = [max(p["derivedBounds"]["max"][i] for p in placements) for i in range(3)]
        return {"min": mins, "max": maxs, "size": [maxs[i] - mins[i] for i in range(3)]}
    def _calc_stats(self) -> dict[str, Any]:
        enabled = [p for p in self.placements if p.get("enabled", True)]; materials = {}
        for p in enabled: materials[str(p.get("material"))] = materials.get(str(p.get("material")), 0) + 1
        return {"totalPlacements": len(self.placements), "enabledPlacements": len(enabled), "disabledPlacements": len(self.placements)-len(enabled), "uniqueItemIds": len({p.get("itemId") for p in enabled}), "materialCounts": materials, "plannedMaterialSubstitutions": sum(p.get("plannedMaterial") != p.get("originalMaterial") for p in self.placements), "allPlacementsBounds": self._calc_bounds(self.placements), "enabledPlacementsBounds": self._calc_bounds(enabled), "derivedPlacements": sum(bool(p.get("derived")) for p in self.placements), "sourcePlacements": sum(not bool(p.get("derived")) for p in self.placements), "mirrorReplayCompatibility": "UNSOLVED"}
    def statistics(self) -> dict[str, Any]: return copy.deepcopy(self._statistics)

    def validate(self) -> dict[str, Any]:
        errors, warnings, info = [], [], []
        if not self.sourceStructure.get("recordingId"): errors.append({"severity": "ERROR", "code": "missing_source_recording"})
        ids, orders = set(), set()
        for p in self.placements:
            if p.get("planPlacementId") in ids: errors.append({"severity": "ERROR", "code": "duplicate_planPlacementId"})
            ids.add(p.get("planPlacementId")); orders.add(p.get("order"))
            if not isinstance(p.get("itemId"), int) or isinstance(p.get("itemId"), bool): errors.append({"severity": "ERROR", "code": "invalid_item_id"})
            if not isinstance(p.get("material"), int) or isinstance(p.get("material"), bool): warnings.append({"severity": "WARNING", "code": "unresolved_material"})
            if not isinstance(p.get("enabled"), bool): errors.append({"severity": "ERROR", "code": "enabled_not_boolean"})
            if not isinstance(p.get("localPosition"), list) or len(p["localPosition"]) != 3 or not _finite(p["localPosition"]): errors.append({"severity": "ERROR", "code": "invalid_position"})
            q = p.get("orientationQuaternion")
            if not isinstance(q, list) or len(q) != 4 or not _finite(q): errors.append({"severity": "ERROR", "code": "invalid_orientation"})
            elif abs(math.sqrt(sum(float(x)*float(x) for x in q))-1.0) > 1e-3: warnings.append({"severity": "WARNING", "code": "orientation_not_normalized"})
        if len(orders) != len(self.placements): errors.append({"severity": "ERROR", "code": "duplicate_order"})
        warnings.extend([{"severity": "WARNING", "code": "orientation_convention_unvalidated", "detail": "internal XYZW transform is DERIVED_EXPERIMENTAL"}, {"severity": "WARNING", "code": "mirror_replay_unsolved"}])
        info.append({"severity": "INFO", "code": "offline_only"})
        return {"valid": not errors, "errors": errors, "warnings": warnings, "info": info}

    def to_dict(self) -> dict[str, Any]:
        validation = self.validate(); return {"schema": SCHEMA, "schemaVersion": SCHEMA_VERSION, "name": self.name, "placementPlanId": self.placementPlanId, "sourceStructure": copy.deepcopy(self.sourceStructure), "sourceSnapshot": {"placements": copy.deepcopy(self._source_snapshot), "pivot": copy.deepcopy(self._source_pivot)}, "coordinateSystem": {"encoding": "signed_q32_32", "scale": 4294967296, "status": "PROVEN_BUILD_1076226", "planCalculation": "double_precision_human_scale_offline"}, "pivot": copy.deepcopy(self.pivot), "operations": {"historyLimit": self.history_limit, "undoDepth": len(self._undo), "redoDepth": len(self._redo)}, "placements": copy.deepcopy(self.placements), "statistics": self.statistics(), "compatibility": {"backendStatus": "offline_plan_only", "replayAvailable": False, "worldMutationAvailable": False, "sourceBuildCompatible": self.sourceStructure.get("gameBuild") == 1076226, "allItemsResolved": all(isinstance(p.get("itemId"), int) for p in self.placements), "allMaterialsResolved": False, "orientationConventionValidated": False, "mirrorCompatibility": "UNSOLVED", "coordinateEncodingSupported": True}, "validation": validation, "provenance": {"sourceIsImmutableEvidence": True, "editedStateIsDerived": True, "replayCapability": "none"}}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PlacementPlan":
        validate_plan(value); plan = cls(name=value["name"], source=value["sourceStructure"], placements=value["placements"], pivot=value.get("pivot"), plan_id=value["placementPlanId"], history_limit=(value.get("operations") or {}).get("historyLimit", HISTORY_LIMIT)); source_snapshot = value.get("sourceSnapshot")
        if isinstance(source_snapshot, dict) and isinstance(source_snapshot.get("placements"), list) and isinstance(source_snapshot.get("pivot"), dict):
            plan._source_snapshot = copy.deepcopy(source_snapshot["placements"]); plan._source_pivot = copy.deepcopy(source_snapshot["pivot"])
        else:
            plan._source_snapshot = copy.deepcopy(plan.placements); plan._source_pivot = copy.deepcopy(plan.pivot)
        return plan


def validate_plan(value: dict[str, Any]) -> None:
    required = {"schema", "schemaVersion", "name", "placementPlanId", "sourceStructure", "coordinateSystem", "pivot", "placements", "statistics", "compatibility", "provenance"}
    missing = required - set(value)
    if missing: raise ValueError(f"missing plan fields: {sorted(missing)}")
    if value["schema"] != SCHEMA or value["schemaVersion"] != SCHEMA_VERSION: raise ValueError("unsupported placement plan schema")
    if not isinstance(value.get("name"), str) or not value["name"] or not isinstance(value.get("placementPlanId"), str) or not value["placementPlanId"]:
        raise ValueError("plan identity is invalid")
    source = value.get("sourceStructure", {})
    if not isinstance(source, dict) or source.get("schema") != "architect.structure.v1" or not source.get("recordingId"):
        raise ValueError("source recording provenance is missing")
    coordinate = value.get("coordinateSystem", {})
    if coordinate.get("encoding") != "signed_q32_32" or coordinate.get("scale") != 4294967296:
        raise ValueError("unsupported plan coordinate system")
    pivot = value.get("pivot", {})
    if not isinstance(pivot, dict) or not isinstance(pivot.get("position"), list) or len(pivot["position"]) != 3 or not _finite(pivot["position"]):
        raise ValueError("invalid plan pivot")
    if not isinstance(value["placements"], list): raise ValueError("placements must be an array")
    ids = [p.get("planPlacementId") for p in value["placements"]]
    if len(ids) != len(set(ids)): raise ValueError("duplicate plan placement IDs")
    orders = []
    for placement in value["placements"]:
        if not isinstance(placement, dict): raise ValueError("placement must be an object")
        if not isinstance(placement.get("planPlacementId"), str) or not placement["planPlacementId"]: raise ValueError("invalid plan placement ID")
        if not isinstance(placement.get("sourcePlacementSequence"), int): raise ValueError("missing source provenance")
        if not isinstance(placement.get("order"), int): raise ValueError("placement order must be integer")
        orders.append(placement["order"])
    if len(orders) != len(set(orders)): raise ValueError("duplicate placement order")
    source_snapshot = value.get("sourceSnapshot")
    if source_snapshot is not None:
        if not isinstance(source_snapshot, dict) or not isinstance(source_snapshot.get("placements"), list) or not isinstance(source_snapshot.get("pivot"), dict):
            raise ValueError("invalid source snapshot")
        snapshot_ids = []
        for placement in source_snapshot["placements"]:
            if not isinstance(placement, dict) or not isinstance(placement.get("planPlacementId"), str) or not placement["planPlacementId"]:
                raise ValueError("invalid source snapshot placement")
            snapshot_ids.append(placement["planPlacementId"])
        if len(snapshot_ids) != len(set(snapshot_ids)): raise ValueError("duplicate source snapshot placement IDs")


def save_plan(plan: PlacementPlan, path: Path) -> None:
    value = plan.to_dict(); validate_plan(value)
    if not value["validation"]["valid"]: raise ValueError("plan contains validation errors")
    path.parent.mkdir(parents=True, exist_ok=True); temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp"); temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"); temporary.replace(path)


def load_plan(path: Path) -> PlacementPlan:
    with path.open("r", encoding="utf-8") as stream: return PlacementPlan.from_dict(json.load(stream))
