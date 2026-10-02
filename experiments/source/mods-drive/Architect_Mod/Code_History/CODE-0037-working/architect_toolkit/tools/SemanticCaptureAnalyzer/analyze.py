#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from analyzer import analyze, render_markdown


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Analyze Architect bridge captures without process access.")
    parser.add_argument("--input", type=Path, default=root / "bridge")
    parser.add_argument("--output", type=Path, default=root / "bridge" / "analysis")
    args = parser.parse_args()
    report = analyze(args.input, root)
    report["generatedAtUtc"] = datetime.now(timezone.utc).isoformat()
    report["analysisCompletedForSessionId"] = report.get("sessionSummary", {}).get("currentSessionId")
    args.output.mkdir(parents=True, exist_ok=True)
    json_path = args.output / "latest_semantic_capture_report.json"
    md_path = args.output / "latest_semantic_capture_report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"sessions={len(report['sessions'])} warnings={len(report['warnings'])}")
    print(json_path.resolve())
    print(md_path.resolve())


if __name__ == "__main__":
    main()
