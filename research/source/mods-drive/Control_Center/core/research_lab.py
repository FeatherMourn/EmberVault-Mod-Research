"""Deterministic KFC research probe generation and result cataloging."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class ResearchProbeService:
    """Wrap the existing probe tools in a stable service API.

    Generation is deterministic for the same candidate input and build. Result
    catalog entries are append/update operations and never modify game files.
    """

    CATALOG_SCHEMA = "control_center.research_catalog.v1"

    @staticmethod
    def controlled_validation_preflight(game_dir: Path, probe_dir: Path, expected_build: str | None = None) -> dict[str, Any]:
        """Check that a controlled probe can be run without touching an active session."""
        game_dir = Path(game_dir).resolve(); probe_dir = Path(probe_dir).resolve()
        issues: list[str] = []
        if not (game_dir / "Enshrouded.exe").is_file():
            issues.append("Enshrouded.exe is missing from the selected game folder.")
        if not (game_dir / "logs").is_dir():
            issues.append("The game logs directory is missing.")
        if not (probe_dir / "mod.json").is_file() or not (probe_dir / "src" / "mod.lua").is_file():
            issues.append("The probe is incomplete; mod.json and src/mod.lua are required.")
        running = True
        try:
            running = "enshrouded.exe" in subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq Enshrouded.exe"], text=True, stderr=subprocess.DEVNULL
            ).lower()
        except (OSError, subprocess.SubprocessError):
            issues.append("Could not establish game process state; refusing to call the session safe.")
        manifest: dict[str, Any] = {}
        if (probe_dir / "mod.json").is_file():
            try:
                manifest = json.loads((probe_dir / "mod.json").read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                issues.append("The probe manifest is not valid JSON.")
        probe_build = str(manifest.get("research_build", "")) if isinstance(manifest, dict) else ""
        if expected_build and probe_build and probe_build != str(expected_build):
            issues.append(f"Probe build {probe_build} does not match expected build {expected_build}.")
        dependencies = manifest.get("dependencies", []) if isinstance(manifest, dict) else []
        if isinstance(dependencies, dict):
            dependencies = [dependencies]
        if not isinstance(dependencies, list):
            issues.append("Probe dependencies must be a list.")
            dependencies = []
        for dependency in dependencies:
            dependency_id = dependency if isinstance(dependency, str) else dependency.get("id") if isinstance(dependency, dict) else None
            if not dependency_id:
                issues.append("Probe contains a dependency without an id.")
                continue
            dependency_manifest = game_dir / "mods" / str(dependency_id) / "mod.json"
            if not dependency_manifest.is_file():
                issues.append(f"Required dependency is not installed: {dependency_id}.")
                continue
            required_version = dependency.get("version") if isinstance(dependency, dict) else None
            if required_version:
                try:
                    dependency_version = str(json.loads(dependency_manifest.read_text(encoding="utf-8-sig")).get("version", ""))
                    from .local_mods import LocalModService
                    if not LocalModService._version_satisfies(dependency_version, str(required_version)):
                        issues.append(f"Required dependency {dependency_id} has incompatible version {dependency_version}; needs {required_version}.")
                except (OSError, ValueError, TypeError):
                    issues.append(f"Required dependency manifest is invalid: {dependency_id}.")
        if running:
            issues.append("Enshrouded is currently running; close it before controlled validation.")
        return {"ready": not issues, "game_dir": str(game_dir), "probe_dir": str(probe_dir), "expected_build": expected_build, "probe_build": probe_build or None, "issues": issues}

    @staticmethod
    def generate(candidates_path: Path, output_dir: Path, build: str | None = None) -> dict[str, Any]:
        from tools.build_kfc_research_probe import build_lua, load_candidates

        candidates_path = Path(candidates_path)
        output_dir = Path(output_dir)
        source = json.loads(candidates_path.read_text(encoding="utf-8"))
        candidates = load_candidates(candidates_path)
        selected_build = str(build if build is not None else source.get("build", "unknown"))
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "src").mkdir(parents=True, exist_ok=True)

        manifest = {
            "id": "control_center_kfc_read_probe",
            "name": "Control Center KFC Read Probe",
            "version": "0.1.0",
            "author": "Enshrouded Control Center",
            "capabilities": ["patch"],
            "dependencies": [{"id": "bed_clone_injection_1076226", "version": ">=0.1.0"}],
            "entrypoint": "src/mod.lua",
            "research_build": selected_build,
            "mode": "read_only",
            "candidate_count": len(candidates),
        }
        probe_manifest = {"schema": "control_center.research_probe.v1", "build": selected_build, "candidates": candidates}
        (output_dir / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (output_dir / "src" / "mod.lua").write_text(build_lua(candidates, selected_build), encoding="utf-8")
        (output_dir / "probe_manifest.json").write_text(json.dumps(probe_manifest, indent=2) + "\n", encoding="utf-8")
        return {
            "output": str(output_dir),
            "build": selected_build,
            "candidate_count": len(candidates),
            "probe_hash": hashlib.sha256((output_dir / "src" / "mod.lua").read_bytes()).hexdigest(),
        }

    @staticmethod
    def generate_localization(
        output_dir: Path,
        entries: dict[str, dict[str, str]],
        build: str = "unknown",
        collection_probe: bool = False,
    ) -> dict[str, Any]:
        """Generate a deterministic localization probe.

        Tag registration is the safe default. Collection/content mutation is
        intentionally opt-in because the live EML boundary has not yet been
        proven safe on every build.
        """
        output_dir = Path(output_dir)
        source = ROOT / "research" / "runtime" / "kfc_localization_registry.lua"
        if not source.is_file():
            raise FileNotFoundError(f"Localization helper is missing: {source}")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "src").mkdir(parents=True, exist_ok=True)
        normalized = {
            str(key): {str(locale): str(text) for locale, text in sorted(values.items())}
            for key, values in sorted(entries.items())
        }
        new_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"control-center/localization/{build}"))
        lines = [
            "-- Deterministic Control Center localization probe.",
            "local registry = require('kfc_localization_registry')",
            "local entries = {",
        ]
        for key, values in normalized.items():
            lines.append(f"  [{json.dumps(key, ensure_ascii=False)}] = {{")
            for locale, text in values.items():
                lines.append(f"    [{json.dumps(locale, ensure_ascii=False)}] = {json.dumps(text, ensure_ascii=False)},")
            lines.append("  },")
        lines.extend([
            "}",
            "local tag_ok, tag = pcall(function() return registry.register_tag('Control Center Demo', 'Control Center localization probe') end)",
            "print('[CC-LOCALIZATION] TAG|ok=' .. tostring(tag_ok) .. '|result=' .. tostring(tag_ok and tag and tag.guid or tag))",
        ])
        if collection_probe:
            lines.extend([
                f"local ok, result = pcall(function() return registry.register(entries, {json.dumps(new_guid)}, 'En_Us') end)",
                "print('[CC-LOCALIZATION] REGISTER|ok=' .. tostring(ok) .. '|result=' .. tostring(ok and result and result.guid or result))",
            ])
        else:
            lines.append("print('[CC-LOCALIZATION] COLLECTION|skipped=safe_default_requires_explicit_opt_in')")
        lines.extend([
            "print('[CC-LOCALIZATION] WARNING|UI_consumption_requires_controlled_validation')",
            "return {}",
            "",
        ])
        (output_dir / "src" / "mod.lua").write_text("\n".join(lines), encoding="utf-8")
        shutil.copy2(source, output_dir / "src" / "kfc_localization_registry.lua")
        manifest = {
            "schema": "control_center.localization_probe.v1",
            "id": "control_center_localization_probe",
            "name": "Control Center Localization Probe",
            "version": "0.1.0",
            "author": "Enshrouded Control Center",
            "feature_state": "research-only",
            "mode": "runtime_research",
            "capabilities": ["patch"],
            "dependencies": [],
            "entrypoint": "src/mod.lua",
            "research_build": str(build),
            "new_collection_guid": new_guid,
            "entry_count": len(normalized),
            "collection_probe": collection_probe,
            "safety_note": "Collection mutation is opt-in; tag-only is the default probe mode.",
        }
        (output_dir / "mod.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        probe_hash = hashlib.sha256((output_dir / "src" / "mod.lua").read_bytes()).hexdigest()
        return {"output": str(output_dir), "build": str(build), "probe_hash": probe_hash, "new_collection_guid": new_guid}

    @staticmethod
    def generate_localized_bed(output_dir: Path, build: str = "1076226") -> dict[str, Any]:
        """Generate a non-colliding bed fixture using a newly-created LocaTag."""
        source = ROOT / "research" / "probes" / "bed_clone_injection_1076226"
        output_dir = Path(output_dir)
        if output_dir.exists() and any(output_dir.iterdir()):
            raise FileExistsError(f"Refusing to overwrite non-empty probe: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "src").mkdir(parents=True, exist_ok=True)
        source_lua = """-- Controlled label-consumption probe for the already-registered bed fixture.
