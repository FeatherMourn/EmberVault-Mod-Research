"""Offline placement-plan CLI used by the optional F8 editor panel.

It only reads/writes Architect JSON files.  No bridge placement command or
game-process access exists in this module.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from tools.StructureEditor.plans import PlacementPlan, load_plan, save_plan  # noqa: E402
from tools.StructureRecorder.recorder import load_blueprint  # noqa: E402

BRIDGE = ROOT / "bridge"
STATE = BRIDGE / "structure_editor_state.json"
STATUS = BRIDGE / "structure_editor_status.json"
PLANS = ROOT / "blueprints" / "plans"
CATALOG = BRIDGE / "build_catalog.json"


def atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"); temporary.replace(path)


def state(plan: PlacementPlan | None) -> dict[str, object]:
    return {"schemaVersion": 1, "mode": "offline_plan_only", "plan": plan.to_dict() if plan else None}


def publish(plan: PlacementPlan | None, message: str = "") -> None:
    atomic(STATE, state(plan)); atomic(STATUS, {"schemaVersion": 1, "feature": "structure_editor", "message": message, "state": "ready" if plan else "idle", "backendStatus": "offline_plan_only", "replayAvailable": False, "worldMutationAvailable": False, "plan": (plan.to_dict() if plan else None)})


def load_state() -> PlacementPlan | None:
    try:
        value = json.loads(STATE.read_text(encoding="utf-8")); return PlacementPlan.from_dict(value["plan"]) if value.get("plan") else None
    except (OSError, ValueError, TypeError, json.JSONDecodeError, KeyError): return None


def catalog_ids() -> dict[int, dict[str, object]] | None:
    """Return the indexed local material/item catalog when available."""
    try:
        value = json.loads(CATALOG.read_text(encoding="utf-8"))
        return {int(entry["itemId"]): entry for entry in value.get("items", []) if isinstance(entry, dict) and isinstance(entry.get("itemId"), int)}
    except (OSError, ValueError, TypeError, json.JSONDecodeError, KeyError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="offline Architect placement plan editor")
    parser.add_argument("action", choices=["create", "load", "save", "translate", "rotate", "mirror", "undo", "redo", "reset", "enable", "disable", "enable_all", "disable_all", "duplicate", "delete", "move_up", "move_down", "move_start", "move_end", "material"])
    parser.add_argument("--source", type=Path); parser.add_argument("--file", type=Path); parser.add_argument("--name", default=None)
    parser.add_argument("--dx", type=float, default=0.0); parser.add_argument("--dy", type=float, default=0.0); parser.add_argument("--dz", type=float, default=0.0); parser.add_argument("--axis", default="y"); parser.add_argument("--degrees", type=float, default=90.0); parser.add_argument("--material-id", type=int); parser.add_argument("--placement-id", action="append", default=[])
    args = parser.parse_args(); plan = load_state()
    try:
        if args.action == "create":
            if not args.source: raise ValueError("--source is required")
            plan = PlacementPlan.load_source(args.source, args.name); publish(plan, "Plan created from immutable source recording"); return 0
        if args.action == "load":
            if not args.file: raise ValueError("--file is required")
            plan = load_plan(args.file); publish(plan, f"Loaded {args.file.name}"); return 0
        if plan is None: raise ValueError("no active offline placement plan")
        if args.action == "save":
            target = args.file or PLANS / f"{plan.name.replace(' ', '_')}.architect-plan.json"; save_plan(plan, target); publish(plan, f"Saved {target.name}"); print(target); return 0
        if args.action == "translate": plan.translate(args.dx, args.dy, args.dz)
        elif args.action == "rotate": plan.rotate(args.axis, args.degrees)
        elif args.action == "mirror": plan.mirror(args.axis)
        elif args.action == "undo": plan.undo()
        elif args.action == "redo": plan.redo()
        elif args.action == "reset": plan.reset_to_source()
        elif args.action == "enable": plan.set_enabled(True, args.placement_id or None)
        elif args.action == "disable": plan.set_enabled(False, args.placement_id or None)
        elif args.action == "enable_all": plan.enable_all()
        elif args.action == "disable_all": plan.set_enabled(False)
        elif args.action == "duplicate": plan.duplicate(args.placement_id or None)
        elif args.action == "delete": plan.delete(args.placement_id)
        elif args.action == "move_up":
            if len(args.placement_id) != 1: raise ValueError("move_up requires one --placement-id")
            plan.move_up(args.placement_id[0])
        elif args.action == "move_down":
            if len(args.placement_id) != 1: raise ValueError("move_down requires one --placement-id")
            plan.move_down(args.placement_id[0])
        elif args.action == "move_start":
            if len(args.placement_id) != 1: raise ValueError("move_start requires one --placement-id")
            plan.move_start(args.placement_id[0])
        elif args.action == "move_end":
            if len(args.placement_id) != 1: raise ValueError("move_end requires one --placement-id")
            plan.move_end(args.placement_id[0])
        elif args.action == "material":
            if args.material_id is None: raise ValueError("material requires --material-id")
            catalog = catalog_ids()
            if catalog is None: raise ValueError("indexed Build Catalog unavailable; material substitution refused")
            plan.substitute_material(args.material_id, args.placement_id or None, catalog=catalog)
        publish(plan, f"Applied offline action: {args.action}"); return 0
    except (OSError, ValueError, TypeError) as exc:
        publish(plan, f"Offline plan action failed: {exc}"); return 2


if __name__ == "__main__": raise SystemExit(main())
