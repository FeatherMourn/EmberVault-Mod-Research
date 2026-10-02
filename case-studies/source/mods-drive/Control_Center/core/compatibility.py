"""Compatibility evaluation for game builds, loader APIs, and module maturity."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from .platform_services import feature_state
from .compatibility_shims import CompatibilityShimService
from .loader_adapter import EmlCompatibilityAdapter
from .api_capabilities import CapabilityRegistry


CONSTRAINT_RE = re.compile(r"^(>=|<=|>|<|=)?\s*(\d+)$")
LOADER_API_VERSION_RE = re.compile(r"^(>=|<=|>|<|=|~\s*)?\s*(\d+)\.(\d+)$")


@dataclass(frozen=True)
class CompatibilityIssue:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class CompatibilityReport:
    module_id: str
    compatible: bool
    feature_state: str
    issues: tuple[CompatibilityIssue, ...]


def build_satisfies(build_id: str | None, constraints: Iterable[str]) -> bool | None:
    """Return True/False when testable, or None when the current build is unknown."""
    if not build_id:
        return None
    build_text = str(build_id).strip()
    constraints = list(constraints)
    if not constraints:
        return True
    # Full EML identities (numeric build, branch, and timestamp) can be
    # pinned exactly. This prevents a hotfix on the same numeric family from
    # being mistaken for the previously verified runtime.
    exact_full = [str(raw).strip() for raw in constraints if "|" in str(raw)]
    if exact_full:
        return build_text in exact_full
    match = re.match(r"^(\d+)", build_text)
    if not match:
        return None
    build = int(match.group(1))
    checks = []
    for raw in constraints:
        match = CONSTRAINT_RE.fullmatch(str(raw).strip())
        if not match:
            continue
        operator, value = match.group(1) or "=", int(match.group(2))
        checks.append({">=": build >= value, "<=": build <= value, ">": build > value, "<": build < value, "=": build == value}[operator])
    return all(checks) if checks else False


class CompatibilityEngine:
    """Evaluate manifests conservatively before package generation."""

    def __init__(self, loader_api_version: str | None = None):
        self.loader_api_version = loader_api_version

    @staticmethod
    def _loader_api_version_satisfies(current: str, constraint: str) -> bool | None:
        actual = LOADER_API_VERSION_RE.fullmatch(str(current).strip())
        required = LOADER_API_VERSION_RE.fullmatch(str(constraint).strip())
        if not actual or not required:
            return None
        found = (int(actual.group(2)), int(actual.group(3)))
        expected = (int(required.group(2)), int(required.group(3)))
        operator = (required.group(1) or "=").replace(" ", "")
        if operator == "~":
            return found[0] == expected[0] and found >= expected
        return {"=": found == expected, ">=": found >= expected, "<=": found <= expected,
                ">": found > expected, "<": found < expected}[operator]

    def evaluate(self, manifest: dict[str, Any], build_id: str | None, capabilities: set[str] | None = None, allow_research: bool = False) -> CompatibilityReport:
        manifest, shims = CompatibilityShimService().adapt_manifest(manifest)
        module_id = str(manifest.get("id", "unknown"))
        state = feature_state(manifest)
        issues: list[CompatibilityIssue] = []
        for shim in shims:
            issues.append(CompatibilityIssue("warning", "compatibility_shim", f"Applied compatibility shim: {shim}."))
        loader = EmlCompatibilityAdapter().inspect(capabilities or set())
        capabilities = set(loader.capabilities)
        issues.extend(CompatibilityIssue("warning", "loader_provenance", warning) for warning in loader.warnings)
        builds = manifest.get("compatible_game_builds", [])
        if isinstance(builds, str): builds = [builds]
        build_result = build_satisfies(build_id, builds)
        if build_result is False:
            issues.append(CompatibilityIssue("error", "game_build_incompatible", f"Module does not support game build {build_id}."))
        elif build_result is None and builds:
            issues.append(CompatibilityIssue("warning", "game_build_unknown", "Game build is unknown; compatibility cannot be confirmed."))
        if state == "research-only" and not allow_research:
            issues.append(CompatibilityIssue("warning", "research_only", "Module is research-only and requires explicit opt-in."))
        required = manifest.get("required_loader_api")
        if required:
            required_items = [required] if isinstance(required, str) else list(required)
            missing = CapabilityRegistry().missing([str(item) for item in required_items], capabilities)
            if missing:
                issues.append(CompatibilityIssue("error", "loader_capability_missing", "Missing loader capability: " + ", ".join(missing)))
        required_version = manifest.get("required_loader_api_version")
        if required_version is not None:
            if not isinstance(required_version, str) or not LOADER_API_VERSION_RE.fullmatch(required_version.strip()):
                issues.append(CompatibilityIssue("error", "loader_api_version_invalid",
                                                 "required_loader_api_version must be a valid version constraint string."))
            elif not self.loader_api_version:
                issues.append(CompatibilityIssue("warning", "loader_api_version_unknown",
                                                 f"Module requires EML API {required_version}; current API version is unknown."))
            else:
                version_result = self._loader_api_version_satisfies(self.loader_api_version, required_version)
                if version_result is False:
                    issues.append(CompatibilityIssue("error", "loader_api_version_incompatible",
                        f"Module requires EML API {required_version} (current {self.loader_api_version})."))
                elif version_result is None:
                    issues.append(CompatibilityIssue("error", "loader_api_version_invalid",
                        f"Unsupported EML API version constraint: {required_version}."))
        return CompatibilityReport(module_id, not any(issue.severity == "error" for issue in issues), state, tuple(issues))

    def evaluate_all(self, modules: dict[str, dict[str, Any]], build_id: str | None, capabilities: set[str] | None = None, enabled: set[str] | None = None, allow_research: bool = False) -> dict[str, CompatibilityReport]:
        selected = set(modules) if enabled is None else set(enabled)
        return {module_id: self.evaluate(manifest, build_id, capabilities, allow_research) for module_id, manifest in modules.items() if module_id in selected}
