"""Versioned offline description of F8 backend operations.

This module is a protocol/data-definition aid only. It does not write bridge
commands and intentionally marks operations with no proven runtime handler as
unsupported.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class Operation(str, Enum):
    PREVIEW = "preview"
    SELECT_CARRIER_SHAPE = "select_carrier_shape"
    GENERATE_SHAPE = "generate_shape"
    PLACE = "place"
    CANCEL = "cancel"
    ROTATE = "rotate"
    MIRROR = "mirror"
    MATERIAL_CHANGE = "material_change"
    APPLY_TO_ARCHITECT_CARRIER = "apply_to_architect_carrier"
    CARRIER_LIVE_REFRESH_PROBE = "carrier_live_refresh_probe"
    START_RECORDING = "start_recording"
    STOP_RECORDING = "stop_recording"
    CANCEL_RECORDING = "cancel_recording"
    SAVE_RECORDING = "save_recording"
    LOAD_RECORDING = "load_recording"
    CREATE_PLAN = "create_plan"
    LOAD_PLAN = "load_plan"
    SAVE_PLAN = "save_plan"
    UNDO_PLAN = "undo_plan"
    REDO_PLAN = "redo_plan"
    RESET_PLAN = "reset_plan"


PROTOCOL_VERSION = 1
SUPPORT = {
    Operation.PREVIEW.value: True,
    Operation.SELECT_CARRIER_SHAPE.value: False,
    Operation.GENERATE_SHAPE.value: False,
    Operation.PLACE.value: True,
    Operation.CANCEL.value: True,
    Operation.ROTATE.value: False,
    Operation.MIRROR.value: False,
    Operation.MATERIAL_CHANGE.value: False,
    Operation.APPLY_TO_ARCHITECT_CARRIER.value: False,
    Operation.CARRIER_LIVE_REFRESH_PROBE.value: True,
    Operation.START_RECORDING.value: True,
    Operation.STOP_RECORDING.value: True,
    Operation.CANCEL_RECORDING.value: True,
    Operation.SAVE_RECORDING.value: True,
    Operation.LOAD_RECORDING.value: True,
    Operation.CREATE_PLAN.value: False,
    Operation.LOAD_PLAN.value: False,
    Operation.SAVE_PLAN.value: False,
    Operation.UNDO_PLAN.value: False,
    Operation.REDO_PLAN.value: False,
    Operation.RESET_PLAN.value: False,
}

PROCEDURAL_CONTROL_SCHEMA = {
    "shape": {"type": "string", "status": "offline-ready"},
    "radius": {"type": "number", "status": "offline-ready"},
    "width": {"type": "integer", "status": "offline-ready"},
    "height": {"type": "integer", "status": "offline-ready"},
    "hollow": {"type": "boolean", "status": "offline-ready"},
    "thickness": {"type": "number", "status": "offline-ready"},
    "axis": {"type": "enum[x,y,z]", "status": "offline-ready"},
    "rotate": {"type": "degrees-90", "status": "offline-ready"},
    "mirror": {"type": "object[xyz]", "status": "offline-ready"},
    "material": {"type": "object-or-id", "status": "experimental/unsupported-runtime"},
    "preview": {"type": "boolean", "status": "supported-existing-preview-path"},
    "applyToArchitectCarrier": {"type": "boolean", "status": "experimental/unsupported-runtime"},
    "carrierLiveRefreshProbe": {"type": "boolean", "status": "observe-only-runtime-probe"},
}


@dataclass(frozen=True)
class F8Command:
    operation: str
    payload: Mapping[str, Any]
    protocol_version: int = PROTOCOL_VERSION

    def validate(self) -> None:
        if self.protocol_version != PROTOCOL_VERSION: raise ValueError("unsupported protocol version")
        if self.operation not in SUPPORT: raise ValueError("unknown operation")
        if not SUPPORT[self.operation]: raise ValueError(f"operation is explicitly unsupported: {self.operation}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {"protocolVersion": self.protocol_version, "operation": self.operation, "payload": dict(self.payload)}
