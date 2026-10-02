"""Copy a verified observe-only EML research mod; never auto-install to the game."""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from .catalog import CatalogError

PROBE_ROOT = Path(__file__).resolve().parent.parent / "probe_mod" / "CC2_Research_Probe"


def export_probe(destination: Path) -> dict:
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise CatalogError("refusing to overwrite an existing probe package: " + str(destination))
    if not (PROBE_ROOT / "mod.json").is_file() or not (PROBE_ROOT / "src/mod.lua").is_file():
        raise CatalogError("packaged observe-only EML probe is missing")
    manifest = json.loads((PROBE_ROOT / "mod.json").read_text(encoding="utf-8"))
    if manifest.get("capabilities") != ["patch", "export"]:
        raise CatalogError("probe requires an unsupported capability")
    if "mods" in {p.lower() for p in destination.parts}:
        raise CatalogError("never deploy directly to a mods directory; use a staging folder")
    # All exported files are static. No generated hooks, patching or game install.
    shutil.copytree(PROBE_ROOT, destination)
    return {"status": "OBSERVE_ONLY_MANUAL_INSTALL", "destination": str(destination),
            "id": manifest["id"], "files": ["mod.json", "src/mod.lua"],
            "game_modified": False, "legacy_modified": False}
