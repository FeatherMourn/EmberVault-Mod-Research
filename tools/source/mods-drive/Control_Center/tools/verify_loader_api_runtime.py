"""Capture or validate fresh-session EML Lua API runtime evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "control_center.eml_api_runtime_evidence.v1"
REGISTRY_EVENT = "Type registry loaded successfully"
API_EVENT = "Lua API initialized"


def validate_report(data: dict[str, Any], expected_build: str, expected_api: str) -> list[str]:
    errors: list[str] = []
    if data.get("schema") != SCHEMA:
        errors.append("unsupported evidence schema")
    if data.get("status") != "passed":
        errors.append("runtime evidence status is not passed")
    if data.get("game_build") != expected_build:
        errors.append("game build does not match the requested build")
    if data.get("loader_api_version") != expected_api:
        errors.append("loader API version does not match the requested version")
    if data.get("api_event_after_registry") is not True:
        errors.append("API event is not proven after the current registry event")
    if data.get("runtime_loader_attached") is not True:
        errors.append("runtime loader attachment was not observed")
    if data.get("current_session_errors") != []:
        errors.append("current session contains errors")
    if not data.get("log_sha256"):
        errors.append("log hash is missing")
    if not data.get("loader_sha256"):
        errors.append("loader binary hash is missing")
    return errors


def capture(log_path: Path, baseline_bytes: int, expected_build: str,
            expected_api: str, loader_path: Path) -> dict[str, Any]:
    log_path = Path(log_path).resolve()
    loader_path = Path(loader_path).resolve()
    raw = log_path.read_bytes()
    if baseline_bytes < 0 or baseline_bytes > len(raw):
        raise ValueError("baseline_bytes must be within the current log size")
    fresh = raw[baseline_bytes:]
    records: list[dict[str, Any]] = []
    for line in fresh.decode("utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            records.append(value)

    registry_indexes = [i for i, row in enumerate(records)
                        if (row.get("fields") or {}).get("message") == REGISTRY_EVENT]
    latest_registry_index = registry_indexes[-1] if registry_indexes else -1
    latest_registry = records[latest_registry_index] if latest_registry_index >= 0 else {}
    registry_version = (latest_registry.get("fields") or {}).get("version")
    api_indexes = [i for i, row in enumerate(records)
                   if (row.get("fields") or {}).get("message") == API_EVENT]
    api_index = api_indexes[-1] if api_indexes else -1
    api_record = records[api_index] if api_index >= 0 else {}
    api_version = (api_record.get("fields") or {}).get("api_version")
    current_records = records[latest_registry_index:] if latest_registry_index >= 0 else []
    current_errors = []
    for row in current_records:
        if str(row.get("level", "")).lower() in {"error", "fatal", "panic"}:
            fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
            current_errors.append(str(fields.get("message") or fields.get("report") or row))
    messages = [(row.get("fields") or {}).get("message") for row in current_records]
    runtime_attached = "Attaching runtime loader" in messages
    loader_hash = hashlib.sha256(loader_path.read_bytes()).hexdigest() if loader_path.is_file() else None
    data = {
        "schema": SCHEMA,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "log_path": str(log_path),
        "baseline_bytes": baseline_bytes,
        "fresh_bytes": len(fresh),
        "log_sha256": hashlib.sha256(raw).hexdigest(),
        "game_build": registry_version,
        "loader_api_version": api_version,
        "api_event_after_registry": latest_registry_index >= 0 and api_index > latest_registry_index,
        "runtime_loader_attached": runtime_attached,
        "mod_execution_observed": any(
            (row.get("fields") or {}).get("message") == "Running mod" for row in current_records
        ),
        "current_session_errors": current_errors,
        "loader_path": str(loader_path),
        "loader_sha256": loader_hash,
    }
    errors = validate_report(data, expected_build, expected_api)
    data["status"] = "passed" if not errors else "failed"
    data["validation_errors"] = errors
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, nargs="?")
    parser.add_argument("--baseline-bytes", type=int)
    parser.add_argument("--expected-build", required=True)
    parser.add_argument("--expected-api", required=True)
    parser.add_argument("--loader", type=Path)
    parser.add_argument("--evidence", type=Path, help="validate an existing evidence JSON instead of capturing")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.evidence:
        try:
            data = json.loads(args.evidence.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
            return 1
        errors = validate_report(data, args.expected_build, args.expected_api)
        result = {"schema": "control_center.eml_api_runtime_evidence_verification.v1",
                  "valid": not errors, "errors": errors, "path": str(args.evidence)}
    else:
        if args.log is None or args.baseline_bytes is None or args.loader is None:
            parser.error("capture mode requires log, --baseline-bytes, and --loader")
        data = capture(args.log, args.baseline_bytes, args.expected_build, args.expected_api, args.loader)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.output.with_suffix(args.output.suffix + ".tmp")
            temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            temporary.replace(args.output)
        result = data
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("valid", result.get("status") == "passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
