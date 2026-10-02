"""Safe package discovery and profile-scoped mod enablement."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

from .profiles import Profile, ProfileService
from .compatibility import CompatibilityState, evaluate


MAX_ARCHIVE_ENTRIES = 2048
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
DEPLOYMENT_MARKER = ".embervault-managed.json"
DEPLOYMENT_MARKER_VERSION = 1


@dataclass(frozen=True)
class PackageManifest:
    id: str
    name: str
    version: str
    author: str = "Unknown"
    description: str = ""
    package_type: str = "mod"
    required_builds: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    path: Path | None = None

    @classmethod
    def from_file(cls, path: Path) -> "PackageManifest":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_data(data, path.parent)

    @classmethod
    def from_data(cls, data: dict, directory: Path) -> "PackageManifest":
        if not isinstance(data, dict):
            raise ValueError("Package manifest must be an object")
        for field_name in ("id", "name", "version"):
            if not isinstance(data.get(field_name), str) or not data[field_name].strip():
                raise ValueError(f"Package {field_name} must be a non-empty string")
        package_id = str(data["id"])
        if not package_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for char in package_id):
            raise ValueError("Package id contains invalid characters")
        raw_required_builds = data.get("required_builds", [])
        raw_dependencies = data.get("dependencies", [])
        if not isinstance(raw_required_builds, list) or not isinstance(raw_dependencies, list):
            raise ValueError("Package required_builds and dependencies must be arrays")
        if any(not isinstance(value, str) for value in [*raw_required_builds, *raw_dependencies]):
            raise ValueError("Package build and dependency entries must be strings")
        for field_name in ("author", "description"):
            if field_name in data and not isinstance(data[field_name], str):
                raise ValueError(f"Package {field_name} must be a string")
        package_type = data.get("package_type", "mod")
        if not isinstance(package_type, str) or not package_type.strip():
            raise ValueError("Package type must be a non-empty string")
        required_builds = tuple(value.strip() for value in raw_required_builds)
        if any(not value for value in required_builds):
            raise ValueError("Package required_builds entries must be non-empty strings")
        if len(set(required_builds)) != len(required_builds):
            raise ValueError("Package required_builds must be unique")
        dependencies = tuple(value.strip() for value in raw_dependencies)
        if any(not dependency or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for char in dependency) for dependency in dependencies):
            raise ValueError("Package dependency contains invalid characters")
        if len(set(dependencies)) != len(dependencies):
            raise ValueError("Package dependencies must be unique")
        if package_id in dependencies:
            raise ValueError("Package cannot depend on itself")
        return cls(
            id=package_id, name=data["name"].strip(), version=data["version"].strip(),
            author=str(data.get("author", "Unknown")), description=str(data.get("description", "")),
            package_type=package_type.strip(),
            required_builds=required_builds,
            dependencies=dependencies,
            path=Path(directory),
        )


@dataclass(frozen=True)
class DeploymentAction:
    package_id: str
    source: Path
    destination: Path
    status: str
    reason: str = ""
    profile_id: str = ""
    compatibility_state: str = "unknown"


class PackageService:
    """Discover packages and change only profile enablement state."""

    def __init__(self, root: Path, profiles: ProfileService):
        self.root = Path(root)
        self.directory = self.root / "packages"
        source_directory = Path(__file__).resolve().parents[1] / "packages"
        installed_directory = Path(sys.prefix) / "packages"
        self.seed_directory = source_directory if source_directory.is_dir() else installed_directory
        self.profiles = profiles
        self._packages: dict[str, PackageManifest] = {}

    def discover(self) -> dict[str, PackageManifest]:
        self._packages = {}
        directories = [self.seed_directory]
        if self.directory.is_dir():
            directories.append(self.directory)
        for directory in directories:
            if not directory.is_dir():
                continue
            for manifest_path in sorted(directory.glob("*/package.json")):
                try:
                    if manifest_path.parent.is_symlink():
                        continue
                    manifest = PackageManifest.from_file(manifest_path)
                    if manifest.id in self._packages:
                        if directory == self.directory:
                            self._packages[manifest.id] = manifest
                        continue
                    self._packages[manifest.id] = manifest
                except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                    continue
        return dict(self._packages)

    def list(self) -> list[PackageManifest]:
        return list(self.discover().values())

    def inspect_external(self, mods_directory: Path) -> list[PackageManifest]:
        """Read external mod manifests without importing or changing them."""
        directory = Path(mods_directory)
        if not directory.is_dir():
            return []
        found: list[PackageManifest] = []
        for manifest_path in sorted(directory.glob("*/mod.json")):
            try:
                if manifest_path.parent.is_symlink() or any(item.is_symlink() for item in manifest_path.parent.rglob("*")):
                    continue
                raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                found.append(PackageManifest.from_data({
                    "id": raw.get("id"), "name": raw.get("name"), "version": raw.get("version"),
                    "author": raw.get("author", raw.get("publisher", "Unknown")),
                    "description": raw.get("description", "External game mod"),
                    "package_type": "mod", "required_builds": raw.get("required_builds", []),
                    "dependencies": raw.get("dependencies", []),
                }, manifest_path.parent))
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return found

    def get(self, package_id: str) -> PackageManifest | None:
        return self._packages.get(package_id)

    def is_enabled(self, profile: Profile, package_id: str) -> bool:
        return package_id in profile.enabled_packages

    def dependency_graph(self) -> dict[str, list[str]]:
        """Return a stable package-to-dependency graph for UI and tooling."""
        return {package.id: sorted(package.dependencies) for package in self.list()}

    def update_candidates(self, available: list[dict] | None = None) -> list[dict]:
        """Compare installed package versions with a trusted metadata list."""
        available = available or []
        remote = {item.get("id"): item for item in available if isinstance(item, dict) and isinstance(item.get("id"), str)}
        result = []
        for package in self.list():
            candidate = remote.get(package.id)
            if not candidate or not isinstance(candidate.get("version"), str):
                continue
            if self._version_key(candidate["version"]) > self._version_key(package.version):
                result.append({"id": package.id, "installed": package.version,
                               "available": candidate["version"], "managed": bool(package.path)})
        return result

    @staticmethod
    def _version_key(version: str) -> tuple:
        parts = []
        for value in str(version).split("."):
            digits = "".join(char for char in value if char.isdigit())
            parts.append(int(digits or 0))
        return tuple((parts + [0, 0, 0])[:3])

    def compare_profiles(self, left: Profile, right: Profile) -> dict[str, list[str]]:
        left_ids, right_ids = set(left.enabled_packages), set(right.enabled_packages)
        return {"only_left": sorted(left_ids - right_ids),
                "only_right": sorted(right_ids - left_ids),
                "shared": sorted(left_ids & right_ids)}

    def batch_set_enabled(self, profile: Profile, package_ids: list[str], enabled: bool,
                          detected_build: str | None = None) -> Profile:
        """Validate a batch completely before changing profile state."""
        if not isinstance(package_ids, list) or any(not isinstance(item, str) or not item.strip() for item in package_ids):
            raise ValueError("Package batch must contain non-empty IDs")
        requested = list(dict.fromkeys(item.strip() for item in package_ids))
        candidate = Profile(**{**profile.__dict__, "enabled_packages": list(profile.enabled_packages)})
        for package_id in requested:
            candidate = self.set_enabled(candidate, package_id, enabled, detected_build)
        return candidate

    def set_enabled(self, profile: Profile, package_id: str, enabled: bool, detected_build: str | None = None) -> Profile:
        if package_id not in self._packages:
            raise ValueError(f"Unknown package: {package_id}")
        if enabled:
            compatibility = evaluate(required_builds=list(self._packages[package_id].required_builds), detected_build=detected_build)
            if compatibility.state == CompatibilityState.INCOMPATIBLE:
                raise ValueError("Package is incompatible with the detected game build")
            missing = [
                dependency for dependency in self._packages[package_id].dependencies
                if dependency not in self._packages or not self.is_enabled(profile, dependency)
            ]
            if missing:
                raise ValueError(f"Enable package dependencies first: {', '.join(missing)}")
        else:
            dependents = [
                item.name for item in self._packages.values()
                if package_id in item.dependencies and self.is_enabled(profile, item.id)
            ]
            if dependents:
                raise ValueError(f"Disable dependent packages first: {', '.join(dependents)}")
        enabled_packages = set(profile.enabled_packages)
        if enabled:
            enabled_packages.add(package_id)
        else:
            enabled_packages.discard(package_id)
        updated = Profile(**{**profile.__dict__, "enabled_packages": sorted(enabled_packages)})
        self.profiles.save(updated)
        return updated

    def install_from_directory(self, source: Path) -> PackageManifest:
        """Import a package directory after validating its manifest."""
        source = Path(source)
        manifest_path = source / "package.json"
        external_manifest_path = source / "mod.json"
        if not source.is_dir() or (not manifest_path.is_file() and not external_manifest_path.is_file()):
            raise ValueError("Package folder must contain package.json or mod.json")
        if any(item.is_symlink() for item in [source, *source.rglob("*")]):
            raise ValueError("Package folder contains an unsafe symlink")
        external = not manifest_path.is_file()
        if external:
            try:
                raw = json.loads(external_manifest_path.read_text(encoding="utf-8"))
                manifest_data = {
                    "id": raw.get("id"), "name": raw.get("name"), "version": raw.get("version"),
                    "author": raw.get("author", raw.get("publisher", "Unknown")),
                    "description": raw.get("description", "Imported external Enshrouded mod"),
                    "package_type": "mod", "required_builds": raw.get("required_builds", []),
                    "dependencies": raw.get("dependencies", []),
                }
                manifest = PackageManifest.from_data(manifest_data, external_manifest_path.parent)
            except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError("External mod.json is invalid") from exc
        else:
            manifest = PackageManifest.from_file(manifest_path)
        if manifest.id in self._packages or any(item.id == manifest.id for item in self.list()):
            raise ValueError(f"Package already installed: {manifest.id}")
        target = self.directory / manifest.id
        target.parent.mkdir(parents=True, exist_ok=True)
        # Stage outside the managed directory so a failed copy cannot leave a
        # package that discovery might mistake for an installed package.
        with tempfile.TemporaryDirectory(prefix="embervault-package-stage-", dir=self.directory.parent) as temp:
            staged = Path(temp) / manifest.id
            shutil.copytree(source, staged)
            if external:
                (staged / "package.json").write_text(json.dumps({
                    "id": manifest.id, "name": manifest.name, "version": manifest.version,
                    "author": manifest.author, "description": manifest.description,
                    "package_type": manifest.package_type,
                    "required_builds": list(manifest.required_builds),
                    "dependencies": list(manifest.dependencies),
                }, indent=2) + "\n", encoding="utf-8")
            shutil.move(str(staged), str(target))
        self._packages[manifest.id] = PackageManifest.from_file(target / "package.json")
        return self._packages[manifest.id]

    def stage_upgrade(self, source: Path) -> dict:
        """Validate and stage an upgrade without replacing the installed package."""
        source = Path(source)
        incoming = PackageManifest.from_file(source / "package.json")
        current = self.get(incoming.id)
        if not current:
            raise ValueError("Upgrade target is not an installed managed package")
        if self._version_key(incoming.version) <= self._version_key(current.version):
            raise ValueError("Upgrade version must be newer than the installed version")
        if any(item.is_symlink() for item in [source, *source.rglob("*")]):
            raise ValueError("Upgrade source contains an unsafe symlink")
        staging = self.root / "package-upgrades" / incoming.id / incoming.version
        if staging.exists():
            shutil.rmtree(staging)
        staging.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, staging)
        return {"package_id": incoming.id, "installed_version": current.version,
                "staged_version": incoming.version, "staged_path": str(staging),
                "requires_review": True, "replacement_performed": False}

    def install_from_archive(self, archive: Path) -> PackageManifest:
        archive = Path(archive)
        if not archive.is_file() or archive.suffix.lower() != ".zip":
            raise ValueError("Package archive must be a .zip file")
        with tempfile.TemporaryDirectory(prefix="embervault-package-") as temp:
            staging = Path(temp)
            with zipfile.ZipFile(archive) as bundle:
                members = bundle.infolist()
                if len(members) > MAX_ARCHIVE_ENTRIES:
                    raise ValueError("Package archive contains too many entries")
                if sum(member.file_size for member in members) > MAX_ARCHIVE_BYTES:
                    raise ValueError("Package archive is too large to import safely")
                member_names: set[str] = set()
                for member in members:
                    normalized_name = member.filename.replace("\\", "/")
                    if normalized_name in member_names:
                        raise ValueError("Package archive contains duplicate paths")
                    member_names.add(normalized_name)
                    unix_mode = (member.external_attr >> 16) & 0o170000
                    if unix_mode == 0o120000:
                        raise ValueError("Package archive contains an unsafe symlink")
                    target = (staging / member.filename).resolve()
                    windows_member = PureWindowsPath(member.filename)
                    if (windows_member.is_absolute() or ".." in windows_member.parts
                            or (staging.resolve() not in target.parents and target != staging.resolve())):
                        raise ValueError("Package archive contains an unsafe path")
                bundle.extractall(staging)
            candidates = [staging, *[item for item in staging.iterdir() if item.is_dir()]]
            package_roots = [item for item in candidates
                             if (item / "package.json").is_file() or (item / "mod.json").is_file()]
            if not package_roots:
                raise ValueError("Package archive must contain package.json or mod.json")
            if len(package_roots) > 1:
                raise ValueError("Package archive contains multiple package roots")
            return self.install_from_directory(package_roots[0])

    def remove(self, package_id: str) -> None:
        package = self.get(package_id)
        if not package or not package.path:
            raise ValueError(f"Unknown installed package: {package_id}")
        if any(package_id in profile.enabled_packages for profile in self.profiles.list()):
            raise ValueError("Disable the package in every profile before removing it")
        dependents = [item.name for item in self._packages.values() if package_id in item.dependencies]
        if dependents:
            raise ValueError(f"Remove dependent packages first: {', '.join(dependents)}")
        managed_path = self.directory / package_id
        if not managed_path.is_dir():
            raise ValueError("Seed packages cannot be removed from the repository")
        if managed_path.is_symlink():
            raise ValueError("Refusing to remove a symlinked package directory")
        shutil.rmtree(managed_path)
        self._packages.pop(package_id, None)

    def deployment_plan(self, profile: Profile, game_directory: Path, *, detected_build: str | None = None, context=None) -> list[DeploymentAction]:
        """Describe enabled package destinations without changing the game."""
        if context is not None and context.profile_id != profile.id:
            raise ValueError("Package deployment profile does not match integration context")
        destination_root = Path(game_directory) / "mods"
        actions: list[DeploymentAction] = []
        for package_id in profile.enabled_packages:
            package = self._packages.get(package_id)
            if not package or not package.path or not package.path.is_dir():
                actions.append(DeploymentAction(package_id, Path(), destination_root / package_id,
                                                "missing", "Package is not installed", profile.id))
                continue
            compatibility = evaluate(required_builds=list(package.required_builds), detected_build=detected_build)
            if compatibility.state == CompatibilityState.INCOMPATIBLE:
                actions.append(DeploymentAction(package_id, package.path, destination_root / package_id,
                                                "incompatible", "; ".join(compatibility.reasons), profile.id,
                                                compatibility.state.value))
                continue
            if package.path.is_symlink() or any(item.is_symlink() for item in package.path.rglob("*")):
                actions.append(DeploymentAction(package_id, package.path, destination_root / package_id,
                                                "unsafe", "Package source contains a symlink", profile.id, compatibility.state.value))
                continue
            if package.package_type != "mod":
                actions.append(DeploymentAction(package_id, package.path, destination_root / package_id,
                                                "unsupported", "Only package_type 'mod' can deploy to game mods", profile.id, compatibility.state.value))
                continue
            target = destination_root / package_id
            if target.exists():
                actions.append(DeploymentAction(package_id, package.path, target, "conflict",
                                                "Destination already exists", profile.id, compatibility.state.value))
            else:
                actions.append(DeploymentAction(package_id, package.path, target, "ready", "", profile.id, compatibility.state.value))
        return actions

    def deploy_ready(self, profile: Profile, game_directory: Path) -> list[DeploymentAction]:
        """Install enabled packages only when the complete plan is conflict-free."""
        if not Path(game_directory).is_dir():
            raise ValueError("Configured game directory does not exist")
        plan = self.deployment_plan(profile, game_directory)
        if any(item.status != "ready" for item in plan):
            raise ValueError("Resolve deployment conflicts before installing packages")
        created: list[Path] = []
        current_destination: Path | None = None
        try:
            for item in plan:
                current_destination = item.destination
                item.destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(item.source, item.destination)
                created.append(item.destination)
                (item.destination / DEPLOYMENT_MARKER).write_text(json.dumps({
                    "marker_version": DEPLOYMENT_MARKER_VERSION,
                    "package_id": item.package_id, "package_version": self._packages[item.package_id].version,
                    "managed_by": "embervault-control-center",
                }, indent=2) + "\n", encoding="utf-8")
            return plan
        except (OSError, shutil.Error) as exc:
            cleanup = list(created)
            if current_destination is not None and current_destination not in cleanup:
                cleanup.append(current_destination)
            for destination in reversed(cleanup):
                if destination.is_dir() and not destination.is_symlink():
                    shutil.rmtree(destination, ignore_errors=True)
            raise OSError("Package deployment failed; new destinations were removed") from exc

    def inspect_deployments(self, game_directory: Path) -> list[DeploymentAction]:
        """Inspect game mod folders without changing managed or external content."""
        mods = Path(game_directory) / "mods"
        if not mods.is_dir():
            return []
        findings: list[DeploymentAction] = []
        for destination in sorted(mods.iterdir()):
            if not destination.is_dir() or destination.is_symlink():
                continue
            marker = destination / DEPLOYMENT_MARKER
            if not marker.is_file():
                findings.append(DeploymentAction(destination.name, Path(), destination, "external",
                                                 "No EmberVault ownership marker"))
                continue
            try:
                metadata = json.loads(marker.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                findings.append(DeploymentAction(destination.name, Path(), destination, "unsafe",
                                                 "Ownership marker is unreadable"))
                continue
            if (metadata.get("marker_version") != DEPLOYMENT_MARKER_VERSION
                    or metadata.get("package_id") != destination.name
                    or metadata.get("managed_by") != "embervault-control-center"):
                findings.append(DeploymentAction(destination.name, Path(), destination, "unsafe",
                                                 "Ownership marker is invalid"))
                continue
            findings.append(DeploymentAction(destination.name, Path(), destination, "managed",
                                             f"EmberVault deployment v{metadata.get('package_version', 'unknown')}"))
        return findings

    def undeploy(self, package_id: str, game_directory: Path) -> None:
        """Remove only a destination bearing EmberVault's ownership marker."""
        destination = Path(game_directory) / "mods" / package_id
        marker = destination / DEPLOYMENT_MARKER
        if not destination.is_dir() or destination.is_symlink():
            raise ValueError("Managed deployment destination does not exist")
        try:
            metadata = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Refusing to remove an unmarked mod destination") from exc
        if (metadata.get("marker_version") != DEPLOYMENT_MARKER_VERSION
                or metadata.get("package_id") != package_id
                or metadata.get("managed_by") != "embervault-control-center"):
            raise ValueError("Refusing to remove a destination not owned by EmberVault")
        shutil.rmtree(destination)
