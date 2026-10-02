"""Platform services shared by the Control Center UI and deployment tools.

This module is intentionally file-based and side-effect light.  It gives the
dashboard one authoritative way to inspect the game, loader, and module graph
without making the UI responsible for interpreting manifests or logs.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


BUILD_RE = re.compile(r"(?<!\d)(\d{6,})(?!\d)")
VERSION_CONSTRAINT_RE = re.compile(r"^(>=|<=|>|<|=|~\s*)?\s*(\d+)\.(\d+)\.(\d+)$")
LOADER_API_RE = re.compile(r"^(>=|<=|>|<|=|~\s*)?\s*(\d+)\.(\d+)$")
LOADER_API_REPORTED_MESSAGE = "Lua API initialized"


@dataclass(frozen=True)
class GameBuild:
    build_id: str | None
    source: str | None
    game_dir: Path
    confidence: str = "unknown"


class GameBuildDetector:
    """Find the best available game-build evidence without modifying the game."""

    FILENAMES = ("build.txt", "version.txt", "build.json", "version.json")

    def detect(self, game_dir: Path) -> GameBuild:
        game_dir = Path(game_dir)
        candidates: list[tuple[str, str, str]] = []
        for path in self._candidate_files(game_dir):
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            build = self._extract_build(raw, path.suffix.lower() == ".json")
            if build:
                candidates.append((build, str(path), "high" if path.name in self.FILENAMES else "medium"))

        if candidates:
            build, source, confidence = candidates[0]
            return GameBuild(build, source, game_dir, confidence)
        # The EML type-registry event is authoritative for the KFC/runtime
        # build actually loaded by the game.  Prefer its explicit version over
        # arbitrary numeric values found in cache metadata.
        logs = sorted((game_dir / "logs").glob("*.eml.log"), key=lambda p: p.stat().st_mtime, reverse=True) if (game_dir / "logs").is_dir() else []
        for path in logs[:3]:
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for line in reversed(lines):
                try:
                    event = json.loads(line)
                except (TypeError, ValueError):
                    continue
                fields = event.get("fields", {})
                if fields.get("message") == "Type registry loaded successfully" and fields.get("version"):
                    match = BUILD_RE.search(str(fields["version"]))
                    if match:
                        return GameBuild(match.group(1), str(path), game_dir, "high")
        # Steam's app manifest is useful only when neither game metadata nor
        # an EML runtime log publishes a build. It describes depot state, not
        # guaranteed EML/KFC compatibility.
        for manifest in game_dir.parents:
            path = manifest / "steamapps" / "appmanifest_1203620.acf"
            if path.is_file():
                try:
                    raw = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                match = re.search(r'"buildid"\s+"(\d+)"', raw, re.IGNORECASE)
                if match:
                    return GameBuild(match.group(1), str(path), game_dir, "medium")
                break
        return GameBuild(None, None, game_dir)

    def _candidate_files(self, game_dir: Path) -> Iterable[Path]:
        for name in self.FILENAMES:
            yield game_dir / name
        cache = game_dir / ".cache"
        for name in self.FILENAMES:
            yield cache / name
        # Do not scan arbitrary cache JSON here. Steam/EML cache files often
        # contain fields named `build_id` that are file-cache timestamps, not
        # game builds. Runtime logs are handled separately below.

    @staticmethod
    def _extract_build(raw: str, is_json: bool) -> str | None:
        if is_json:
            try:
                data = json.loads(raw)
            except (TypeError, ValueError):
                return None
            if isinstance(data, dict):
                for key in ("build", "build_id", "buildId", "version"):
                    value = data.get(key)
                    match = BUILD_RE.search(str(value)) if value is not None else None
                    if match:
                        return match.group(1)
                return None
            return None
        match = BUILD_RE.search(raw)
        return match.group(1) if match else None


@dataclass(frozen=True)
class RuntimeHealth:
    status: str
    log_path: Path | None
    build_id: str | None = None
    loader_api_version: str | None = None
    events: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


class RuntimeHealthService:
    """Summarize the latest EML log using explicit, conservative signals."""

    ERROR_MARKERS = ("panic", "fatal error", "stack overflow", "out of bounds")
    SUCCESS_MARKERS = ("registered|", "ui_links|", "loaded mod", "module loaded")

    def inspect(self, game_dir: Path) -> RuntimeHealth:
        logs_dir = Path(game_dir) / "logs"
        logs = sorted(logs_dir.glob("*.eml.log"), key=lambda p: p.stat().st_mtime, reverse=True) if logs_dir.is_dir() else []
        if not logs:
            return RuntimeHealth("unknown", None)
        path = logs[0]
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return RuntimeHealth("unknown", path)
        lowered = [line.lower() for line in lines]
        errors_list: list[str] = []
        error_lines: list[int] = []
        events_list: list[str] = []
        event_lines: list[int] = []
        latest_session_start = 0
        latest_session_version: str | None = None
        # A single EML log is append-only across launches.  A successful type
        # registry load is the strongest available session boundary; errors
        # before the newest boundary are historical startup records, not a
        # current loader failure.
        for line_number, (line, low) in enumerate(zip(lines, lowered), 1):
            try:
                record = json.loads(line)
            except (TypeError, ValueError):
                record = None
            if isinstance(record, dict) and str(record.get("level", "")).lower() in {"error", "fatal", "panic"}:
                fields = record.get("fields") if isinstance(record.get("fields"), dict) else record
                details = []
                for key in ("message", "report", "error", "stacktrace"):
                    if isinstance(fields, dict) and fields.get(key) is not None:
                        details.append(str(fields[key]))
                errors_list.append(" | ".join(details) or line)
                error_lines.append(line_number)
            elif any(marker in low for marker in self.ERROR_MARKERS):
                errors_list.append(line)
                error_lines.append(line_number)
            if any(marker in low for marker in self.SUCCESS_MARKERS):
                events_list.append(line)
                event_lines.append(line_number)
            if isinstance(record, dict):
                fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
                if fields.get("message") == "Type registry loaded successfully":
                    latest_session_start = line_number
                    version = fields.get("version")
                    latest_session_version = str(version) if version is not None else None
        if latest_session_start:
            current = [(line, number) for line, number in zip(errors_list, error_lines) if number > latest_session_start]
            errors_list = [line for line, _ in current]
            error_lines = [number for _, number in current]
        errors = tuple(errors_list)
        events = tuple(events_list)[-20:]
        if errors and event_lines and event_lines[-1] > error_lines[-1]:
            status = "degraded"
        elif errors:
            status = "failed"
        elif events:
            status = "healthy"
        else:
            status = "started"
        build_match = BUILD_RE.search(latest_session_version or "")
        build = build_match.group(1) if build_match else None
        loader_api_version = None
        for line_number in range(len(lines), latest_session_start, -1):
            line = lines[line_number - 1]
            try:
                record = json.loads(line)
            except (TypeError, ValueError):
                continue
            if not isinstance(record, dict):
                continue
            fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
            if fields.get("message") == LOADER_API_REPORTED_MESSAGE:
                value = fields.get("api_version")
                if isinstance(value, str) and LOADER_API_RE.fullmatch(value.strip()):
                    loader_api_version = value.strip()
                break
        return RuntimeHealth(status, path, build, loader_api_version, events, errors)


@dataclass(frozen=True)
class ModuleIssue:
    module_id: str
    severity: str
    message: str


@dataclass
class ModuleGraph:
    modules: dict[str, dict[str, Any]]
    order: list[str]
    issues: list[ModuleIssue] = field(default_factory=list)


class ModuleGraphService:
    """Load, validate, order, and audit Control Center module manifests."""

    def __init__(self, modules_dir: Path, loader_api_version: str | None = None):
        self.modules_dir = Path(modules_dir)
        self.loader_api_version = str(loader_api_version).strip() if loader_api_version else None

    def build(self, enabled: set[str] | None = None, *, strict_metadata: bool = False) -> ModuleGraph:
        modules: dict[str, dict[str, Any]] = {}
        issues: list[ModuleIssue] = []
        for manifest_path in sorted(self.modules_dir.glob("*/module.json")):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                issues.append(ModuleIssue(manifest_path.parent.name, "error", f"Invalid manifest: {exc}"))
                continue
            module_id = str(manifest.get("id") or manifest_path.parent.name)
            if module_id in modules:
                issues.append(ModuleIssue(module_id, "error", "Duplicate module identifier."))
                continue
            if strict_metadata:
                declared_state = manifest.get("feature_state")
                if not isinstance(declared_state, str) or declared_state.strip().lower() not in FEATURE_STATES:
                    issues.append(ModuleIssue(
                        module_id, "error",
                        "Module must declare a valid feature_state (stable, experimental, research-only, or disabled).",
                    ))
            required_api = manifest.get("required_loader_api_version")
            if required_api is not None and (enabled is None or module_id in enabled):
                if not isinstance(required_api, str) or not LOADER_API_RE.fullmatch(required_api.strip()):
                    issues.append(ModuleIssue(module_id, "error",
                        f"Unsupported required_loader_api_version constraint: {required_api}."))
                    manifest["_path"] = str(manifest_path.parent)
                    modules[module_id] = manifest
                    continue
                compatibility = (self._loader_api_satisfies(self.loader_api_version, str(required_api))
                                 if self.loader_api_version else None)
                if compatibility is False:
                    issues.append(ModuleIssue(module_id, "error",
                        f"Module requires loader API {required_api} (current {self.loader_api_version})."))
                elif compatibility is None:
                    reason = (f"Unsupported required_loader_api_version constraint: {required_api}."
                              if self.loader_api_version else
                              f"Cannot confirm required loader API {required_api}; no version was reported by EML.")
                    issues.append(ModuleIssue(module_id, "warning", reason))
            manifest["_path"] = str(manifest_path.parent)
            modules[module_id] = manifest

        requested = set(modules) if enabled is None else set(enabled)
        if enabled is not None:
            for missing_id in sorted(requested - set(modules)):
                issues.append(ModuleIssue(missing_id, "error", "Profile requests a module that is not installed."))
        selected = requested & set(modules)
        order: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(module_id: str) -> None:
            if module_id in visited or module_id not in selected:
                return
            if module_id in visiting:
                issues.append(ModuleIssue(module_id, "error", "Circular module dependency."))
                return
            visiting.add(module_id)
            manifest = modules[module_id]
            dependencies = manifest.get("dependencies", [])
            if isinstance(dependencies, dict):
                dependencies = list(dependencies)
            elif not isinstance(dependencies, list):
                issues.append(ModuleIssue(module_id, "error", "Dependencies must be an array."))
                dependencies = []
            dependency_ids_seen: set[str] = set()
            for dependency in dependencies:
                raw_dep_id = dependency.get("id") if isinstance(dependency, dict) else dependency
                dep_id = str(raw_dep_id).strip() if raw_dep_id is not None else ""
                if not dep_id:
                    issues.append(ModuleIssue(module_id, "error", "Dependency ID cannot be empty."))
                    continue
                if dep_id in dependency_ids_seen:
                    issues.append(ModuleIssue(module_id, "error", f"Duplicate dependency declaration: {dep_id}."))
                    continue
                dependency_ids_seen.add(dep_id)
                if dep_id == module_id:
                    issues.append(ModuleIssue(module_id, "error", "Module cannot depend on itself."))
                    continue
                if dep_id not in modules:
                    issues.append(ModuleIssue(module_id, "error", f"Missing dependency: {dep_id}"))
                elif dep_id not in selected:
                    issues.append(ModuleIssue(module_id, "error", f"Dependency is disabled: {dep_id}"))
                else:
                    if isinstance(dependency, dict) and dependency.get("version"):
                        constraint = str(dependency["version"]).strip()
                        actual = str(modules[dep_id].get("version", "")).strip()
                        result = self._version_satisfies(actual, constraint)
                        if result is False:
                            issues.append(ModuleIssue(module_id, "error", f"Dependency {dep_id} does not satisfy version {constraint} (found {actual or 'unknown'})."))
                        elif result is None:
                            issues.append(ModuleIssue(module_id, "error", f"Unsupported dependency version constraint: {constraint}."))
                    visit(dep_id)
            conflicts = manifest.get("conflicts", [])
            if not isinstance(conflicts, list):
                issues.append(ModuleIssue(module_id, "error", "Conflicts must be an array."))
                conflicts = []
            conflict_ids_seen: set[str] = set()
            for conflict in conflicts:
                raw_conflict_id = conflict.get("id") if isinstance(conflict, dict) else conflict
                conflict_id = str(raw_conflict_id).strip() if raw_conflict_id is not None else ""
                if not conflict_id:
                    issues.append(ModuleIssue(module_id, "error", "Conflict ID cannot be empty."))
                    continue
                if conflict_id in conflict_ids_seen:
                    issues.append(ModuleIssue(module_id, "error", f"Duplicate conflict declaration: {conflict_id}."))
                    continue
                conflict_ids_seen.add(conflict_id)
                if conflict_id == module_id:
                    issues.append(ModuleIssue(module_id, "error", "Module cannot conflict with itself."))
                    continue
                if conflict_id in selected:
                    issues.append(ModuleIssue(module_id, "error", f"Conflicts with enabled module: {conflict_id}"))
            visiting.remove(module_id)
            visited.add(module_id)
            order.append(module_id)

        def priority(module_id: str) -> tuple[int, str]:
            value = modules[module_id].get("load_order", 0)
            try:
                value = int(value)
            except (TypeError, ValueError):
                value = 0
            return value, module_id

        for module_id in sorted(selected, key=priority):
            visit(module_id)
        return ModuleGraph(modules, order, issues)

    @staticmethod
    def _version_satisfies(version: str, constraint: str) -> bool | None:
        """Evaluate the small SemVer constraint subset accepted by manifests."""
        match = VERSION_CONSTRAINT_RE.fullmatch(constraint)
        actual = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
        if not match or not actual:
            return None
        expected = tuple(int(match.group(index)) for index in (2, 3, 4))
        found = tuple(int(part) for part in actual.groups())
        operator = (match.group(1) or "=").replace(" ", "")
        if operator == "~":
            return found[:2] == expected[:2] and found >= expected
        return {"=": found == expected, ">=": found >= expected, "<=": found <= expected,
                ">": found > expected, "<": found < expected}[operator]

    @staticmethod
    def _loader_api_satisfies(version: str, constraint: str) -> bool | None:
        actual = LOADER_API_RE.fullmatch(str(version).strip())
        required = LOADER_API_RE.fullmatch(str(constraint).strip())
        if not actual or not required:
            return None
        found = (int(actual.group(2)), int(actual.group(3)))
        expected = (int(required.group(2)), int(required.group(3)))
        operator = (required.group(1) or "=").replace(" ", "")
        if operator == "~":
            return found[0] == expected[0] and found >= expected
        return {"=": found == expected, ">=": found >= expected, "<=": found <= expected,
                ">": found > expected, "<": found < expected}[operator]

    @staticmethod
    def explain(graph: ModuleGraph) -> list[dict[str, Any]]:
        """Return a stable, user-facing explanation of graph decisions."""
        positions = {module_id: index for index, module_id in enumerate(graph.order)}
        issue_map: dict[str, list[str]] = {}
        for issue in graph.issues:
            issue_map.setdefault(issue.module_id, []).append(f"{issue.severity}: {issue.message}")
        rows = []
        for module_id, manifest in sorted(graph.modules.items()):
            dependencies = manifest.get("dependencies", [])
            if isinstance(dependencies, dict):
                dependencies = list(dependencies)
            if not isinstance(dependencies, list):
                dependencies = []
            dependency_ids = [str(item.get("id")) if isinstance(item, dict) else str(item) for item in dependencies]
            dependency_details = []
            for item in dependencies:
                dependency_id = str(item.get("id")) if isinstance(item, dict) else str(item)
                dependency_details.append({
                    "id": dependency_id,
                    "requested_version": item.get("version") if isinstance(item, dict) else None,
                    "installed_version": graph.modules.get(dependency_id, {}).get("version"),
                })
            rows.append({
                "id": module_id,
                "enabled": module_id in positions,
                "load_index": positions.get(module_id),
                "declared_load_order": manifest.get("load_order", 0),
                "feature_state": feature_state(manifest),
                "dependencies": dependency_ids,
                "dependency_details": dependency_details,
                "conflicts": [str(item.get("id")) if isinstance(item, dict) else str(item) for item in (manifest.get("conflicts", []) if isinstance(manifest.get("conflicts", []), list) else [])],
                "issues": issue_map.get(module_id, []),
            })
        return rows


FEATURE_STATES = ("stable", "experimental", "research-only", "disabled")


def feature_state(manifest: dict[str, Any]) -> str:
    """Return an explicit maturity state, defaulting conservatively."""
    state = str(manifest.get("feature_state", "")).lower()
    if state in FEATURE_STATES:
        return state
    if manifest.get("research_only") or manifest.get("type") == "kfc_resource_patch":
        return "research-only"
    return "experimental"


@dataclass(frozen=True)
class PlatformStatus:
    game: GameBuild
    runtime: RuntimeHealth
    graph: ModuleGraph
    loader_api_version: str | None = None


class PlatformService:
    """Facade consumed by future dashboard pages and diagnostics exports."""

    def __init__(self, base_dir: Path, game_dir: Path | None = None):
        self.base_dir = Path(base_dir)
        self.game_dir = Path(game_dir) if game_dir else None
        self.builds = GameBuildDetector()
        self.health = RuntimeHealthService()
        self.modules = ModuleGraphService(self.base_dir / "modules", loader_api_version=None)

    def status(self, enabled: set[str] | None = None) -> PlatformStatus:
        game = self.builds.detect(self.game_dir) if self.game_dir else GameBuild(None, None, Path())
        runtime = self.health.inspect(self.game_dir) if self.game_dir else RuntimeHealth("unknown", None)
        api_version = runtime.loader_api_version
        self.modules.loader_api_version = api_version
        return PlatformStatus(game, runtime, self.modules.build(enabled), api_version)

