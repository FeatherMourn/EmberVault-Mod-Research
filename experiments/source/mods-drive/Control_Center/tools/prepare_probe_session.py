"""Record a fresh-session boundary for a controlled EML probe."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    raw = args.log.read_bytes() if args.log.is_file() else b""
    stat = args.log.stat() if args.log.is_file() else None
    session = {
        "schema": "control_center.probe_session.v1",
        "created": datetime.now(timezone.utc).isoformat(),
        "log": str(args.log),
        "from_byte": len(raw),
        "baseline_size": stat.st_size if stat else 0,
        "baseline_mtime": stat.st_mtime if stat else None,
        "prior_log_sha256": hashlib.sha256(raw).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(session, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(session, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
