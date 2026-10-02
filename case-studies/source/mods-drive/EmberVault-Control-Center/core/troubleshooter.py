"""Read-only health checks for the Control Center workspace."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .game_detection import GameDetector
from .compatibility import CompatibilityState, evaluate
from .modules import ModuleRegistry
from .packages import PackageService
from .profiles import ProfileService
from .settings import SettingsService


@dataclass(frozen=True)
class Diagnostic:
    key: str
    title: str
    severity: str
    message: str


class TroubleshooterService:
    def __init__(self, root: Path, settings: SettingsService, profiles: ProfileService,
                 modules: ModuleRegistry, packages: PackageService, detector: GameDetector):
        self.root = Path(root)
        self.settings = settings
        self.profiles = profiles
        self.modules = modules
        self.packages = packages
        self.detector = detector

    def scan(self) -> list[Diagnostic]:
        findings: list[Diagnostic] = []
        settings = self.settings.load()
        detected_build = None
        if not settings.game_path:
            findings.append(Diagnostic("game-path", "Game location", "attention", "Choose the Enshrouded installation folder."))
        else:
            installation = self.detector.detect(Path(settings.game_path))
            detected_build = installation.build_id
            issues = self.detector.validate(installation)
            if issues:
                findings.append(Diagnostic("game-installation", "Game installation", "attention", "; ".join(issues)))
            else:
                findings.append(Diagnostic("game-installation", "Game installation", "ready", "Installation detected and readable."))
        profiles = self.profiles.list()
        findings.append(Diagnostic("profiles", "Profiles", "ready" if profiles else "attention",
                                   f"{len(profiles)} profile{'s' if len(profiles) != 1 else ''} available."))
        modules = self.modules.discover()
        findings.append(Diagnostic("modules", "Module registry", "ready", f"{len(modules)} module manifest{'s' if len(modules) != 1 else ''} discovered."))
        packages = self.packages.list()
        findings.append(Diagnostic("packages", "Package registry", "ready", f"{len(packages)} package{'s' if len(packages) != 1 else ''} discovered."))
        package_map = {item.id: item for item in packages}
        cycle_nodes: set[str] = set()
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(package_id: str, trail: tuple[str, ...] = ()) -> None:
            if package_id in visiting:
                cycle_nodes.update(trail[trail.index(package_id):] if package_id in trail else trail)
                return
            if package_id in visited or package_id not in package_map:
                return
            visiting.add(package_id)
            for dependency in package_map[package_id].dependencies:
                visit(dependency, (*trail, package_id))
            visiting.remove(package_id)
            visited.add(package_id)

        for package_id in package_map:
            visit(package_id)
        if cycle_nodes:
            findings.append(Diagnostic(
                "package-dependency-cycle", "Package dependencies", "attention",
                f"Dependency cycle detected: {', '.join(sorted(cycle_nodes))}",
            ))
        for package in packages:
            compatibility = evaluate(required_builds=list(package.required_builds), detected_build=detected_build)
            if compatibility.state in {CompatibilityState.INCOMPATIBLE, CompatibilityState.BLOCKED}:
                findings.append(Diagnostic(
                    f"package-{package.id}", package.name, "attention",
                    "; ".join(compatibility.reasons),
                ))
            missing = [dependency for dependency in package.dependencies if dependency not in {item.id for item in packages}]
            if missing:
                findings.append(Diagnostic(
                    f"package-dependency-{package.id}", package.name, "attention",
                    f"Missing package dependencies: {', '.join(missing)}",
                ))
            for profile in profiles:
                if package.id in profile.enabled_packages:
                    disabled = [dependency for dependency in package.dependencies if dependency not in profile.enabled_packages]
                    if disabled:
                        findings.append(Diagnostic(
                            f"package-profile-dependency-{profile.id}-{package.id}", package.name, "attention",
                            f"Profile {profile.name} has disabled dependencies: {', '.join(disabled)}",
                        ))
        if settings.game_path:
            for profile in profiles:
                for action in self.packages.deployment_plan(profile, Path(settings.game_path)):
                    if action.status != "ready":
                        findings.append(Diagnostic(
                            f"deployment-{profile.id}-{action.package_id}", "Mod deployment", "attention",
                            f"Profile {profile.name}: {action.package_id} is {action.status}"
                            + (f" ({action.reason})" if action.reason else ""),
                        ))
        return findings
