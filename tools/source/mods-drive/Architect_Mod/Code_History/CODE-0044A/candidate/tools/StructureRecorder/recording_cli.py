"""Small capture-only CLI used by the F8 shell and offline tests."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from recorder import RecordingSession, enrich_from_catalog, ingest_semantic_jsonl, load_blueprint, read_jsonl, save_blueprint  # noqa: E402

BRIDGE = ROOT / "bridge"
STATE = BRIDGE / "structure_recorder_state.json"
STATUS = BRIDGE / "structure_recorder_status.json"
EVENTS = BRIDGE / "semantic_actions.jsonl"
CATALOG = BRIDGE / "build_catalog.json"
RECORDED = ROOT / "blueprints" / "recorded"


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def state_obj(session: RecordingSession | None) -> dict:
    return {"schemaVersion": 1, "mode": "capture_only_no_replay_backend", "session": (session.to_dict() if session else None)}


def write_status(session: RecordingSession | None, message: str = "") -> None:
    placements = []
    if session:
        for p in session.placements[-128:]:
            placements.append(p)
    atomic_json(STATUS, {"schemaVersion": 1, "feature": "structure_recorder", "state": (session.state if session else "idle"), "message": message, "placementCount": (len(session.placements) if session else 0), "placements": placements, "statistics": (session.statistics() if session else None), "provenance": (session.to_dict().get("provenance") if session else None)})


def latest_sequence() -> int | None:
    values = []
    for row in read_jsonl(EVENTS):
        try:
            values.append(int(row.get("rawEventSequence", row.get("eventSequence"))))
        except (TypeError, ValueError):
            continue
    return max(values) if values else None


def load_state() -> RecordingSession | None:
    if not STATE.exists():
        return None
    try:
        raw = json.loads(STATE.read_text(encoding="utf-8"))
        return RecordingSession.from_dict(raw["session"]) if raw.get("session") else None
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError):
        return None


BLUEPRINTS = ROOT / "runtime" / "blueprints"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["start", "stop", "cancel", "save", "load", "status", "start_recording", "stop_recording", "cancel_recording", "save_recording", "load_recording", "slice", "export_blueprint"])
    ap.add_argument("--name", default="Untitled Recording")
    ap.add_argument("--file", type=Path)
    ap.add_argument("--corner-a", nargs=3, type=float, metavar=("X", "Y", "Z"), help="Bounding box corner A coordinates in meters")
    ap.add_argument("--corner-b", nargs=3, type=float, metavar=("X", "Y", "Z"), help="Bounding box corner B coordinates in meters")
    ap.add_argument("--material", default="block.rough_stone", help="Default material block identifier")
    args = ap.parse_args()
    aliases = {"start_recording": "start", "stop_recording": "stop", "cancel_recording": "cancel", "save_recording": "save", "load_recording": "load", "export_blueprint": "save"}
    args.action = aliases.get(args.action, args.action)
    session = load_state()

    if args.action == "slice":
        a = args.corner_a or [0.0, 0.0, 0.0]
        b = args.corner_b or [10.0, 10.0, 10.0]
        min_x, max_x = min(a[0], b[0]), max(a[0], b[0])
        min_y, max_y = min(a[1], b[1]), max(a[1], b[1])
        min_z, max_z = min(a[2], b[2]), max(a[2], b[2])
        w = max(1, int(round(max_x - min_x)))
        h = max(1, int(round(max_y - min_y)))
        d = max(1, int(round(max_z - min_z)))

        materials = {}
        total_voxels = (w * 2) * (h * 2) * (d * 2)

        # Check if active session has placements inside bounding volume
        if session and session.placements:
            count = 0
            for p in session.placements:
                pos = (p.get("derived", {}).get("localPosition") or
                       p.get("raw", {}).get("position") or [0, 0, 0])
                if min_x <= pos[0] <= max_x and min_y <= pos[1] <= max_y and min_z <= pos[2] <= max_z:
                    mat = str(p.get("raw", {}).get("material") or args.material)
                    materials[mat] = materials.get(mat, 0) + 1
                    count += 1
            if count > 0:
                total_voxels = count * 64

        if not materials:
            materials[args.material] = total_voxels

        bp_id = f"bp-slice-{uuid.uuid4().hex[:8]}"
        target = args.file or (BLUEPRINTS / f"{bp_id}.json")
        target.parent.mkdir(parents=True, exist_ok=True)

        bp_obj = {
            "id": bp_id,
            "name": args.name if args.name != "Untitled Recording" else f"Sliced Volume ({w}x{h}x{d}m)",
            "version": "1.0",
            "category": "Recorded Slice",
            "description": f"Sliced bounding volume ({w}m W x {h}m H x {d}m D) between Corner A ({a[0]}, {a[1]}, {a[2]}) and Corner B ({b[0]}, {b[1]}, {b[2]}).",
            "author": "Structure Slicer",
            "created": Path(__file__).stat().st_mtime and datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "dimensions": {
                "width": w,
                "height": h,
                "depth": d,
                "totalVoxels": total_voxels
            },
            "materials": materials,
            "tags": ["Slice", "Recorded", "BoundingBox"],
            "boundingBox": {
                "cornerA": list(a),
                "cornerB": list(b),
                "min": [min_x, min_y, min_z],
                "max": [max_x, max_y, max_z]
            }
        }
        atomic_json(target, bp_obj)
        print(str(target))
        return 0

    if args.action == "start":
        existing = read_jsonl(EVENTS)
        sequences = []
        for row in existing:
            try: sequences.append(int(row.get("rawEventSequence", row.get("eventSequence"))))
            except (TypeError, ValueError): pass
        session = RecordingSession(name=args.name, start_raw_event_sequence=max(sequences) if sequences else None)
        atomic_json(STATE, state_obj(session)); write_status(session, "Recording started"); return 0
    if args.action == "status":
        if session and session.state == "recording": ingest_semantic_jsonl(EVENTS, session); enrich_from_catalog(session, CATALOG)
        atomic_json(STATE, state_obj(session) if session else {"session": None}); write_status(session); return 0
    if not session and args.action not in {"load"}:
        write_status(None, "No active recording session"); return 2
    if args.action == "stop":
        ingest_semantic_jsonl(EVENTS, session); enrich_from_catalog(session, CATALOG); session.set_window_end(latest_sequence()); session.stop(); atomic_json(STATE, state_obj(session)); write_status(session, "Recording stopped"); return 0
    if args.action == "cancel":
        session.cancel(); atomic_json(STATE, state_obj(session)); write_status(session, "Recording cancelled"); return 0
    if args.action == "save":
        ingest_semantic_jsonl(EVENTS, session); enrich_from_catalog(session, CATALOG); session.set_window_end(latest_sequence()); session.stop(); target = args.file or (RECORDED / (session.name.replace(" ", "_") + ".architect.json")); save_blueprint(session, target); atomic_json(STATE, state_obj(session)); write_status(session, f"Saved {target.name}"); print(str(target)); return 0
    if args.action == "load":
        if not args.file: raise SystemExit("--file is required for load")
        loaded = load_blueprint(args.file); loaded.state = "loaded"; atomic_json(STATE, state_obj(loaded)); write_status(loaded, f"Loaded {args.file.name}"); return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
