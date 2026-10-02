"""Compile a Control Center structured content definition into a project."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.content_compiler import ContentCompiler, ContentCompilerError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("definition", type=Path, help="JSON content definition")
    parser.add_argument("output", type=Path, help="Destination project directory")
    parser.add_argument("--base-dir", type=Path, default=ROOT, help="Control Center project root")
    parser.add_argument("--overwrite", action="store_true", help="Allow an existing project directory to be replaced")
    args = parser.parse_args()
    try:
        definition = json.loads(args.definition.read_text(encoding="utf-8-sig"))
        definition.setdefault("definition_dir", str(args.definition.parent))
        project = ContentCompiler(args.base_dir).compile(definition, args.output, overwrite=args.overwrite)
    except (OSError, ValueError, ContentCompilerError) as exc:
        parser.exit(1, f"compile failed: {exc}\n")
    print(json.dumps({"project": str(project), "status": "research-only"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
