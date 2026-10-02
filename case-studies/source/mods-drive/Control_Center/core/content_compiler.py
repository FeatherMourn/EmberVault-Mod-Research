"""Compile structured content definitions into research-gated EML projects."""
from __future__ import annotations

import json
import hashlib
import re
import copy
from pathlib import Path
from typing import Any

from .content_identity import ContentIdentityService
from .content_project import ContentProjectGenerator, ContentProjectError
from .content_validation import ContentProjectValidator
from .lua_assistant import LuaAssistant, LuaAssistantError
from .recipe_ui_adapter import RecipeUiAdapter, RecipeUiPlanError
from .asset_substitution import AssetSubstitutionPlanner, AssetSubstitutionError
from .capability_status import CapabilityStatus
from .template_graph import TemplateGraphPlanner, TemplateGraphError


class ContentCompilerError(RuntimeError):
    pass


class ContentCompiler:
    """Compile definitions without deploying or modifying the game install."""

    def __init__(self, base_dir: Path, identity_registry_path: Path | None = None):
        self.base_dir = Path(base_dir)
        self.identity = ContentIdentityService(identity_registry_path or (self.base_dir / "profiles" / "content-identities.json"))
        self.projects = ContentProjectGenerator(self.base_dir, self.identity.registry_path)
        self.validator = ContentProjectValidator()

    @staticmethod
    def validate_definition(definition: dict[str, Any]) -> dict[str, Any]:
        """Validate author input without creating files or allocating identity."""
        normalized = ContentCompiler._normalize_visual_variant(definition)
        ContentCompiler._validate_definition(normalized)
        customization = normalized.get("customization") or {}
        research_fields = sorted(
            key for key in customization
            if key not in {"identity", "localization", "recipe", "layout"}
        )
        mechanics = customization.get("mechanics")
        policy = "preserve"
        if isinstance(mechanics, dict):
            policy = str(mechanics.get("preservation_policy", "preserve")).strip().lower()
        field_matrix = {}
        evidence_gates = {
            "identity": "same-build donor-preservation and lookup evidence",
            "localization": "fresh-session in-game label readback",
            "recipe": "same-build recipe registration and craftability evidence",
            "layout": "same-build visible category/slot evidence",
            "icon": "same-build rendered icon evidence",
            "color": "same-build rendered color/material evidence",
            "material": "same-build placed-object material evidence",
            "texture": "same-build placed-object texture evidence",
            "model": "same-build placed-object model evidence",
            "visual_transform": "same-build placed-object scale/offset evidence",
            "mechanics": "same-build behavior and donor-preservation evidence",
        }
        verified = {"identity", "localization", "recipe", "layout"}
        for field in sorted(customization):
            field_matrix[field] = {
                "status": "verified" if field in verified else "research-only",
                "runtime_action": "apply" if field in verified else "hold_for_research",
                "required_evidence": evidence_gates.get(field, "field-specific same-build runtime evidence"),
            }
        return {
            "schema": "control_center.content_definition_validation.v1",
            "valid": True,
            "content_id": str(normalized.get("id", normalized.get("name", ""))),
            "research_only_fields": research_fields,
            "mechanics_preservation_policy": policy,
            "customization_matrix": field_matrix,
            "deployment": "compiler-only; no live game mutation",
        }

    def compile(self, definition: dict[str, Any], destination: Path, overwrite: bool = False) -> Path:
        definition = self._normalize_visual_variant(definition)
        self._validate_definition(definition)
        namespace = self._slug(definition["namespace"])
        name = str(definition["name"]).strip()
        project_id = self._slug(definition.get("id", name))
        destination = Path(destination)
        existed = destination.exists()
        identity_path = self.identity.registry_path
        old_identity = identity_path.read_bytes() if identity_path.is_file() else None
        try:
            project = self.projects.create(destination, namespace, name, str(definition["author"]), project_id,
                                           str(definition.get("version", "0.1.0")), overwrite)
            icon_source = definition.get("icon")
            if icon_source:
                icon_path = Path(str(icon_source)).expanduser()
                if not icon_path.is_absolute():
                    icon_path = (Path(definition.get("definition_dir", ".")) / icon_path).resolve()
                icon_entry = self.projects.import_icon(project, icon_path, definition.get("icon_slug") or project_id)
                if definition.get("icon_resource_type") and definition.get("icon_field"):
                    from .asset_service import AssetService
                    AssetService().register_reference(
                        project,
                        icon_entry["path"],
                        definition["icon_resource_type"],
                        definition["icon_field"],
                        definition.get("icon_resource_id"),
                    )
            declared_assets = definition.get("assets", [])
            if declared_assets:
                from .asset_service import AssetError, AssetService
                for asset in declared_assets:
                    try:
                        source = Path(str(asset["source"])).expanduser()
                        if not source.is_absolute():
                            source = (Path(definition.get("definition_dir", ".")) / source).resolve()
                        AssetService().import_file(source, project, str(asset["kind"]), asset.get("name"),
                                                    provenance=asset.get("provenance"))
                    except (KeyError, AssetError, TypeError, ValueError) as exc:
                        raise ContentCompilerError(f"Asset import failed: {exc}") from exc
            manifest_path = project / "mod.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            content_path = project / "content" / "content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            identity = self.identity.identity(namespace, project_id)
            entry = {
                "id": f"{namespace}:{identity.slug}",
                "numeric_id": identity.numeric_id,
                "guid": identity.guid,
                "name": name,
                "content_class": str(definition.get("content_class", "item")),
                "resource_type": str(definition.get("resource_type", "keen::ItemInfo")),
                "properties": definition.get("properties", {}),
                "customization": self._customization_contract(definition.get("customization", {})),
            }
            entry["metadata_policy"] = self._metadata_policy(entry["resource_type"])
            runtime_definition = dict(definition)
            if definition.get("registry_probe"):
                try:
                    LuaAssistant().generate_registry_clone_probe(
                        str(definition.get("donor_guid", "")),
                        int(definition.get("new_item_id", 0)),
                        project_id,
                        project / "src" / "mod.lua",
                    )
                except (LuaAssistantError, TypeError, ValueError) as exc:
                    raise ContentCompilerError(f"Registry probe generation failed: {exc}") from exc
                manifest["runtime_generation"] = {
                    "generator": "control_center.lua_assistant.v3",
                    "entrypoint": "src/mod.lua",
                    "registry_probe": True,
                }
                capabilities = manifest.setdefault("capabilities", [])
                if "patch" not in capabilities:
                    capabilities.append("patch")
            elif definition.get("visual_probe"):
                try:
                    dependencies = definition.get("asset_dependencies", [])
                    LuaAssistant().generate_visual_substitution_probe(
                        str(definition.get("visual_resource_type", "keen::RenderModel")),
                        dependencies,
                        project_id,
                        project / "src" / "mod.lua",
                    )
                except (LuaAssistantError, TypeError, ValueError) as exc:
                    raise ContentCompilerError(f"Visual probe generation failed: {exc}") from exc
                manifest["runtime_generation"] = {
                    "generator": "control_center.lua_assistant.v3",
                    "entrypoint": "src/mod.lua",
                    "visual_probe": True,
                    "read_only": True,
                }
                capabilities = manifest.setdefault("capabilities", [])
                if "patch" not in capabilities:
                    capabilities.append("patch")
            elif definition.get("visual_field_probe"):
                try:
                    LuaAssistant().generate_visual_field_probe(
                        str(definition.get("donor_guid", "")), project_id,
                        project / "src" / "mod.lua",
                    )
                except (LuaAssistantError, TypeError, ValueError) as exc:
                    raise ContentCompilerError(f"Visual field probe generation failed: {exc}") from exc
                manifest["runtime_generation"] = {
                    "generator": "control_center.lua_assistant.v3",
                    "entrypoint": "src/mod.lua",
                    "visual_field_probe": True,
                    "read_only": True,
                }
                capabilities = manifest.setdefault("capabilities", [])
                if "patch" not in capabilities:
                    capabilities.append("patch")
            elif definition.get("resource_graph_probe"):
                try:
                    LuaAssistant().generate_resource_graph_probe(
                        definition.get("resource_guids", []),
                        definition.get("resource_types", []), project_id,
                        project / "src" / "mod.lua",
                    )
                except (LuaAssistantError, TypeError, ValueError) as exc:
                    raise ContentCompilerError(f"Resource graph probe generation failed: {exc}") from exc
                manifest["runtime_generation"] = {
                    "generator": "control_center.lua_assistant.v3",
                    "entrypoint": "src/mod.lua",
                    "resource_graph_probe": True,
                    "read_only": True,
                }
                capabilities = manifest.setdefault("capabilities", [])
                if "patch" not in capabilities:
                    capabilities.append("patch")
            elif definition.get("single_resource_probe"):
                try:
                    LuaAssistant().generate_single_resource_probe(
                        str(definition.get("resource_type", "")),
                        str(definition.get("resource_guid", "")), project_id,
                        project / "src" / "mod.lua",
                    )
                except (LuaAssistantError, TypeError, ValueError) as exc:
                    raise ContentCompilerError(f"Single resource probe generation failed: {exc}") from exc
                manifest["runtime_generation"] = {
                    "generator": "control_center.lua_assistant.v3",
                    "entrypoint": "src/mod.lua",
                    "single_resource_probe": True,
                    "read_only": True,
                }
                capabilities = manifest.setdefault("capabilities", [])
                if "patch" not in capabilities:
                    capabilities.append("patch")
            elif definition.get("item_visual_reference_probe"):
                try:
                    LuaAssistant().generate_item_visual_reference_probe(
                        str(definition.get("donor_guid", "")), int(definition.get("new_item_id", 0)),
                        str(definition.get("replacement_model_guid", "")), project_id,
                        project / "src" / "mod.lua",
                    )
                except (LuaAssistantError, TypeError, ValueError) as exc:
                    raise ContentCompilerError(f"Item visual probe generation failed: {exc}") from exc
                manifest["runtime_generation"] = {
                    "generator": "control_center.lua_assistant.v3",
                    "entrypoint": "src/mod.lua",
                    "item_visual_reference_probe": True,
                    "clone_only": True,
                }
                capabilities = manifest.setdefault("capabilities", [])
                if "patch" not in capabilities:
                    capabilities.append("patch")
            elif definition.get("localization_probe"):
                try:
                    LuaAssistant().generate_localization_probe(
                        str(definition.get("localization_guid", "")), project_id,
                        project / "src" / "mod.lua",
                    )
                except (LuaAssistantError, TypeError, ValueError) as exc:
                    raise ContentCompilerError(f"Localization probe generation failed: {exc}") from exc
                manifest["runtime_generation"] = {
                    "generator": "control_center.lua_assistant.v3",
                    "entrypoint": "src/mod.lua",
                    "localization_probe": True,
                    "read_only": False,
                    "research_only": True,
                }
                capabilities = manifest.setdefault("capabilities", [])
                if "patch" not in capabilities:
                    capabilities.append("patch")
            elif definition.get("minimal_probe"):
                try:
                    LuaAssistant().generate_minimal_clone_probe(
                        str(definition.get("donor_guid", "")),
                        int(definition.get("new_item_id", 0)),
                        project_id,
                        project / "src" / "mod.lua",
                    )
                except (LuaAssistantError, TypeError, ValueError) as exc:
                    raise ContentCompilerError(f"Minimal probe generation failed: {exc}") from exc
                manifest["runtime_generation"] = {
                    "generator": "control_center.lua_assistant.v3",
                    "entrypoint": "src/mod.lua",
                    "minimal_probe": True,
                }
                capabilities = manifest.setdefault("capabilities", [])
                if "patch" not in capabilities:
                    capabilities.append("patch")
            elif all(isinstance(definition.get(key), int) for key in ("donor_id", "new_item_id")):
                try:
                    LuaAssistant().generate(runtime_definition, project / "src" / "mod.lua")
                except LuaAssistantError as exc:
                    raise ContentCompilerError(f"Runtime Lua generation failed: {exc}") from exc
                manifest["runtime_generation"] = {
                    "generator": "control_center.lua_assistant.v2",
                    "entrypoint": "src/mod.lua",
                    "recipe_linkage": all(isinstance(definition.get(key), int)
                                           for key in ("donor_recipe_id", "new_recipe_id")),
                }
                capabilities = manifest.setdefault("capabilities", [])
                if "patch" not in capabilities:
                    capabilities.append("patch")
            content["entries"] = [entry]
            content_path.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            manifest["content"] = [{"id": entry["id"], "numeric_id": entry["numeric_id"],
                                    "guid": entry["guid"], "resource_type": entry["resource_type"],
                                    "path": "content/content.json"}]
            manifest["content_class"] = entry["content_class"]
            manifest["feature_state"] = CapabilityStatus.RESEARCH_ONLY.value
            manifest["customization"] = entry["customization"]
            if all(isinstance(definition.get(key), int)
                   for key in ("donor_recipe_id", "new_recipe_id", "new_item_id")):
                try:
                    recipe_plan = RecipeUiAdapter().plan(
                        int(definition["donor_recipe_id"]),
                        int(definition["new_recipe_id"]),
                        int(definition["new_item_id"]),
                    )
                    manifest["recipe_ui_plan"] = RecipeUiAdapter.manifest_metadata(recipe_plan)
                except RecipeUiPlanError as exc:
                    raise ContentCompilerError(f"Recipe/UI planning failed: {exc}") from exc
            recipe_customization = (definition.get("customization") or {}).get("recipe")
            if recipe_customization is not None and not isinstance(recipe_customization, dict):
                raise ContentCompilerError("customization.recipe must be an object.")
            if isinstance(recipe_customization, dict):
                allowed_recipe_edits = {
                    "ingredients", "input", "output", "station", "craftTime",
                    "craftingDuration", "workshopId", "workshopGuid", "requiredProps",
                    "amount", "debugName", "knowledgeRequirement",
                }
                unknown_recipe_edits = sorted(set(recipe_customization) - allowed_recipe_edits)
                if unknown_recipe_edits:
                    raise ContentCompilerError(
                        "Unsupported recipe customization fields: " + ", ".join(unknown_recipe_edits)
                    )
                self._validate_recipe_customization(recipe_customization)
                manifest["recipe_customization_plan"] = {
                    "schema": "control_center.recipe_customization_plan.v1",
                    "state": "research-only",
                    "runtime_action": "hold_for_research",
                    "requested_edits": copy.deepcopy(recipe_customization),
                    "donor_preservation": "deep_copy_before_edit",
                    "required_evidence": "same-build recipe registration and craftability evidence",
                }
            mechanics_customization = (definition.get("customization") or {}).get("mechanics")
            if isinstance(mechanics_customization, dict):
                manifest["mechanics_customization_plan"] = {
                    "schema": "control_center.mechanics_customization_plan.v1",
                    "state": "research-only",
                    "runtime_action": "hold_for_research",
                    "requested_edits": copy.deepcopy(mechanics_customization),
                    "preservation_policy": str(mechanics_customization.get("preservation_policy", "preserve")).lower(),
                    "donor_preservation": "deep_copy_before_edit",
                    "required_evidence": "same-build behavior and donor-isolation evidence",
                }
            customization_input = definition.get("customization") or {}
            substitutions = list(definition.get("asset_substitutions") or [])
            for customization_key, field_name in (("model", "visualModel"), ("material", "material"), ("texture", "texture"), ("icon", "iconImage")):
                value = customization_input.get(customization_key)
                if isinstance(value, dict) and value.get("resource_guid"):
                    if not any(item.get("field") == field_name for item in substitutions if isinstance(item, dict)):
                        substitutions.append({
                            "field": field_name,
                            "resource_guid": value["resource_guid"],
                            **({"resource_type": value["resource_type"]} if value.get("resource_type") else {}),
                        })
            color_adjustments = customization_input.get("color_adjustments", [])
            if not color_adjustments and isinstance(customization_input.get("color"), dict):
                tint = customization_input["color"].get("tint")
                if tint:
                    color_adjustments = [{"target": customization_input["color"].get("target", "material"), "color": tint}]
            if "asset_substitutions" in definition or substitutions or color_adjustments:
                try:
                    asset_plan = AssetSubstitutionPlanner().plan(
                        int(definition.get("donor_id", 0)),
                        int(definition.get("new_item_id", 0)),
                        substitutions,
                        color_adjustments=color_adjustments,
                    )
                    asset_metadata = AssetSubstitutionPlanner.manifest_metadata(asset_plan)
                    manifest["asset_substitution_plan"] = asset_metadata
                    manifest["asset_dependencies"] = asset_metadata["resource_dependencies"]
                    if any("asset" in substitution for substitution in asset_plan.substitutions):
                        from .asset_service import AssetService
                        for substitution in asset_plan.substitutions:
                            asset_path = substitution.get("asset")
                            if not asset_path:
                                continue
                            AssetService().register_reference(
                                project,
                                asset_path,
                                substitution.get("resource_type", "keen::ItemInfo"),
                                substitution["field"],
                                substitution["resource_guid"],
                            )
                except (AssetSubstitutionError, TypeError, ValueError) as exc:
                    raise ContentCompilerError(f"Asset substitution planning failed: {exc}") from exc
            customization = definition.get("customization") or {}
            visual_keys = ("icon", "color", "color_adjustments", "item_color_combination", "material", "texture", "model", "visual_transform")
            requested_visual = {key: copy.deepcopy(customization[key]) for key in visual_keys if key in customization}
            if requested_visual:
                manifest["visual_variant_plan"] = {
                    "schema": "control_center.visual_variant_plan.v1",
                    "state": "research-only",
                    "runtime_action": "hold_for_research",
                    "donor_item_id": definition.get("donor_id"),
                    "replacement_resources": copy.deepcopy(substitutions),
                    "requested_visual_changes": requested_visual,
                    "catalog_preview_policy": (customization.get("visual_preview_policy") or {}).get("catalog", "donor-fallback"),
                    "placement_preview_policy": (customization.get("visual_preview_policy") or {}).get("placement", "donor-fallback"),
                    "fallback": "preserve_donor_visual_and_mechanics",
                    "compatibility": {
                        "game_build": definition.get("compatible_game_build"),
                        "required_resource_types": sorted({
                            str(item.get("resource_type"))
                            for item in substitutions
                            if isinstance(item, dict) and item.get("resource_type")
                        }),
                    },
                    "promotion_evidence": ["runtime_verified", "catalog_visual_verified", "placed_visual_verified", "rollback_verified"],
                }
            if definition.get("template_model_source"):
                try:
                    source = Path(str(definition["template_model_source"])).expanduser()
                    if not source.is_absolute():
                        source = (Path(definition.get("definition_dir", ".")) / source).resolve()
                    template_plan = TemplateGraphPlanner().plan(
                        source, str(definition["template_model_replacement_guid"]),
                        definition.get("template_model_component_index")
                    )
                    candidate = project / "content" / "resources" / "templates" / f"{project_id}_model_candidate.json"
                    TemplateGraphPlanner().write_candidate(template_plan, candidate)
                    preserved, unexpected = TemplateGraphPlanner.verify_candidate(template_plan, candidate)
                    if not preserved:
                        raise ContentCompilerError(
                            "Template graph candidate changed unplanned paths: " + ", ".join(unexpected)
                        )
                    manifest["template_graph_plan"] = TemplateGraphPlanner.manifest_metadata(template_plan)
                    manifest["template_graph_plan"]["candidate_path"] = candidate.relative_to(project).as_posix()
                    manifest["template_graph_plan"]["candidate_sha256"] = hashlib.sha256(candidate.read_bytes()).hexdigest()
                    manifest["template_graph_plan"]["component_inventory"] = list(
                        TemplateGraphPlanner.inventory(source)
                    )
                except (TemplateGraphError, TypeError, ValueError) as exc:
                    raise ContentCompilerError(f"Template graph planning failed: {exc}") from exc
            manifest["compiler"] = {"schema": "control_center.compiler.v1", "definition_id": project_id}
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            localization = project / "content" / "localization.json"
            localization_data = json.loads(localization.read_text(encoding="utf-8"))
            localization_entries = definition.get("localization", {})
            # Keep the Lua payload synchronized with the validated catalog. It
            # is a payload for research/runtime adapters, not proof that the
            # current game build consumes newly-created tags.
            catalog = self.projects.localization.build(namespace, localization_entries)
            if not catalog.valid:
                raise ContentCompilerError(
                    "Compiled localization failed validation: " + "; ".join(issue.message for issue in catalog.issues)
                )
            # Persist the canonical namespaced keys, rather than the author's
            # shorthand input keys. This keeps the JSON artifact, Lua payload,
            # and saved-payload validator aligned.
            localization_data["namespace"] = catalog.namespace
            localization_data["default_language"] = catalog.default_language
            localization_data["entries"] = catalog.entries
            localization.write_text(json.dumps(localization_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            # Read back the exact artifact that will ship. This catches
            # serialization/schema drift before the project is packaged.
            self.projects.localization.load(localization)
            self.projects.localization.save_lua_payload(catalog, project / "src" / "localization_payload.lua")
            # Rebuild integrity metadata after compiler-owned files change.
            self.projects.packages.create_manifest(project, project_id, str(definition.get("version", "0.1.0")))
            report = self.validator.validate(project)
            if not report.valid:
                raise ContentCompilerError("Compiled project failed validation: " + "; ".join(issue.message for issue in report.issues))
            return project
        except (OSError, ValueError, ContentProjectError) as exc:
            if not existed and destination.exists():
                import shutil
                try:
                    shutil.rmtree(destination)
                except OSError:
                    pass
            try:
                if old_identity is None:
                    if identity_path.exists(): identity_path.unlink()
                else:
                    identity_path.write_bytes(old_identity)
                self.identity._data = self.identity._load()
            except OSError:
                pass
            if isinstance(exc, ContentCompilerError):
                raise
            raise ContentCompilerError(str(exc)) from exc

    @staticmethod
    def _validate_recipe_customization(recipe: dict) -> None:
        """Reject malformed recipe edits before they can reach a loader probe."""
        for field in ("ingredients", "input", "output"):
            value = recipe.get(field)
            if value is None:
                continue
            if not isinstance(value, list):
                raise ContentCompilerError(f"Recipe customization field '{field}' must be a list.")
            for index, entry in enumerate(value):
                if not isinstance(entry, dict):
                    raise ContentCompilerError(f"Recipe customization {field}[{index}] must be an object.")
                item = entry.get("item", entry.get("itemId"))
                if item is not None and (not isinstance(item, int) or item <= 0):
                    raise ContentCompilerError(f"Recipe customization {field}[{index}].item must be a positive integer.")
                amount = entry.get("amount", entry.get("count"))
                if amount is not None and (not isinstance(amount, int) or amount <= 0):
                    raise ContentCompilerError(f"Recipe customization {field}[{index}].count must be a positive integer.")
        for field in ("craftTime", "craftingDuration"):
            value = recipe.get(field)
            if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0):
                raise ContentCompilerError(f"Recipe customization field '{field}' must be a non-negative number.")
        for field in ("workshopId", "amount"):
            value = recipe.get(field)
            if value is not None and (not isinstance(value, int) or value <= 0):
                raise ContentCompilerError(f"Recipe customization field '{field}' must be a positive integer.")
        for field in ("requiredProps", "knowledgeRequirement"):
            value = recipe.get(field)
            if value is not None and not isinstance(value, (list, dict)):
                raise ContentCompilerError(f"Recipe customization field '{field}' must be an object or list.")

    @staticmethod
    def _normalize_visual_variant(definition: dict[str, Any]) -> dict[str, Any]:
        """Translate the reusable visual-variant template into compiler fields."""
        if not isinstance(definition, dict):
            return definition
        variant = definition.get("visual_variant")
        if variant is None:
            return definition
        if not isinstance(variant, dict):
            raise ContentCompilerError("visual_variant must be an object.")
        normalized = copy.deepcopy(definition)
        customization = dict(normalized.get("customization") or {})
        substitutions = list(normalized.get("asset_substitutions") or [])
        model_guid = variant.get("replacement_model_guid")
        if model_guid:
            substitutions.append({"field": "visualModel", "resource_guid": model_guid,
                                  "resource_type": "keen::RenderModel"})
        for key, field in (("materials", "material"), ("textures", "texture")):
            values = variant.get(key) or []
            if not isinstance(values, list):
                raise ContentCompilerError(f"visual_variant.{key} must be an array.")
            for value in values:
                if not isinstance(value, dict) or not str(value.get("resource_guid", "")).strip():
                    raise ContentCompilerError(f"visual_variant.{key} entries require resource_guid.")
                substitutions.append({"field": field, "resource_guid": value["resource_guid"],
                                      **({"resource_type": value["resource_type"]} if value.get("resource_type") else {})})
        if variant.get("color_adjustments"):
            customization["color_adjustments"] = copy.deepcopy(variant["color_adjustments"])
        if isinstance(variant.get("item_color_combination"), dict):
            customization["item_color_combination"] = copy.deepcopy(variant["item_color_combination"])
        if "scale" in variant or "offset" in variant:
            customization["visual_transform"] = {
                "scale": copy.deepcopy(variant.get("scale", [1.0, 1.0, 1.0])),
                "offset": copy.deepcopy(variant.get("offset", [0.0, 0.0, 0.0])),
            }
        if "catalog_preview" in variant or "placement_preview" in variant:
            customization["visual_preview_policy"] = {
                "catalog": variant.get("catalog_preview", "donor-fallback"),
                "placement": variant.get("placement_preview", "donor-fallback"),
            }
        if substitutions:
            normalized["asset_substitutions"] = substitutions
        if customization:
            normalized["customization"] = customization
        return normalized

    @staticmethod
    def _validate_definition(definition: dict[str, Any]) -> None:
        if not isinstance(definition, dict):
            raise ContentCompilerError("Content definition must be an object.")
        for key in ("namespace", "name", "author"):
            if not str(definition.get(key, "")).strip():
                raise ContentCompilerError(f"Content definition requires {key}.")
        if "localization" in definition and not isinstance(definition["localization"], dict):
            raise ContentCompilerError("localization must be an object.")
        if "properties" in definition and not isinstance(definition["properties"], dict):
            raise ContentCompilerError("properties must be an object.")
        if "asset_substitutions" in definition and not isinstance(definition["asset_substitutions"], list):
            raise ContentCompilerError("asset_substitutions must be an array.")
        if "visual_variant" in definition and not isinstance(definition["visual_variant"], dict):
            raise ContentCompilerError("visual_variant must be an object.")
        if "assets" in definition:
            if not isinstance(definition["assets"], list):
                raise ContentCompilerError("assets must be an array.")
            for asset in definition["assets"]:
                if not isinstance(asset, dict) or not str(asset.get("source", "")).strip() or not str(asset.get("kind", "")).strip():
                    raise ContentCompilerError("Each asset requires source and kind.")
                provenance = asset.get("provenance")
                if provenance is not None:
                    if not isinstance(provenance, dict):
                        raise ContentCompilerError("asset provenance must be an object.")
                    allowed_provenance = {"source", "license", "author", "attribution", "url", "notes"}
                    unknown_provenance = sorted(set(provenance) - allowed_provenance)
                    if unknown_provenance:
                        raise ContentCompilerError(
                            "Unsupported asset provenance fields: " + ", ".join(unknown_provenance)
                        )
                    if any(not isinstance(value, str) or not value.strip() for value in provenance.values()):
                        raise ContentCompilerError("Asset provenance values must be non-empty strings.")
        if "template_model_source" in definition:
            if not isinstance(definition["template_model_source"], str) or not definition["template_model_source"].strip():
                raise ContentCompilerError("template_model_source must be a path string.")
            if not isinstance(definition.get("template_model_replacement_guid"), str) or not definition["template_model_replacement_guid"].strip():
                raise ContentCompilerError("template_model_replacement_guid is required.")
            if "template_model_component_index" in definition and (
                    not isinstance(definition["template_model_component_index"], int)
                    or definition["template_model_component_index"] < 0):
                raise ContentCompilerError("template_model_component_index must be a non-negative integer.")
        if definition.get("visual_probe"):
            if not isinstance(definition.get("asset_dependencies"), list) or not definition["asset_dependencies"]:
                raise ContentCompilerError("visual_probe requires a non-empty asset_dependencies array.")
            if any(not isinstance(value, str) or not value.strip() for value in definition["asset_dependencies"]):
                raise ContentCompilerError("visual_probe asset_dependencies must contain non-empty strings.")
        if definition.get("visual_field_probe") and not str(definition.get("donor_guid", "")).strip():
            raise ContentCompilerError("visual_field_probe requires donor_guid.")
        if definition.get("resource_graph_probe"):
            for key in ("resource_guids", "resource_types"):
                if not isinstance(definition.get(key), list) or not definition[key]:
                    raise ContentCompilerError(f"resource_graph_probe requires {key}.")
        if definition.get("single_resource_probe"):
            if not str(definition.get("resource_type", "")).strip() or not str(definition.get("resource_guid", "")).strip():
                raise ContentCompilerError("single_resource_probe requires resource_type and resource_guid.")
        if definition.get("item_visual_reference_probe"):
            if not isinstance(definition.get("donor_guid"), str) or not definition["donor_guid"].strip():
                raise ContentCompilerError("item_visual_reference_probe requires donor_guid.")
            if not isinstance(definition.get("new_item_id"), int) or definition["new_item_id"] <= 0:
                raise ContentCompilerError("item_visual_reference_probe requires new_item_id.")
            if not isinstance(definition.get("replacement_model_guid"), str) or not definition["replacement_model_guid"].strip():
                raise ContentCompilerError("item_visual_reference_probe requires replacement_model_guid.")
        if definition.get("localization_probe"):
            if not isinstance(definition.get("localization_guid"), str) or not definition["localization_guid"].strip():
                raise ContentCompilerError("localization_probe requires localization_guid.")
        if "customization" in definition:
            if not isinstance(definition["customization"], dict):
                raise ContentCompilerError("customization must be an object.")
            allowed = {"identity", "localization", "recipe", "layout", "icon", "color", "color_adjustments", "item_color_combination", "material", "texture", "model", "visual_transform", "visual_preview_policy", "mechanics"}
            unknown = sorted(set(definition["customization"]) - allowed)
            if unknown:
                raise ContentCompilerError("Unsupported customization fields: " + ", ".join(unknown))
            color_plan = definition["customization"].get("item_color_combination")
            if color_plan is not None:
                if not isinstance(color_plan, dict):
                    raise ContentCompilerError("customization.item_color_combination must be an object.")
                if color_plan.get("runtime_field") != "itemColorCombinationSetup":
                    raise ContentCompilerError("customization.item_color_combination has an invalid runtime field.")
                for channel in ("color0", "color1", "color2"):
                    value = color_plan.get(channel)
                    if not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
                        raise ContentCompilerError(f"customization.item_color_combination.{channel} must be a packed 32-bit color.")
                if color_plan.get("isSet") is not True:
                    raise ContentCompilerError("customization.item_color_combination.isSet must be true.")
            for key, value in definition["customization"].items():
                if not isinstance(value, (dict, list, str, int, float, bool)) and value is not None:
                    raise ContentCompilerError(f"customization.{key} must be JSON-compatible.")
                if key == "mechanics":
                    if not isinstance(value, dict):
                        raise ContentCompilerError("customization.mechanics must be an object.")
                    allowed_mechanics = {
                        "preservation_policy", "comfort", "stack_size", "maxStackSize", "durability",
                        "placement_behavior", "required_workstation", "resource_requirements", "tags",
                        "category", "unlock_state", "functional_flags",
                    }
                    unknown_mechanics = sorted(set(value) - allowed_mechanics)
                    if unknown_mechanics:
                        raise ContentCompilerError(
                            "Unsupported mechanics customization fields: " + ", ".join(unknown_mechanics)
                        )
                    policy = str(value.get("preservation_policy", "preserve")).strip().lower()
                    if policy not in {"preserve", "replace"}:
                        raise ContentCompilerError(
                            "customization.mechanics.preservation_policy must be 'preserve' or 'replace'."
                        )
                if key == "visual_transform":
                    if not isinstance(value, dict):
                        raise ContentCompilerError("customization.visual_transform must be an object.")
                    for transform in ("scale", "offset"):
                        vector = value.get(transform)
                        if vector is not None and (
                            not isinstance(vector, list) or len(vector) != 3
                            or not all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in vector)
                        ):
                            raise ContentCompilerError(
                                f"customization.visual_transform.{transform} must contain exactly three numeric values."
                            )
                if key == "visual_preview_policy":
                    if not isinstance(value, dict):
                        raise ContentCompilerError("customization.visual_preview_policy must be an object.")
                    allowed_policies = {"donor-fallback", "replacement-preview", "custom-research", "unverified"}
                    for policy_key in ("catalog", "placement"):
                        if value.get(policy_key) not in allowed_policies:
                            raise ContentCompilerError(f"customization.visual_preview_policy.{policy_key} is unsafe.")
        if "icon" in definition and not isinstance(definition["icon"], str):
            raise ContentCompilerError("icon must be a PNG path string.")
        if "icon_slug" in definition and not isinstance(definition["icon_slug"], str):
            raise ContentCompilerError("icon_slug must be a string.")
        for key in ("icon_resource_type", "icon_field", "icon_resource_id"):
            if key in definition and definition[key] is not None and not isinstance(definition[key], str):
                raise ContentCompilerError(f"{key} must be a string.")
        if definition.get("registry_probe") or definition.get("minimal_probe"):
            if not isinstance(definition.get("donor_guid"), str) or not definition["donor_guid"].strip():
                raise ContentCompilerError("minimal_probe requires donor_guid.")
            if not isinstance(definition.get("new_item_id"), int) or definition["new_item_id"] <= 0:
                raise ContentCompilerError("minimal_probe requires a positive integer new_item_id.")

    def _metadata_policy(self, resource_type: str) -> dict[str, Any]:
        research_dir = self.base_dir / "research"
        candidates = sorted(research_dir.glob("SAFE_METADATA_RESOURCE_TYPES_*.json"), reverse=True)
        path = candidates[0] if candidates else research_dir / "SAFE_METADATA_RESOURCE_TYPES_20260928.json"
        try:
            policy = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            return {"state": "unknown", "resource_type": resource_type}
        aliases = [str(resource_type)]
        if not str(resource_type).startswith("keen::"):
            aliases.append("keen::" + str(resource_type))
        for item in policy.get("quarantined_types", []):
            if item.get("type") in aliases:
                return {"state": "quarantined", "resource_type": resource_type,
                        "policy_type": item.get("type"), "reason": item.get("reason"),
                        "target_build": policy.get("target_build")}
        for item in policy.get("verified_types", []):
            if item.get("type") in aliases:
                return {"state": "verified", "resource_type": resource_type,
                        "policy_type": item.get("type"), "target_build": policy.get("target_build")}
        return {"state": "unverified", "resource_type": resource_type,
                "target_build": policy.get("target_build")}

    @staticmethod
    def _slug(value: str) -> str:
        result = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value).strip()).strip("_").lower()
        if not result:
            raise ContentCompilerError("Content ID cannot be empty.")
        return result[:64]

    @staticmethod
    def _customization_contract(value: Any) -> dict[str, Any]:
        """Normalize requested edits without pretending they are runtime-proven.

        The compiler records the author's intent and maturity gate. Runtime Lua
        generation remains separate so unsupported visual/model edits cannot be
        silently deployed as if they were verified.
        """
        if value is None:
            value = {}
        if not isinstance(value, dict):
            raise ContentCompilerError("customization must be an object.")
        # Packaging an icon is supported, but engine-side icon replacement is
        # not yet visually verified on the current build. Keep it gated until
        # a same-build in-game rendering result exists.
        verified = {"identity", "localization", "recipe", "layout"}
        result = {}
        for key, requested in value.items():
            normalized = copy.deepcopy(requested)
            # Make the donor-behavior decision explicit in every compiled
            # definition.  Preservation is the safe default; replacing donor
            # mechanics is intentionally retained as research-only until a
            # runtime authority path is proven for the target build.
            if key == "mechanics":
                if not isinstance(normalized, dict):
                    raise ContentCompilerError("customization.mechanics must be an object.")
                policy = str(normalized.get("preservation_policy", "preserve")).strip().lower()
                if policy not in {"preserve", "replace"}:
                    raise ContentCompilerError(
                        "customization.mechanics.preservation_policy must be 'preserve' or 'replace'."
                    )
                normalized["preservation_policy"] = policy
            result[key] = {
                "requested": normalized,
                "status": "verified" if key in verified else "research-only",
                "runtime_action": "apply" if key in verified else "hold_for_research",
            }
        return result
