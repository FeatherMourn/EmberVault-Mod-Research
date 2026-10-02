"""Safely archive oversized EML logs before a controlled smoke test.

The command is intentionally dry-run by default.  Use ``--apply`` only when
Enshrouded is closed.  Archived logs are never deleted and can be restored
from the reported recovery directory.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def plan(game_dir: Path, archive_root: Path, threshold: int = 512 * 1024 * 1024) -> dict:
    game_dir = Path(game_dir).resolve()
    logs_dir = game_dir / "logs"
    candidates = []
    if logs_dir.is_dir():
        for path in sorted(logs_dir.glob("*.eml.log")):
            size = path.stat().st_size
            if size >= threshold:
                candidates.append({"source": str(path), "name": path.name, "size": size})
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = Path(archive_root).resolve() / f"{stamp}-log-rotation"
    return {"game_dir": str(game_dir), "threshold": threshold, "archive_dir": str(archive), "candidates": candidates}


def apply_rotation(spec: dict) -> dict:
    if game_is_running():
        raise RuntimeError("Enshrouded is running; close the game before rotating EML logs")
    archive = Path(spec["archive_dir"])
    archive.mkdir(parents=True, exist_ok=False)
    moved = []
    for item in spec["candidates"]:
        source = Path(item["source"])
        destination = archive / item["name"]
        shutil.move(str(source), str(destination))
        moved.append({**item, "destination": str(destination)})
    result = {**spec, "moved": moved, "applied": True}
    (archive / "rotation_manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def game_is_running() -> bool:
    """Return whether the Windows game process is present.

    A failed process query is treated as running (fail closed), so a missing
    system utility can never turn a safety check into an unsafe move.
    """
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq enshrouded.exe", "/NH"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return True
    if result.returncode != 0:
        return True
    return "enshrouded.exe" in result.stdout.lower()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game_dir", type=Path)
    parser.add_argument("--archive-root", type=Path, default=Path("H:/Enshrouded_ControlCenter_Backups"))
    parser.add_argument("--threshold-mib", type=int, default=512)
    parser.add_argument("--apply", action="store_true", help="move files; requires the game to be closed")
    args = parser.parse_args()
    spec = plan(args.game_dir, args.archive_root, args.threshold_mib * 1024 * 1024)
    if args.apply:
        try:
            spec = apply_rotation(spec)
        except RuntimeError as exc:
            parser.error(str(exc))
    else:
        spec["applied"] = False
    print(json.dumps(spec, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
