"""Dry-run-first transactional installer for a staged research probe."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.local_mods import LocalModError, LocalModService
from verify_live_loader import inspect as inspect_live


KNOWN_STALL_RESOURCE_TYPES = {
    "keen::TemplateResource",
    "keen::AnimationGraphResource2_0",
    "keen::ds::AnimationGraphResource2_0",
    "keen::VoxelWorldResource",
    "keen::VoxelWorldChunkResource",
    "keen::WaterWorldResource",
    "keen::ecs::InteractionOffer",
    "keen::ecs::InteractionQuery",
    "keen::ecs::InteractionAcceptData",
    "keen::ecs::InteractionAcceptedEvent",
    "keen::ecs::ToggleInteractionEvent",
    "keen::ecs::LootInteractionEvent",
}
PAYLOAD_MATERIALIZATION_CALLS = (
    "get_resources_by_type(", "get_resource(", "get_resource_parts(",
    "get_all_resources(",
)
ECS_EVENT_TYPES = {name for name in KNOWN_STALL_RESOURCE_TYPES if "::ecs::" in name}
EML_CAPABILITIES = {"export", "patch", "runtime", "runtime-register-dll"}


def probe_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(file.relative_to(path).as_posix().encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()


def log_baseline(game_dir: Path) -> dict:
    """Capture the latest EML log identity before a probe session starts."""
    logs = sorted((Path(game_dir) / "logs").glob("*.eml.log"),
                  key=lambda item: item.stat().st_mtime, reverse=True) if (Path(game_dir) / "logs").is_dir() else []
    if not logs:
        return {"path": None, "mtime": None, "size": None}
    latest = logs[0]
    stat = latest.stat()
    return {"path": str(latest), "mtime": stat.st_mtime, "size": stat.st_size}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("probe", type=Path)
    parser.add_argument("game_dir", type=Path)
    parser.add_argument("--storage", type=Path, default=ROOT / "profiles" / "research-probe-installer")
    parser.add_argument("--apply", "--install", dest="apply", action="store_true", help="install after validation; default is dry-run")
    parser.add_argument("--allow-research", action="store_true", help="explicitly approve applying a research-only probe")
    parser.add_argument("--replace", action="store_true", help="allow replacement of existing owned files")
    parser.add_argument("--restore", metavar="BACKUP_ID", help="restore a recorded backup instead of installing")
    parser.add_argument("--remove", action="store_true", help="remove the installed probe using its ownership record")
    parser.add_argument("--output", type=Path, help="also save the operation report as JSON")
    parser.add_argument("--expected-build", help="require the latest EML log to report this exact build")
    parser.add_argument("--cycle", type=Path, help="prepared RESEARCH_CYCLE.json to bind to this probe")
    parser.add_argument("--allow-unsafe-boundary", action="store_true",
                        help="approve a probe containing a known-stalling resource family")
    args = parser.parse_args()
    try:
        service = LocalModService(args.game_dir, args.storage)
        baseline = log_baseline(args.game_dir)
        cycle_binding = None
        if args.cycle:
            cycle_binding = json.loads(args.cycle.read_text(encoding="utf-8-sig"))
            expected_hash = cycle_binding.get("staged_probe_sha256")
            if not expected_hash:
                raise LocalModError("Research cycle does not contain a staged probe hash.")
            observed_hash = probe_hash(args.probe)
            if observed_hash != expected_hash:
                raise LocalModError("Probe does not match the research cycle integrity hash.")
        build_compatibility = None
        if args.expected_build:
            live = inspect_live(args.game_dir, expected_build=args.expected_build)
            compatibility = live.get("build_compatibility", {})
            if compatibility.get("status") != "compatible":
                raise LocalModError("Game/EML build mismatch; probe application is refused.")
            build_compatibility = compatibility
        manifest = args.probe / "mod.json"
        if not manifest.is_file():
            raise LocalModError("Staged probe must contain mod.json")
        try:
            manifest_data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise LocalModError(f"Staged probe manifest is invalid: {exc}") from exc
        entrypoint = manifest_data.get("entrypoint", "src/mod.lua")
        if not isinstance(entrypoint, str) or not entrypoint.strip() or Path(entrypoint).is_absolute() or ".." in Path(entrypoint).parts:
            raise LocalModError("Staged probe entrypoint must be a safe relative path")
        if not (args.probe / entrypoint).is_file():
            raise LocalModError(f"Staged probe entrypoint is missing: {entrypoint}")
        package = service.inspect(args.probe)
        capabilities = package.manifest.get("capabilities", [])
        if not isinstance(capabilities, list) or any(item not in EML_CAPABILITIES for item in capabilities):
            raise LocalModError(
                "Probe declares an unsupported EML capability; allowed values are: "
                + ", ".join(sorted(EML_CAPABILITIES))
            )
        source_text = "\n".join(
            file.read_text(encoding="utf-8", errors="replace")
            for file in args.probe.rglob("*")
            if file.is_file() and file.suffix.lower() in {".lua", ".json", ".md"}
        )
        unsafe_types = sorted(type_name for type_name in KNOWN_STALL_RESOURCE_TYPES
                              if type_name in source_text)
        metadata_only = (
            "get_resource_metadata_by_type(" in source_text
            and not any(call in source_text for call in PAYLOAD_MATERIALIZATION_CALLS)
            and not any(type_name in ECS_EVENT_TYPES for type_name in unsafe_types)
        )
        if unsafe_types and (not metadata_only or "keen::TemplateResource" in unsafe_types) and not args.allow_unsafe_boundary:
            if "keen::TemplateResource" in unsafe_types:
                raise LocalModError(
                    "TemplateResource is quarantined: even metadata-only access stalled on this build. "
                    "Use --allow-unsafe-boundary only for an isolated boundary experiment."
                )
            raise LocalModError(
                "Probe references known-stalling resource families: "
                + ", ".join(unsafe_types)
                + ". Use --allow-unsafe-boundary only for a controlled boundary experiment."
            )
        if args.remove:
            service.uninstall(package.identity, args.game_dir)
            result = {"mode": "remove", "identity": package.identity, "removed": True, "session_baseline": baseline}
        elif args.restore:
            result = service.restore_backup(package.identity, args.restore, args.game_dir)
            result["mode"] = "restore"
        else:
            if args.apply and package.manifest.get("feature_state") == "research-only" and not args.allow_research:
                raise LocalModError("Applying a research-only probe requires explicit --allow-research approval.")
            plan = service.preview(package, args.game_dir, allow_research=True)
            result = {"mode": "apply" if args.apply else "dry_run", "plan": plan,
                      "identity": package.identity, "feature_state": package.manifest.get("feature_state"),
                      "research_approval": bool(args.allow_research or package.manifest.get("feature_state") != "research-only"),
                      "session_baseline": baseline}
            if cycle_binding is not None:
                result["research_cycle_binding"] = {"cycle": str(args.cycle.resolve()), "probe_sha256": expected_hash}
            if build_compatibility is not None:
                result["build_compatibility"] = build_compatibility
            if args.apply:
                service.install(package, args.game_dir, replace=args.replace, allow_research=True)
                result["installed"] = True
        rendered = json.dumps(result, indent=2, sort_keys=True)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0
    except (OSError, ValueError, LocalModError) as exc:
        print(f"research probe operation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