local PREFIX = '[CC-LOCALIZED-BED] '
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
local function resources(type_name)
    local ok, result = pcall(function() return game.assets.get_resources_by_type(type_name) or {} end)
    if not ok then log('ERROR', type_name .. '|' .. tostring(result)); return {} end
    return result
end
local target
for _, item in pairs(resources('keen::ItemInfo')) do
    if item and item.data and item.data.itemId and item.data.itemId.value == 3987654321 then target = item; break end
end
if not target then log('STOP', 'verified_bed_clone_not_found'); return {} end
local tag_ok, tag = pcall(function()
    return require('kfc_localization_registry').register_tag('Control Center Localized Bed', 'A runtime localization UI test bed')
end)
log('LOCALIZATION_TAG', 'ok=' .. tostring(tag_ok) .. '|result=' .. tostring(tag_ok and tag and tag.guid or tag))
if tag_ok and tag then
    target.data.name = tag.guid
    target.data.description = tag.guid
    log('DISPLAY_FIELDS', 'name=' .. tostring(target.data.name) .. '|description=' .. tostring(target.data.description))
else
    log('STOP', 'localization_tag_failed')
end
return {}
"""
        (output_dir / "src" / "mod.lua").write_text(source_lua, encoding="utf-8")
        shutil.copy2(ROOT / "research" / "runtime" / "kfc_localization_registry.lua", output_dir / "src" / "kfc_localization_registry.lua")
        manifest = {
            "id": "localized_bed_probe_1076226",
            "name": "Control Center Localized Bed Probe",
            "version": "0.1.0",
            "author": "Enshrouded Control Center",
            "capabilities": ["patch"],
            "dependencies": [{"id": "bed_clone_injection_1076226", "version": ">=0.1.0"}],
            "entrypoint": "src/mod.lua",
            "feature_state": "research-only",
            "research_build": str(build),
            "mode": "controlled_content_injection",
            "content_class": "furniture_bed",
            "item_id": 3987654321,
            "recipe_id": 3987654322,
            "notes": "Uses a newly-created keen::LocaTag for visual UI validation.",
        }
        (output_dir / "mod.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        readme = source / "README.md"
        if readme.is_file():
            (output_dir / "README.md").write_text(readme.read_text(encoding="utf-8") + "\nThis variant uses a new runtime keen::LocaTag.\n", encoding="utf-8")
        return {"output": str(output_dir), "build": str(build), "probe_hash": hashlib.sha256((output_dir / "src" / "mod.lua").read_bytes()).hexdigest(), "item_id": 3987654321, "recipe_id": 3987654322}

    @staticmethod
    def generate_combined_localized_bed(output_dir: Path, build: str = "1076226") -> dict[str, Any]:
        """Generate an atomic bed clone where the LocaTag exists before ItemInfo."""
        source = ROOT / "research" / "probes" / "bed_clone_injection_1076226"
        output_dir = Path(output_dir)
        if output_dir.exists() and any(output_dir.iterdir()):
            raise FileExistsError(f"Refusing to overwrite non-empty probe: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "src").mkdir(parents=True, exist_ok=True)
        source_lua = (source / "src" / "mod.lua").read_text(encoding="utf-8")
        source_lua = source_lua.replace("[CC-BED-CLONE]", "[CC-COMBINED-LOCALIZED-BED]")
        source_lua = source_lua.replace("local DONOR_ID = 2940001508", "local DONOR_ID = 2940001508\nlocal DONOR_RECIPE_ID = 3531872774\nlocal DONOR_GUID = '01474f79-6b5a-4bcd-999d-7e9339fda91c'")
        source_lua = source_lua.replace("3987654321", "3987654333").replace("3987654322", "3987654334")
        source_lua = source_lua.replace("CC_Custom_Bed_001", "CC_Combined_Localized_Bed")
        source_lua = source_lua.replace("-- Use an existing localized bed label until custom localization payloads are\n-- supported; the item identity and recipe remain independent.", "-- The custom tag is paired with a matching locale-collection entry.\n-- The item identity and recipe remain independent of the donor IDs.")
        source_lua = source_lua.replace("local ok_item, clone_or_error = pcall(function()", """local localization = require('kfc_localization_registry')
