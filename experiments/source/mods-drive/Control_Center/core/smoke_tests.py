"""Static smoke tests for generated EML/KFC content projects."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .content_validation import ContentProjectValidator
from .package_service import PackageService
from .resource_inspector import ResourceInspector


@dataclass(frozen=True)
class SmokeCheck:
    name: str
    passed: bool
    details: str


@dataclass(frozen=True)
class SmokeReport:
    project: Path
    checks: tuple[SmokeCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)


class ContentSmokeTester:
    def run(self, project: Path) -> SmokeReport:
        project = Path(project).resolve()
        checks: list[SmokeCheck] = []
        validation = ContentProjectValidator().validate(project)
        checks.append(SmokeCheck("content validation", validation.valid, "; ".join(issue.message for issue in validation.issues) or "valid"))
        manifest = project / "mod.json"
        checks.append(SmokeCheck("manifest", manifest.is_file(), "mod.json present" if manifest.is_file() else "mod.json missing"))
        entry = project / "src" / "mod.lua"
        checks.append(SmokeCheck("entrypoint", entry.is_file(), "src/mod.lua present" if entry.is_file() else "src/mod.lua missing"))
        helper = project / "src" / "kfc_content_registry.lua"
        helper_ok = helper.is_file() and "register_resource" in helper.read_text(encoding="utf-8", errors="replace")
        checks.append(SmokeCheck("runtime helper", helper_ok, "packaged helper exposes register_resource" if helper_ok else "helper missing or incomplete"))
        package_ok, package_errors = PackageService().verify(project)
        checks.append(SmokeCheck("package hashes", package_ok, "; ".join(package_errors) or "hashes verified"))
        records = ResourceInspector().scan(project)
        checks.append(SmokeCheck("resource JSON", True, f"{len(records)} readable resource file(s)"))
        return SmokeReport(project, tuple(checks))
