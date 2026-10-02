"""Install or remove the generated read-only KFC research probe."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "research" / "probes" / "kfc_read_probe_1076226"
GAME = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded")
MOD_ID = "control_center_kfc_read_probe"
OWNER = ".control-center-research-probe.json"


def install() -> None:
    if not (PROBE / "mod.json").is_file() or not (PROBE / "src" / "mod.lua").is_file():
        raise SystemExit("The probe has not been generated yet. Run the probe builder first.")
    target = GAME / "mods" / MOD_ID
    target.parent.mkdir(parents=True, exist_ok=True)
    owner = target / OWNER
    if target.exists() and not owner.is_file():
        raise SystemExit(f"Refusing to overwrite an unowned folder: {target}")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(PROBE, target)
    manifest = {"owner": MOD_ID, "source": str(PROBE), "mode": "read_only"}
    (target / OWNER).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    mode = json.loads((target / "mod.json").read_text(encoding="utf-8")).get("mode", "research")
    print(f"Installed {mode} KFC research probe to:\n{target}")
    print("Launch Enshrouded once, then close it and provide the latest EML log.")


def remove() -> None:
    target = GAME / "mods" / MOD_ID
    owner = target / OWNER
    if not owner.is_file():
        raise SystemExit("The research probe is not installed, or its ownership marker is missing.")
    shutil.rmtree(target)
    print(f"Removed research probe:\n{target}")


parser = argparse.ArgumentParser()
parser.add_argument("action", choices=("install", "remove"))
parser.add_argument("--probe", type=Path, default=PROBE)
parser.add_argument("--id", default=MOD_ID)
parser.add_argument("--owner", default=OWNER)
args = parser.parse_args()
if args.probe != PROBE:
    PROBE = args.probe
if args.id != MOD_ID:
    MOD_ID = args.id
if args.owner != OWNER:
    OWNER = args.owner
(install if args.action == "install" else remove)()