local LOCALIZATION_KEY = 'Control Center Combined Localized Bed'
local tag_ok, tag = pcall(function()
    return localization.register_tag(LOCALIZATION_KEY, 'Atomic localization test bed')
end)
log('LOCALIZATION_TAG', 'ok=' .. tostring(tag_ok) .. '|result=' .. tostring(tag_ok and tag and tag.guid or tag))
local collection_ok, collection = pcall(function()
    return localization.register({[LOCALIZATION_KEY] = {En_Us = 'Control Center Combined Localized Bed'}}, '9d0a2a4f-3b7b-5e4c-9aa2-6b8e5f77c1d0', 'En_Us')
end)
log('LOCALIZATION_COLLECTION', 'ok=' .. tostring(collection_ok) .. '|result=' .. tostring(collection_ok and collection and collection.guid or collection))
local ok_item, clone_or_error = pcall(function()""")
        source_lua = source_lua.replace("clone.data.name = '5ea4b496-9073-4c41-9c68-9c9a990b7378'", """if tag_ok and tag then
    -- Build 1076226 does not resolve a same-startup custom LocaTag through
    -- ItemInfo.name. Keep the donor name for the stable rendered fixture.
    clone.data.name = donor.data.name
    clone.data.caption = donor.data.caption
    clone.data.description = donor.data.description
else
    clone.data.name = '5ea4b496-9073-4c41-9c68-9c9a990b7378'
end""")
        source_lua = source_lua.replace("new_recipe.debugName = 'CC_Combined_Localized_Bed_Recipe'", """new_recipe.recipeGuid = 'c4d7e9b2-3f58-6a01-9d24-8b7c5e0f3162'
new_recipe.debugName = 'CC_Combined_Localized_Bed_Recipe'
new_recipe.recipeName = donor_recipe.recipeName
for _, requirement in ipairs({new_recipe.knowledgeRequirement, new_recipe.completionRequirementQuery}) do
    if requirement and requirement.type == 'Extern' and requirement.knowledgeOrQueryId then
        requirement.knowledgeOrQueryId.value = 0
        requirement.compareValue = 0
    end
end""")
        old_search = """local donor_recipe
for _, recipe in pairs(recipe_registry.data.recipes) do
    if recipe.output then
        for _, output in pairs(recipe.output) do
            if output.item and output.item.value == DONOR_ID then donor_recipe = recipe; break end
        end
    end
    if donor_recipe then break end
end"""
        new_search = """local donor_recipe
local function recipe_matches(recipe)
    if recipe and recipe.recipeId and recipe.recipeId.value == DONOR_RECIPE_ID then return true end
    for _, output in pairs(recipe and recipe.output or {}) do
        if output and output.item and output.item.value == DONOR_ID then return true end
        if output and output.itemRef and output.itemRef.value == DONOR_ID then return true end
        if output and output.itemRef and tostring(output.itemRef) == DONOR_GUID then return true end
    end
    return false
end
-- Keep typed requirement fields intact until a schema-safe empty
-- representation is identified; nil can cross the Lua/Rust boundary as an
-- invalid resource value.
for _, candidate_type in ipairs({'keen::RecipeRegistryResource', 'keen::ds::RecipeRegistryResource'}) do
    for _, candidate_registry in pairs(resources(candidate_type)) do
        for _, recipe in pairs(candidate_registry.data and candidate_registry.data.recipes or {}) do
            if recipe_matches(recipe) then donor_recipe = recipe; recipe_registry = candidate_registry; break end
        end
        if donor_recipe then break end
    end
    if donor_recipe then break end
end"""
        source_lua = source_lua.replace(old_search, new_search)
        (output_dir / "src" / "mod.lua").write_text(source_lua, encoding="utf-8")
        shutil.copy2(ROOT / "research" / "runtime" / "kfc_localization_registry.lua", output_dir / "src" / "kfc_localization_registry.lua")
        manifest = {
            "id": "combined_localized_bed_probe_1076226",
            "name": "Control Center Combined Localized Bed Probe",
            "version": "0.1.0",
            "author": "Enshrouded Control Center",
            "capabilities": ["patch"],
            "dependencies": [],
            "entrypoint": "src/mod.lua",
            "feature_state": "research-only",
            "research_build": str(build),
            "mode": "controlled_content_injection",
            "content_class": "furniture_bed",
            "item_id": 3987654333,
            "recipe_id": 3987654334,
            "notes": "Creates keen::LocaTag before the cloned ItemInfo for UI consumption testing.",
        }
        (output_dir / "mod.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {"output": str(output_dir), "build": str(build), "probe_hash": hashlib.sha256((output_dir / "src" / "mod.lua").read_bytes()).hexdigest(), "item_id": 3987654333, "recipe_id": 3987654334}

    @classmethod
    def catalog_result(cls, log_path: Path, catalog_path: Path) -> dict[str, Any]:
        from tools.parse_kfc_research_log import parse

        log_path = Path(log_path)
        catalog_path = Path(catalog_path)
        result = parse(log_path)
        catalog: dict[str, Any] = {"schema": cls.CATALOG_SCHEMA, "entries": []}
        if catalog_path.exists():
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            if catalog.get("schema") != cls.CATALOG_SCHEMA:
                raise ValueError("unsupported research catalog schema")

        raw = log_path.read_bytes()
        entry = dict(result)
        entry["log_sha256"] = hashlib.sha256(raw).hexdigest()
        entry["log_name"] = log_path.name
        entries = [item for item in catalog.get("entries", []) if item.get("log_sha256") != entry["log_sha256"]]
        entries.append(entry)
        entries.sort(key=lambda item: (str(item.get("build", "unknown")), str(item.get("log_name", ""))))
        catalog["entries"] = entries
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
        return entry

    @classmethod
    def catalog_localization_result(cls, log_path: Path, catalog_path: Path) -> dict[str, Any]:
        """Catalog live localization registration markers without claiming UI success."""
        log_path = Path(log_path)
        events: list[dict[str, Any]] = []
        build = "unknown"
        for raw in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            fields = event.get("fields", {})
            message = str(fields.get("message", ""))
            if message.startswith("[CC-LOCALIZATION] "):
                events.append({"message": message, "timestamp": event.get("timestamp")})
            if message == "Type registry loaded successfully" and fields.get("version"):
                build = str(fields["version"]).split("|", 1)[0]
        registrations = [e["message"] for e in events if " REGISTER|" in e["message"]]
        successful = [message for message in registrations if "ok=true" in message.lower()]
        failures = [message for message in registrations if "ok=false" in message.lower()]
        entry = {
            "schema": "control_center.localization_probe_result.v1",
            "marker_prefix": "[CC-LOCALIZATION] ",
            "build": build,
            "log": str(log_path),
            "log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
            "registration_attempts": len(registrations),
            "successful_registrations": len(successful),
            "failed_registrations": len(failures),
            "registration_messages": registrations,
            "ui_consumption_verified": False,
            "promotion_ready": False,
            "promotion_blocker": "game-facing UI consumption has not been visually verified",
            "status": "runtime_registration_verified" if successful else ("marker_not_found" if not events else "review_required"),
        }
        catalog_path = Path(catalog_path)
        catalog = {"schema": "control_center.localization_catalog.v1", "entries": []}
        if catalog_path.exists():
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            if catalog.get("schema") != "control_center.localization_catalog.v1":
                raise ValueError("unsupported localization catalog schema")
        catalog["entries"] = [item for item in catalog.get("entries", []) if item.get("log_sha256") != entry["log_sha256"]]
        catalog["entries"].append(entry)
        catalog["entries"].sort(key=lambda item: (str(item.get("build", "unknown")), str(item.get("log", ""))))
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return entry

    @classmethod
    def catalog_content_fixture_result(cls, log_path: Path, catalog_path: Path, marker: str = "[CC-COMBINED-LOCALIZED-BED]", visual_evidence: Path | None = None, visual_claim: str | None = None, visual_verified: bool = False) -> dict[str, Any]:
        """Catalog the latest run of a structured runtime content fixture."""
        log_path = Path(log_path)
        raw = log_path.read_text(encoding="utf-8", errors="replace")
        events: list[dict[str, Any]] = []
        build = "unknown"
        for line in raw.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            fields = event.get("fields", {})
            message = str(fields.get("message", ""))
            if message == "Type registry loaded successfully" and fields.get("version"):
                build = str(fields["version"]).split("|", 1)[0]
            if message.startswith(marker + " "):
                events.append({"message": message[len(marker) + 1:], "timestamp": event.get("timestamp")})
        if not events:
            raise ValueError(f"No fixture markers found for {marker}")
        # A localized fixture begins with localization registration.
        # Non-localized legacy fixtures use DISPLAY_FIELDS as their boundary.
        boundary = "LOCALIZATION_TAG|" if any(event["message"].startswith("LOCALIZATION_TAG|") for event in events) else "DISPLAY_FIELDS|"
        starts = [index for index, event in enumerate(events)
                  if event["message"].startswith(boundary)]
        latest = events[starts[-1]:] if starts else events
        messages = [str(event["message"]) for event in latest]
        registered = next((message for message in messages if message.startswith("REGISTERED|")), "")
        fields: dict[str, str] = {}
        for part in registered.split("|", 1)[1].split("|") if "|" in registered else []:
            if "=" in part:
                key, value = part.split("=", 1)
                fields[key] = value
        runtime_verified = any(message.startswith("REGISTERED|") for message in messages) and not any(message.startswith("STOP|") for message in messages)
        generated_item = next((message.split("|", 1)[1] for message in messages if message.startswith("CLONED_ITEM|")), None)
        generated_recipe = next((message.split("|", 1)[1] for message in messages if message.startswith("REGISTERED_RECIPE|")), None)
        generated_ui = next((message.split("|", 1)[1].lower() == "true" for message in messages if message.startswith("UI_REGISTERED|")), None)
        recorded_events = latest
        if generated_item is not None:
            runtime_verified = generated_recipe is not None and not any(message.startswith("BLOCKED|") for message in messages)
            # Generated donor scans can contain thousands of repetitive
            # candidate markers. Preserve the decisive evidence while keeping
            # the catalog compact and readable.
            recorded_events = [event for event in latest if not event["message"].startswith("DONOR_CANDIDATE|")]
        entry = {
            "schema": "control_center.content_fixture_result.v1",
            "fixture": marker.strip("[]").lower().replace("-", "_"),
            "build": build,
            "log": str(log_path),
            "log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
            "events": recorded_events,
            "item_id": fields.get("itemId"),
            "recipe_id": fields.get("recipeId"),
            "ui_visual_verified": bool(visual_evidence and Path(visual_evidence).is_file()),
            "status": "end_to_end_visual_verified" if runtime_verified and visual_verified else ("runtime_registration_verified" if runtime_verified else "review_required"),
            "visual_verification_claimed": bool(visual_verified),
        }
        if generated_item is not None:
            entry["generated_item_id"] = generated_item
            entry["generated_recipe_id"] = generated_recipe
            entry["ui_registration_reported"] = generated_ui
        if visual_evidence and Path(visual_evidence).is_file():
            entry["visual_evidence"] = str(Path(visual_evidence))
            entry["visual_claim"] = visual_claim or "in-game visual confirmation"
        catalog_path = Path(catalog_path)
        catalog = {"schema": "control_center.content_fixture_catalog.v1", "entries": []}
        if catalog_path.exists():
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            if catalog.get("schema") != "control_center.content_fixture_catalog.v1":
                raise ValueError("unsupported content fixture catalog schema")
        catalog["entries"] = [item for item in catalog.get("entries", []) if item.get("log_sha256") != entry["log_sha256"] or item.get("fixture") != entry["fixture"]]
        catalog["entries"].append(entry)
        catalog["entries"].sort(key=lambda item: (str(item.get("build", "unknown")), str(item.get("fixture", ""))))
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return entry

    @classmethod
    def catalog_icon_import_result(cls, log_path: Path, catalog_path: Path, prefix: str = "[CC-COMBINED-LOCALIZED-BED] ") -> dict[str, Any]:
        """Catalog the machine-checkable PNG-to-UiTexture evidence chain."""
        from research.tools.verify_icon_import_log import verify

        log_path = Path(log_path)
        evidence = verify(log_path, prefix)
        entry = {
            "schema": "control_center.icon_import_catalog.v1",
            "log": str(log_path),
            "log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
            "prefix": prefix,
            "evidence": evidence["evidence"],
            "missing": evidence["missing"],
            "status": "runtime_icon_import_verified" if evidence["valid"] else "review_required",
            "rendering_verified": False,
        }
        catalog_path = Path(catalog_path)
        catalog = {"schema": "control_center.icon_import_catalog.v1", "entries": []}
        if catalog_path.exists():
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            if catalog.get("schema") != "control_center.icon_import_catalog.v1":
                raise ValueError("unsupported icon import catalog schema")
        catalog["entries"] = [item for item in catalog.get("entries", []) if item.get("log_sha256") != entry["log_sha256"]]
        catalog["entries"].append(entry)
        catalog["entries"].sort(key=lambda item: str(item.get("log", "")))
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return entry

    @classmethod
    def load_catalog(cls, catalog_path: Path) -> dict[str, Any]:
        payload = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
        if payload.get("schema") != cls.CATALOG_SCHEMA:
            raise ValueError("unsupported research catalog schema")
        return payload
