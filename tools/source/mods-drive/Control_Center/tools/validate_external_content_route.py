"""Run a guarded EML CLI patch and verify the resulting KFC content graph.

This is intentionally restricted to disposable game copies. It never targets
the configured live installation and does not claim client rendering.
"""
from __future__ import annotations

import argparse
import json
import sys
import subprocess
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.tools.verify_kfc_fixture import verify


LIVE_GAME = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded").resolve()


def _discover_recipe_guid(root: Path, recipe_id: int) -> str | None:
    for path in (root / "RecipeRegistryResource").glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        for recipe in payload.get("recipes", []):
            if recipe.get("recipeId", {}).get("value") == recipe_id:
                guid = recipe.get("recipeGuid")
                if isinstance(guid, str) and guid:
                    return guid
    return None


def run(args: argparse.Namespace) -> dict:
    target = Path(args.game_dir).resolve()
    if target == LIVE_GAME:
        raise SystemExit("Refusing to patch the live Enshrouded installation.")
    if not (target / "enshrouded.exe").is_file() or not (target / "enshrouded.kfc").is_file():
        raise SystemExit(f"Target is not a complete Enshrouded copy: {target}")
    emm = Path(args.emm).resolve()
    if not emm.is_file():
        raise SystemExit(f"EML CLI was not found: {emm}")
    installed_by_us = False
    probe_target = target / "mods" / (Path(args.probe).name if args.probe else "")
    try:
        if args.probe:
            if not (Path(args.probe) / "mod.json").is_file():
                raise SystemExit(f"Probe is missing mod.json: {args.probe}")
            if not probe_target.exists():
                installer = Path(__file__).resolve().parent / "install_research_probe.py"
                install = subprocess.run(
                    [sys.executable, str(installer), str(Path(args.probe).resolve()), str(target),
                     "--apply", "--allow-research", "--expected-build", args.expected_build],
                    capture_output=True, text=True, check=False,
                )
                if install.returncode != 0:
                    raise SystemExit(f"Research probe installation failed.\n{install.stdout}\n{install.stderr}")
                installed_by_us = True
        command = [str(emm), "run", "-g", str(target), "--patch"]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise SystemExit(f"EML CLI patch failed with exit code {completed.returncode}.\n{completed.stdout}\n{completed.stderr}")
        with tempfile.TemporaryDirectory(prefix="cc-postpatch-") as temp:
            unpack = Path(temp)
            parser = Path(args.parser).resolve()
            unpacked = subprocess.run(
                [str(parser), "unpack", "--game-directory", str(target), "--output", str(unpack),
                 "--filter", "tkeen::ItemInfo,tkeen::RecipeRegistryResource,tkeen::ItemRegistryResource,tkeen::ItemKnowledgeResource,tkeen::FbUiBundle"],
                capture_output=True, text=True, check=False,
            )
            if unpacked.returncode != 0:
                raise SystemExit(f"KFC unpack failed with exit code {unpacked.returncode}.\n{unpacked.stdout}\n{unpacked.stderr}")
            recipe_guid = args.recipe_guid
            if recipe_guid == "auto":
                recipe_guid = _discover_recipe_guid(unpack, args.recipe_id)
                if not recipe_guid:
                    raise SystemExit("Unable to discover a recipe GUID for the requested recipe ID.")
            report = verify(unpack, args.item_id, args.recipe_id, args.debug_name, recipe_guid)
            report["discovered_recipe_guid"] = recipe_guid
    finally:
        if installed_by_us:
            installer = Path(__file__).resolve().parent / "install_research_probe.py"
            subprocess.run([sys.executable, str(installer), str(Path(args.probe).resolve()), str(target), "--remove"], capture_output=True, text=True, check=False)
    report.update({
        "schema": "control_center.external_content_route_validation.v1",
        "target": str(target),
        "cli": str(emm),
        "patch_stdout_tail": completed.stdout[-4000:],
        "unpack_stdout_tail": unpacked.stdout[-1000:],
        "client_rendering_verified": False,
    })
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(report, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_dir")
    parser.add_argument("--emm", default=r"H:\enshroudedresearch\external\kfc-parser-source\target\release\emm.exe")
    parser.add_argument("--parser", default=r"H:\enshroudedresearch\external\kfc-parser-source\target\release\kfc-parser.exe")
    parser.add_argument("--item-id", type=int, required=True)
    parser.add_argument("--recipe-id", type=int, required=True)
    parser.add_argument("--debug-name", required=True)
    parser.add_argument("--recipe-guid", help="Expected GUID, or 'auto' to discover the generated recipe GUID")
    parser.add_argument("--probe", help="Optional research probe to install transactionally for the patch run")
    parser.add_argument("--expected-build", default="1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z")
    parser.add_argument("--output")
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
