"""Verify Blender probe milestones directly from a JSON-lines EML log."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_MARKERS = {
    "custom_textures_registered": "custom texture:",
    "custom_material_assigned": "assigned custom material:",
    "new_item_registered": "EBT DEBUG item registry=",
    "new_recipe_registered": "EBT DEBUG recipe registry=",
    "catalog_entry_added": "EBT DEBUG recipe UI added",
    "custom_render_model_assigned": "patched RenderModel; content=",
    "loader_attached": "Attaching runtime loader",
}


def verify(log_path: Path, probe_id: str = "stool") -> dict[str, object]:
    errors: list[str] = []
    messages: list[str] = []
    try:
        for line in Path(log_path).read_text(encoding="utf-8-sig", errors="replace").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            fields = record.get("fields", {})
            message = fields.get("message", "") if isinstance(fields, dict) else ""
            if f"[{probe_id}]" in message or (probe_id == "stool" and "[stool]" in message) or message == "Attaching runtime loader":
                messages.append(str(message))
        for name, marker in REQUIRED_MARKERS.items():
            if not any(marker in message for message in messages):
                errors.append(f"missing runtime marker: {name}")
        if any("error" in message.lower() or "panic" in message.lower() for message in messages):
            errors.append("probe log contains an error or panic marker")
    except OSError as exc:
        errors.append(str(exc))
    return {
        "schema": "control_center.blender_runtime_log_verification.v1",
        "valid": not errors,
        "probe_id": probe_id,
        "log": str(Path(log_path)),
        "message_count": len(messages),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--probe-id", default="stool")
    args = parser.parse_args()
    result = verify(args.log, args.probe_id)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
