"""Validate a structured content definition without creating a project."""
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
    parser.add_argument("definition", type=Path)
    args = parser.parse_args()
    try:
        definition = json.loads(args.definition.read_text(encoding="utf-8-sig"))
        result = ContentCompiler.validate_definition(definition)
    except (OSError, ValueError, ContentCompilerError) as exc:
        parser.exit(1, f"validation failed: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
