"""Single supported GUI entry point for the Enshrouded Control Center.

The older GUI modules remain importable for backwards compatibility, but new
launchers should call this module so the platform has one front door.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enshrouded Mod Control Center")
    parser.add_argument(
        "--legacy",
        choices=("app", "visual_builder", "simple_editor"),
        help="open a preserved legacy tool for backwards-compatible maintenance",
    )
    parser.add_argument("--status", action="store_true", help="print a machine-readable local health report and exit")
    parser.add_argument("--game-dir", type=Path, help="Enshrouded installation to inspect with --status")
    parser.add_argument("--capabilities", action="store_true", help="print the current capability audit and exit")
    args = parser.parse_args(argv)

    if args.status:
        from core.health_report import HealthReportService
        report = HealthReportService(PROJECT_ROOT).generate(args.game_dir)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if args.capabilities:
        audit_candidates = sorted(
            (PROJECT_ROOT / "research").glob("CAPABILITY_AUDIT_*.json"),
            key=lambda path: path.stat().st_mtime if path.is_file() else 0,
            reverse=True,
        )
        audit_path = audit_candidates[0] if audit_candidates else PROJECT_ROOT / "research" / "CAPABILITY_AUDIT_20260927.json"
        from tools.verify_capability_audit import verify as verify_audit
        result = verify_audit(audit_path)
        print(audit_path.read_text(encoding="utf-8"))
        return 0 if result["valid"] else 2

    if args.legacy:
        if args.legacy == "app":
            from gui.app import main as legacy_main
        elif args.legacy == "visual_builder":
            from gui.visual_builder import main as legacy_main
        else:
            from gui.simple_editor import main as legacy_main
        legacy_main()
        return 0

    from gui.control_center import main as control_center_main

    control_center_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
