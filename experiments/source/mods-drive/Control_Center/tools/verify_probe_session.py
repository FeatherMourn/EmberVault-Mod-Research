"""Verify fresh, marker-based evidence for one controlled probe session."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.probe_evidence import inspect_probe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("marker")
    parser.add_argument("--baseline-mtime", type=float)
    parser.add_argument("--require-fresh", action="store_true",
                        help="refuse to classify evidence unless --baseline-mtime is supplied")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = inspect_probe(args.log, args.marker, args.baseline_mtime, args.require_fresh)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["status"] in {
        "registry_indexed", "clone_registered", "metadata_lookup_verified",
        "metadata_call_completed", "metadata_api_exposed", "metadata_enumeration_verified",
        "actor_sequence_identity_clone_registered",
        "actor_sequence_attack_attachment_tested",
        "journal_schema_inventory_verified",
        "knowledge_schema_inventory_verified",
        "journal_identity_clone_registered",
        "journal_registry_clone_insert_verified",
        "journal_live_attachment_runtime_verified",
        "standalone_quest_resource_created",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
