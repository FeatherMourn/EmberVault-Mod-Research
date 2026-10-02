"""Run a bounded portable launch smoke test with process-tree cleanup."""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def process_ids(image_name: str) -> set[int]:
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH", "/FI", f"IMAGENAME eq {image_name}"],
        capture_output=True, text=True, check=False,
    )
    ids: set[int] = set()
    for line in result.stdout.splitlines():
        fields = [field.strip('"') for field in line.split('","')]
        if len(fields) >= 2 and fields[0].lower() == image_name.lower():
            try:
                ids.add(int(fields[1]))
            except ValueError:
                pass
    return ids


def terminate_tree(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True, check=False)


def run(executable: Path, wait_seconds: float = 5.0) -> dict[str, object]:
    before = process_ids(executable.name)
    process = subprocess.Popen([str(executable)])
    try:
        time.sleep(wait_seconds)
        observed = process_ids(executable.name) - before
        responding = process.poll() is None
    finally:
        terminate_tree(process.pid)
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and process_ids(executable.name) - before:
        time.sleep(0.2)
    remaining = process_ids(executable.name) - before
    return {
        "schema": "control_center.portable_launch_smoke.v2",
        "executable": str(executable.resolve()),
        "launch_observed": bool(observed),
        "process_responding": responding,
        "process_tree_pids": sorted(observed),
        "clean_shutdown_observed": not remaining,
        "remaining_pids": sorted(remaining),
        "game_started": False,
        "status": "passed" if observed and responding and not remaining else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--wait", type=float, default=5.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.executable, args.wait)
    payload = json.dumps(result, indent=2, sort_keys=True)
    print(payload)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
