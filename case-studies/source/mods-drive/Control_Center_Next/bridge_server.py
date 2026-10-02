"""Read-only localhost bridge for Control Center Next.

This first bridge slice exposes health and capability information only. It does
not install mods, edit saves, write game files, or attach to a running game.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


CAPABILITIES = {
    "schema": "control_center.bridge_capabilities.v1",
    "mode": "read-only",
    "operations": {
        "health": "verified",
        "capabilities": "verified",
        "mod_install": "disabled",
        "save_write": "disabled",
        "trainer_attach": "disabled",
    },
}


def modules(control_center_dir: str | None) -> list[dict]:
    root = Path(control_center_dir).expanduser() if control_center_dir else None
    if not root or not (root / "modules").is_dir():
        return []
    result = []
    for manifest_path in sorted((root / "modules").glob("*/module.json")):
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            result.append({
                "id": data.get("id", manifest_path.parent.name),
                "name": data.get("name", manifest_path.parent.name),
                "version": data.get("version", "unknown"),
                "feature_state": data.get("feature_state", "unclassified"),
                "enabled": bool(data.get("enabled", True)),
            })
        except (OSError, json.JSONDecodeError):
            result.append({"id": manifest_path.parent.name, "name": manifest_path.parent.name, "version": "invalid", "feature_state": "invalid", "enabled": False})
    return result


def profile_state(control_center_dir: str | None) -> dict:
    root = Path(control_center_dir).expanduser() if control_center_dir else None
    result = {"schema": "control_center.bridge_profile.v1", "mode": "read-only", "active_profile": None, "enabled_modules": {}, "module_settings": {}, "live_config_modules": {}}
    if not root:
        return result
    for name, key in (("profiles/active_profile.json", "active_profile"), ("runtime/live_config.json", "live_config")):
        path = root / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if key == "active_profile":
                result["active_profile"] = data.get("name") or data.get("profile") or "active_profile.json"
                result["enabled_modules"] = data.get("enabled_modules", {})
                result["module_settings"] = data.get("module_settings", {})
            else:
                result["live_config_modules"] = data.get("modules", {})
        except (OSError, json.JSONDecodeError):
            result["profile_read_warning"] = f"Could not read {name}"
    return result


def diagnostics(game_dir: str | None, control_center_dir: str | None = None) -> dict:
    game = Path(game_dir).expanduser() if game_dir else None
    root = Path(control_center_dir).expanduser() if control_center_dir else None
    return {
        "schema": "control_center.bridge_diagnostics.v1",
        "mode": "read-only",
        "game_folder_detected": bool(game and game.is_dir()),
        "mods_directory_detected": bool(game and (game / "mods").is_dir()),
        "control_center_detected": bool(root and root.is_dir()),
        "active_profile_detected": bool(root and (root / "profiles" / "active_profile.json").is_file()),
        "live_config_detected": bool(root and (root / "runtime" / "live_config.json").is_file()),
        "module_count": len(modules(control_center_dir)),
        "writes_enabled": False,
    }


def health(game_dir: str | None, control_center_dir: str | None = None) -> dict:
    path = Path(game_dir).expanduser() if game_dir else None
    root = Path(control_center_dir).expanduser() if control_center_dir else None
    module_count = len(list((root / "modules").glob("*/module.json"))) if root and (root / "modules").is_dir() else 0
    return {
        "schema": "control_center.bridge_health.v1",
        "bridge": "ready",
        "mode": "read-only",
        "game_folder": str(path) if path else None,
        "game_folder_detected": bool(path and path.is_dir()),
        "writes_enabled": False,
        "running_game_detection": "not_connected",
        "module_count": module_count,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "ControlCenterNextBridge/0.1"

    def _send(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        game_dir = query.get("game_dir", [self.server.game_dir])[0]
        if parsed.path == "/api/health":
            self._send(health(game_dir, self.server.control_center_dir))
        elif parsed.path == "/api/capabilities":
            self._send(CAPABILITIES)
        elif parsed.path == "/api/modules":
            self._send({"schema": "control_center.bridge_modules.v1", "mode": "read-only", "modules": modules(self.server.control_center_dir)})
        elif parsed.path == "/api/profile":
            self._send(profile_state(self.server.control_center_dir))
        elif parsed.path == "/api/diagnostics":
            self._send(diagnostics(game_dir, self.server.control_center_dir))
        else:
            self._send({"error": "not_found", "read_only": True}, 404)

    def do_POST(self) -> None:  # noqa: N802 - explicitly reject writes
        self._send({"error": "read_only_bridge", "message": "This bridge does not accept write operations."}, 405)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[bridge] {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the read-only Control Center Next bridge")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4175)
    parser.add_argument("--game-dir", default=None)
    parser.add_argument("--control-center-dir", default=None)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.game_dir = args.game_dir
    server.control_center_dir = args.control_center_dir
    print(f"Control Center Next bridge listening on http://{args.host}:{args.port}")
    print("Mode: read-only; live writes and trainer attachment are disabled")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping bridge")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
