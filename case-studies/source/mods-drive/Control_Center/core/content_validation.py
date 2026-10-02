"""Fail-closed validation for staged and generated custom-content projects."""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


KNOWN_RESOURCE_TYPES = {
    "ItemInfo", "ItemRegistryResource", "RecipeRegistryResource",
    "ItemKnowledgeResource", "FbUiBundle", "HashKey32", "TemplateResource",
    "RenderModel", "ActorSequenceResource", "Localization",
}


@dataclass(frozen=True)
class ContentIssue:
    severity: str
    code: str
    message: str
    path: str | None = None


@dataclass(frozen=True)
class ContentValidationReport:
    project: Path
    issues: tuple[ContentIssue, ...]
    manifest: dict[str, Any] | None = None

    @property
    def valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)


class ContentProjectValidator:
    """Validate a content project without touching the game installation."""

    MANIFEST_NAMES = ("content.json", "mod.json", "CLONE_MANIFEST.json")

    def validate(self, project: Path) -> ContentValidationReport:
        project = Path(project).resolve()
        issues: list[ContentIssue] = []
        manifest_path = next((project / name for name in self.MANIFEST_NAMES if (project / name).is_file()), None)
        if not manifest_path:
            return ContentValidationReport(project, (ContentIssue("error", "manifest.missing", "No supported content manifest was found."),))
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            return ContentValidationReport(project, (ContentIssue("error", "manifest.invalid", str(exc), manifest_path.name),))
        if not isinstance(manifest, dict):
            return ContentValidationReport(project, (ContentIssue("error", "manifest.type", "Content manifest must be a JSON object.", manifest_path.name),))

        if "schema" in manifest and str(manifest["schema"]).startswith("control_center.bed_clone_staging"):
            self._validate_bed_staging(manifest, issues)
        else:
            self._validate_general_manifest(manifest, issues)
        self._validate_content_class(project, manifest, issues)
        self._validate_donor_schemas(project, manifest, issues)
        self._validate_asset_manifest(project, issues)
        self._validate_visual_variant(project, issues)
        self._validate_template_graph_plan(project, manifest, issues)
        self._validate_localization_payload(project, issues)
        self._validate_package_manifest(project, issues)
        self._validate_files(project, issues)
        return ContentValidationReport(project, tuple(issues), manifest)

    @staticmethod
    def _validate_visual_variant(project: Path, issues: list[ContentIssue]) -> None:
        path = project / "content" / "visual_variant.json"
        if not path.is_file():
            return
        try:
            variant = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            issues.append(ContentIssue("error", "visual_variant.invalid", str(exc), "content/visual_variant.json"))
            return
        if not isinstance(variant, dict):
            issues.append(ContentIssue("error", "visual_variant.type", "Visual variant must be an object.", "content/visual_variant.json"))
            return
        adjustments = variant.get("color_adjustments")
        if adjustments is not None:
            if not isinstance(adjustments, list):
                issues.append(ContentIssue("error", "visual_variant.colors_invalid", "color_adjustments must be a list.", "content/visual_variant.json:color_adjustments"))
            else:
                from .visual_colors import hex_to_packed_color
                for index, adjustment in enumerate(adjustments):
                    location = f"content/visual_variant.json:color_adjustments[{index}]"
                    if not isinstance(adjustment, dict) or not adjustment.get("target"):
                        issues.append(ContentIssue("error", "visual_variant.color_entry_invalid", "Each color adjustment needs a target and color.", location))
                        continue
                    try:
                        hex_to_packed_color(str(adjustment.get("color", "")))
                    except ValueError as exc:
                        issues.append(ContentIssue("error", "visual_variant.color_invalid", str(exc), location))
        for key in ("scale", "offset"):
            value = variant.get(key)
            if value is not None and (not isinstance(value, list) or len(value) != 3 or
                                      not all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)):
                issues.append(ContentIssue("error", "visual_variant.transform_invalid", f"{key} must contain exactly three numeric values.", f"content/visual_variant.json:{key}"))
        if isinstance(variant.get("scale"), list) and any(isinstance(item, (int, float)) and item <= 0 for item in variant["scale"]):
            issues.append(ContentIssue("error", "visual_variant.scale_invalid", "Scale values must be greater than zero.", "content/visual_variant.json:scale"))
        allowed = {"donor-fallback", "replacement-preview", "custom-research", "unverified"}
        for key in ("catalog_preview", "placement_preview"):
            value = variant.get(key)
            if value is not None and value not in allowed:
                issues.append(ContentIssue("error", "visual_variant.preview_policy_invalid", f"Unsupported {key} policy: {value}", f"content/visual_variant.json:{key}"))

    @staticmethod
    def _validate_package_manifest(project: Path, issues: list[ContentIssue]) -> None:
        if not (project / "package.json").is_file():
            return
        try:
            from .package_service import PackageService
            valid, errors = PackageService().verify(project)
        except Exception as exc:
            issues.append(ContentIssue("error", "package.manifest_invalid", str(exc), "package.json"))
            return
        if not valid:
            issues.extend(ContentIssue("error", "package.integrity", error, "package.json") for error in errors)

    @staticmethod
    def _validate_content_class(project: Path, manifest: dict[str, Any], issues: list[ContentIssue]) -> None:
        try:
            from .content_classes import ContentClassService
            profile = ContentClassService().infer(manifest)
            if profile is None:
                return
            missing = ContentClassService().validate_resource_families(
                profile, ContentClassService.resource_types(project))
            # Runtime-generated projects intentionally do not carry extracted
            # donor families; their EML entrypoint resolves those resources at
            # startup. Keep the project valid but visibly research-gated.
            runtime_generated = isinstance(manifest.get("runtime_generation"), dict)
            for resource_type in missing:
                severity = "warning" if runtime_generated else ("error" if profile.status == "verified" else "warning")
                issues.append(ContentIssue(severity, "content_class.resource_missing", resource_type, profile.name))
            if profile.status == "research-only":
                issues.append(ContentIssue("warning", "content_class.research_only",
                                            f"{profile.name} is not runtime-proven on the target build.", profile.name))
            metadata = manifest.get("donor_metadata")
            if metadata is not None:
                if not isinstance(metadata, dict):
                    issues.append(ContentIssue("error", "donor_schema.metadata_type", "donor_metadata must be an object.", "donor_metadata"))
                else:
                    for message in ContentClassService().validate_donor_schema(profile, metadata):
                        issues.append(ContentIssue("error", "donor_schema.identity", message, "donor_metadata"))
        except ValueError as exc:
            issues.append(ContentIssue("error", "content_class.unknown", str(exc), "content_class"))

    @staticmethod
    def _validate_donor_schemas(project: Path, manifest: dict[str, Any], issues: list[ContentIssue]) -> None:
        declarations = manifest.get("donor_validation", [])
        if declarations is None:
            return
        if not isinstance(declarations, list):
            issues.append(ContentIssue("error", "donor_schema.structure", "donor_validation must be a list.", "donor_validation"))
            return
        try:
            from .resource_inspector import ResourceInspector
            inspector = ResourceInspector()
            for index, declaration in enumerate(declarations):
                location = f"donor_validation[{index}]"
                if not isinstance(declaration, dict):
                    issues.append(ContentIssue("error", "donor_schema.entry_type", "Donor validation entries must be objects.", location))
                    continue
                donor = ContentProjectValidator._project_path(project, declaration.get("donor"), issues, location + ".donor")
                candidate = ContentProjectValidator._project_path(project, declaration.get("candidate"), issues, location + ".candidate")
                if donor is None or candidate is None:
                    continue
                if not donor.is_file() or not candidate.is_file():
                    issues.append(ContentIssue("error", "donor_schema.file_missing", "Donor and candidate resource files are required.", location))
                    continue
                try:
                    plan = inspector.clone_plan(donor, candidate, declaration.get("resource_type"), candidate)
                except ValueError as exc:
                    issues.append(ContentIssue("error", "donor_schema.invalid", str(exc), location))
                    continue
                for difference in plan.differences:
                    severity = "error" if difference.severity == "error" else "warning"
                    issues.append(ContentIssue(severity, "donor_schema.difference", difference.message,
                                                f"{location}.{difference.path}"))
        except Exception as exc:
            issues.append(ContentIssue("error", "donor_schema.validation_failed", str(exc), "donor_validation"))

    @staticmethod
    def _project_path(project: Path, raw: Any, issues: list[ContentIssue], location: str) -> Path | None:
        if not isinstance(raw, str) or not raw.strip():
            issues.append(ContentIssue("error", "donor_schema.path_missing", "Resource path is required.", location))
            return None
        path = project / raw
        try:
            resolved = path.resolve()
            resolved.relative_to(project)
        except ValueError:
            issues.append(ContentIssue("error", "donor_schema.path_unsafe", "Resource path must remain inside the project.", location))
            return None
        if path.is_symlink():
            issues.append(ContentIssue("error", "donor_schema.symlink", "Symbolic links are not allowed for donor resources.", location))
            return None
        return path

    @staticmethod
    def _validate_asset_manifest(project: Path, issues: list[ContentIssue]) -> None:
        path = project / "assets.json"
        if not path.is_file(): return
        try:
            from .asset_service import AssetService
            valid, errors = AssetService().verify(project)
        except Exception as exc:
            issues.append(ContentIssue("error", "assets.manifest_invalid", str(exc), "assets.json")); return
        if not valid:
            issues.extend(ContentIssue("error", "assets.integrity", error, "assets.json") for error in errors)

    @staticmethod
    def _validate_template_graph_plan(project: Path, manifest: dict[str, Any], issues: list[ContentIssue]) -> None:
        plan = manifest.get("template_graph_plan")
        if plan is None:
            return
        if not isinstance(plan, dict):
            issues.append(ContentIssue("error", "template_graph.plan_type", "template_graph_plan must be an object.", "template_graph_plan"))
            return
        relative = str(plan.get("candidate_path", "")).strip()
        candidate = project / relative
        try:
            candidate.resolve().relative_to(project)
        except ValueError:
            issues.append(ContentIssue("error", "template_graph.path_unsafe", "Candidate path must remain inside the project.", relative)); return
        if not candidate.is_file() or candidate.is_symlink():
            issues.append(ContentIssue("error", "template_graph.candidate_missing", "Template graph candidate is missing.", relative)); return
        expected = str(plan.get("candidate_sha256", "")).strip().lower()
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if expected != actual:
            issues.append(ContentIssue("error", "template_graph.hash_mismatch", "Template graph candidate hash does not match the manifest.", relative))
        source_raw = str(plan.get("source", "")).strip()
        expected_source = str(plan.get("source_sha256", "")).strip().lower()
        if source_raw and expected_source:
            source = Path(source_raw)
            if source.is_file() and not source.is_symlink():
                source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
                if source_hash != expected_source:
                    issues.append(ContentIssue("error", "template_graph.source_changed", "Template graph donor source hash changed.", source_raw))
            else:
                issues.append(ContentIssue("warning", "template_graph.source_unavailable", "Template graph donor source is unavailable for provenance recheck.", source_raw))

    @staticmethod
    def _validate_localization_payload(project: Path, issues: list[ContentIssue]) -> None:
        path = project / "content" / "localization.json"
        if not path.is_file(): return
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            issues.append(ContentIssue("error", "localization.invalid", str(exc), "content/localization.json")); return
        try:
            from .localization import LocalizationService
            localization_issues = LocalizationService.validate_payload(data)
        except Exception as exc:
            issues.append(ContentIssue("error", "localization.validation_failed", str(exc), "content/localization.json")); return
        for localization_issue in localization_issues:
            issues.append(ContentIssue(localization_issue.severity, "localization.invalid", localization_issue.message,
                                        f"content/localization.json:{localization_issue.key}"))

    @staticmethod
    def _validate_bed_staging(manifest: dict[str, Any], issues: list[ContentIssue]) -> None:
        required = ("cloneItemId", "cloneRecipeId", "donorItemId", "donorRecipeId", "cloneItemGuid", "cloneRecipeGuid")
        for key in required:
            if key not in manifest:
                issues.append(ContentIssue("error", "staging.field_missing", f"Missing staging field: {key}"))
        for key in ("cloneItemId", "cloneRecipeId", "donorItemId", "donorRecipeId"):
            if key in manifest and (not isinstance(manifest[key], int) or manifest[key] <= 0):
                issues.append(ContentIssue("error", "staging.id_invalid", f"{key} must be a positive integer."))
        if manifest.get("liveGameModified") is True:
            issues.append(ContentIssue("error", "staging.unsafe", "Staging metadata claims that live game files were modified."))

    @staticmethod
    def _validate_general_manifest(manifest: dict[str, Any], issues: list[ContentIssue]) -> None:
        for key in ("id", "name", "version"):
            if not str(manifest.get(key, "")).strip():
                issues.append(ContentIssue("error", "manifest.field_missing", f"Missing manifest field: {key}"))
        namespace = manifest.get("namespace")
        if namespace is not None:
            try:
                from .content_identity import ContentIdentityService
                ContentIdentityService.validate_namespace(str(namespace))
            except ValueError as exc:
                issues.append(ContentIssue("error", "manifest.namespace_invalid", str(exc)))
        capabilities = manifest.get("capabilities", [])
        if not isinstance(capabilities, list) or any(not isinstance(value, str) or not value.strip() for value in capabilities):
            issues.append(ContentIssue("error", "manifest.capabilities_invalid", "Manifest capabilities must be a list of non-empty strings.", "capabilities"))
        required_api = manifest.get("required_loader_api")
        if required_api is not None:
            required_apis = [required_api] if isinstance(required_api, str) else required_api
            if not isinstance(required_apis, list) or any(not isinstance(value, str) or not value.strip() for value in required_apis):
                issues.append(ContentIssue("error", "manifest.required_api_invalid", "required_loader_api must be a string or list of non-empty strings.", "required_loader_api"))
            else:
                try:
                    from .api_capabilities import CAPABILITY_ALIASES
                    known = set(CAPABILITY_ALIASES)
                    for value in required_apis:
                        if value not in known:
                            issues.append(ContentIssue("warning", "manifest.required_api_unknown", f"Loader capability requires target-build negotiation: {value}", "required_loader_api"))
                except ImportError:
                    pass
        ids: set[str] = set()
        for index, item in enumerate(manifest.get("content", [])):
            if not isinstance(item, dict):
                issues.append(ContentIssue("error", "content.entry_type", "Content entries must be objects.", f"content[{index}]"))
                continue
            identity = str(item.get("id", ""))
            if not identity:
                issues.append(ContentIssue("error", "content.id_missing", "Content entry has no id.", f"content[{index}]"))
            elif identity in ids:
                issues.append(ContentIssue("error", "content.id_duplicate", f"Duplicate content id: {identity}", f"content[{index}]"))
            ids.add(identity)
            resource_type = item.get("resource_type")
            if resource_type and str(resource_type).split("::")[-1] not in KNOWN_RESOURCE_TYPES:
                issues.append(ContentIssue("warning", "content.resource_type_unknown", f"Resource type requires donor-specific research: {resource_type}", f"content[{index}]"))

    @staticmethod
    def _validate_files(project: Path, issues: list[ContentIssue]) -> None:
        for path in project.rglob("*"):
            if not path.is_file():
                continue
            try:
                path.relative_to(project)
            except ValueError:
                issues.append(ContentIssue("error", "file.outside_project", "Project contains a path outside its root.", str(path)))
            if path.suffix.lower() == ".json":
                try:
                    # Extracted KFC JSON occasionally carries a UTF-8 BOM.
                    # Accept that encoding without weakening syntax checks.
                    json.loads(path.read_text(encoding="utf-8-sig"))
                except (OSError, ValueError) as exc:
                    issues.append(ContentIssue("error", "resource.json_invalid", str(exc), str(path.relative_to(project))))
