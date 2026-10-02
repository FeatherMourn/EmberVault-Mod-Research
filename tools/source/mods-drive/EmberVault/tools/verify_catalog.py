"""Validate a public EmberVault catalog snapshot in the content repository."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def validate(payload: dict) -> None:
    required = ("generated_at", "contract_versions", "packages", "modules", "tuning_adapters", "knowledge", "research", "content_projects")
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("Catalog schema_version must be 1")
    if set(payload) != {"schema_version", *required}:
        raise ValueError("Catalog top-level fields do not match the public contract")
    if not isinstance(payload["generated_at"], str) or not payload["generated_at"].strip():
        raise ValueError("Catalog generated_at is required")
    versions = payload["contract_versions"]
    expected_versions = ("module_manifest", "package_manifest", "research_record", "content_project", "tuning_adapter")
    if not isinstance(versions, dict) or set(versions) != set(expected_versions):
        raise ValueError("Catalog contract_versions are incomplete")
    if any(not isinstance(versions[key], int) or isinstance(versions[key], bool) or versions[key] < 1 for key in expected_versions):
        raise ValueError("Catalog contract_versions contain an invalid value")
    for name in ("packages", "modules", "tuning_adapters", "knowledge", "research", "content_projects"):
        if not isinstance(payload[name], list):
            raise ValueError(f"Catalog collection is not an array: {name}")
    for item in payload["modules"]:
        if not isinstance(item, dict) or item.get("process_mode") not in {"embedded", "separate"}:
            raise ValueError("Module records must declare embedded or separate process_mode")
    fields = {"id", "name", "version", "loader", "game_build", "supported_setting_keys", "feature_state", "process_mode", "evidence_state"}
    for item in payload["tuning_adapters"]:
        if not isinstance(item, dict) or set(item) != fields:
            raise ValueError("Tuning adapter records do not match the public contract")
        if item["process_mode"] not in {"embedded", "separate"} or not isinstance(item["supported_setting_keys"], list):
            raise ValueError("Tuning adapter records are invalid")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python tools/verify_catalog.py <catalog.json>")
        return 2
    try:
        validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"Catalog validation failed: {exc}")
        return 1
    print("Catalog validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
