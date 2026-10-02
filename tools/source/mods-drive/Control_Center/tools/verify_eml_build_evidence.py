"""Validate current EML source-build evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(path: Path) -> dict:
    errors = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "control_center.eml_build_evidence_verification.v1", "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.eml_build_verification.v1": errors.append("unsupported schema")
    if not data.get("target_build"): errors.append("target_build is required")
    if data.get("mod_loader_lua") != "passed": errors.append("mod-loader-lua did not pass")
    if data.get("dinput8_proxy") != "passed": errors.append("dinput8-proxy did not pass")
    if data.get("errors") != 0: errors.append("build errors must be zero")
    if data.get("status") != "passed": errors.append("status must be passed")
    return {"schema": "control_center.eml_build_evidence_verification.v1", "valid": not errors, "path": str(path), "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    result = validate(parser.parse_args().evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
