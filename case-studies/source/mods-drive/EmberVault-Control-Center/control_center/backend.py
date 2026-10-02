"""Qt-facing adapter for the first Control Center vertical slice."""
from __future__ import annotations

from pathlib import Path
import json
import subprocess
import re
from datetime import datetime

from core.application import EmbervaultRuntime
from core.game_detection import GameDetector
from core.profiles import ProfileService
from core.save_manager import SaveManagerError, SaveManagerService
from core.save_workflow import SaveWorkflowService
from core.settings import SettingsService
from core.operations import OperationStatus
from core.compatibility import evaluate
from core.modules import LaunchContext
from core.promotion import PromotionEvidence

MAX_WORKER_OUTPUT = 1024 * 1024

try:
    from PySide6.QtCore import QObject, Property, Signal, Slot
except ImportError:  # Keep core imports and headless checks usable without Qt.
    QObject = object  # type: ignore[misc,assignment]
    class _Signal:
        def emit(self):
            return None
    Signal = lambda *args, **kwargs: _Signal()  # type: ignore[assignment]
    Property = lambda _type, notify=None: (lambda fn: property(fn))  # type: ignore[assignment]
    def Slot(*args, **kwargs):  # type: ignore[no-redef]
        return lambda fn: fn


class ControlCenterBackend(QObject):
    stateChanged = Signal() if QObject is not object else None

    def __init__(self, data_root: Path, parent=None, runtime: EmbervaultRuntime | None = None):
        super().__init__(parent) if QObject is not object else super().__init__()
        self.data_root = Path(data_root)
        self.settings_service = SettingsService(self.data_root)
        self.settings = self.settings_service.load()
        self.profile_service = ProfileService(self.data_root)
        self.profiles = self.profile_service.ensure_defaults()
        self.save_manager = runtime.saves if runtime else SaveManagerService(self.data_root)
        self.save_workflow = runtime.save_workflow if runtime else None
        self.operations = runtime.operations if runtime else None
        self.logs = runtime.logs if runtime else None
        self.modules = runtime.modules if runtime else None
        self.packages = runtime.packages if runtime else None
        self.troubleshooter = runtime.troubleshooter if runtime else None
        self.game_settings = runtime.game_settings if runtime else None
        self.research = runtime.research if runtime else None
        self.knowledge = runtime.knowledge if runtime else None
        self.catalog = runtime.catalog if runtime else None
        self.community_sync = runtime.community_sync if runtime else None
        self.release = runtime.release if runtime else None
        self.content = runtime.content if runtime else None
        self.trainer = runtime.trainer if runtime else None
        self.tuning_adapter = runtime.tuning_adapter if runtime else None
        self.characters = runtime.characters if runtime else None
        self.risk = runtime.risk if runtime else None
        self.launcher = runtime.launcher if runtime else None
        self.promotion = runtime.promotion if runtime else None
        self.migrations = runtime.migrations if runtime else None
        self._migration_report = None
        self.detector = runtime.game if runtime else GameDetector()
        self._game_status = "Not configured"
        self._build = "Unknown build"
        self._profile_name = self.profiles[0].name if self.profiles else "No profile"
        self._safety = "No backup required"
        self._save_directory = ""
        self._last_save_message = "No save selected"
        self._selected_backup_id = ""
        self._restore_preview_backup_id = ""
        self._deployment_plan_signature = None
        self._restore_preview = "No restore selected"
        self._selected_profile_id = self.profiles[0].id if self.profiles else ""
        self._knowledge_query = ""
        self._research_query = ""
        self._staged_adapter_package = None
        self._staged_adapter_operation_id = None
        self._adapter_deployed = False
        self._adapter_verified = False
        self._adapter_deployed_at = None
        self._restore_adapter_operation_state()

    def _restore_adapter_operation_state(self) -> None:
        """Recover adapter lifecycle state from durable operation history."""
        if not self.operations:
            return
        for operation in self.operations.list_recent(limit=200):
            if operation.status != OperationStatus.SUCCEEDED:
                continue
            if operation.operation_type == "tuning-adapter-rollback":
                self._staged_adapter_package = None
                self._staged_adapter_operation_id = None
                self._adapter_deployed = False
                self._adapter_verified = False
                return
            if operation.operation_type == "tuning-adapter-verify":
                self._adapter_verified = True
                self._adapter_deployed = True
                continue
            if operation.operation_type == "tuning-adapter-deploy":
                self._adapter_deployed = True
                try:
                    self._adapter_deployed_at = datetime.fromisoformat(operation.started_at).timestamp()
                except ValueError:
                    self._adapter_deployed_at = None
                continue
            if operation.operation_type == "tuning-adapter-stage":
                match = re.search(r" at (.+)$", operation.message)
                if match:
                    staged = Path(match.group(1))
                    if staged.is_dir():
                        self._staged_adapter_package = staged
                        self._staged_adapter_operation_id = operation.id
                return

    @Property(str, notify=stateChanged)
    def gameStatus(self):
        return self._game_status

    @Property(str, notify=stateChanged)
    def gameBuild(self):
        return self._build

    @Property(str, notify=stateChanged)
    def profileName(self):
        return self._profile_name

    @Property(str, notify=stateChanged)
    def safetySummary(self):
        return self._safety

    @Property(str, notify=stateChanged)
    def saveSummary(self):
        count = len(self.save_manager.list_backups())
        return f"{count} verified backup{'s' if count != 1 else ''}"

    @Property("QStringList", notify=stateChanged)
    def workspaceSummary(self):
        """Expose the current workspace footprint without exposing private records."""
        return [
            f"Research · {len(self.research.list()) if self.research else 0} records",
            f"Knowledge · {len(self.knowledge.entries()) if self.knowledge else 0} entries",
            f"Content · {len(self.content.list()) if self.content else 0} projects",
            f"Trainer · {len(self.trainer.list()) if self.trainer else 0} plans",
            f"Promotions · {len(self.promotion.decisions()) if self.promotion else 0} decisions",
            f"Migration · {'ready' if self.migrations else 'unavailable'}",
        ]

    @Property("QStringList", notify=stateChanged)
    def migrationPreview(self):
        if not self.migrations:
            return ["Migration service unavailable"]
        return [f"{item.status.upper()} · {item.path} · {item.reason or str(item.records) + ' record(s)'}"
                for item in self.migrations.preview()]

    @Property(str, notify=stateChanged)
    def migrationReport(self):
        return self._migration_report or "No migration has been applied. Preview first."

    @Slot()
    def applyMigration(self):
        if not self.migrations:
            return
        operation = self.operations.start("data-migration", profile_id=self._selected_profile_id,
                                          capability="migration", capability_state="staged",
                                          recovery_expectation="migration backup and rollback available") if self.operations else None
        try:
            report = self.migrations.apply()
            self._migration_report = f"Migration backup: {report['backup']} · {len(report['items'])} item(s)"
            if operation and self.operations: self.operations.finish(operation, OperationStatus.SUCCEEDED, self._migration_report)
        except (OSError, ValueError, TypeError) as exc:
            self._migration_report = str(exc)
            if operation and self.operations: self.operations.finish(operation, OperationStatus.FAILED, str(exc))
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def promotionSummary(self):
        if not self.promotion:
            return []
        return [f"{item['evidence'].get('capability_id', 'unknown')} → {item.get('target_state', 'unknown')}"
                for item in self.promotion.decisions()[-20:]]

    @Slot(str, result=str)
    def reviewCapability(self, capability_id):
        """Return a read-only governance explanation for the selected capability."""
        if not self.promotion:
            return "Promotion service unavailable"
        decisions = [item for item in self.promotion.decisions()
                     if item.get("evidence", {}).get("capability_id") == capability_id]
        if not decisions:
            missing = self.promotion.missing_requirements(None)
            return f"{capability_id}: no promotion decision; missing: {', '.join(missing)}"
        latest = decisions[-1]
        evidence = latest.get("evidence", {})
        missing = self.promotion.missing_requirements(PromotionEvidence(
            evidence.get("capability_id", capability_id), evidence.get("current_build", ""),
            bool(evidence.get("reproducible")), bool(evidence.get("runtime_confirmed")),
            bool(evidence.get("recovery_tested")), bool(evidence.get("compatibility_documented")),
            evidence.get("owner", ""), bool(evidence.get("rollback_tested")),
            evidence.get("source_research_id", "")))
        return f"{capability_id}: {latest.get('target_state', 'unknown')}; " + ("all requirements met" if not missing else "missing: " + ", ".join(missing))

    @Property("QStringList", notify=stateChanged)
    def capabilityGovernance(self):
        """Sanitized capability readiness rows for the governance workspace."""
        rows = []
        decisions = self.promotion.decisions() if self.promotion else []
        latest = {item["evidence"].get("capability_id"): item for item in decisions}
        for manifest in (self.modules.discover().values() if self.modules else []):
            decision = latest.get(manifest.id) or latest.get(next(iter(manifest.capabilities), ""))
            state = decision.get("target_state", manifest.feature_state) if decision else manifest.feature_state
            evidence = decision.get("evidence", {}) if decision else {}
            labels = (("reproducible", "reproducibility"), ("runtime_confirmed", "runtime"),
                      ("recovery_tested", "recovery"), ("compatibility_documented", "compatibility"),
                      ("rollback_tested", "rollback"))
            missing = [label for key, label in labels if evidence.get(key) is not True]
            suffix = "missing: " + ", ".join(missing) if missing else "all evidence present"
            rows.append(f"{manifest.name} · {state} · {suffix} · owner: {evidence.get('owner', 'unassigned')}")
        if self.tuning_adapter:
            try:
                manifest = self.tuning_adapter.manifest()
            except ValueError:
                rows.append("EML runtime adapter · unavailable until adapter evidence is installed")
            else:
                decision = latest.get(manifest["id"])
                state = decision.get("target_state", manifest["feature_state"]) if decision else manifest["feature_state"]
                rows.append(f"{manifest['name']} · {state} · runtime adapter · rollback required")
        return rows

    @Property("QStringList", notify=stateChanged)
    def adapterGovernance(self):
        if not self.tuning_adapter:
            return ["No runtime adapter service available"]
        try:
            manifest = self.tuning_adapter.manifest()
        except ValueError:
            return ["EML adapter evidence is unavailable"]
        return [f"{manifest['id']} v{manifest['version']} · {manifest['loader']} API {manifest['loader_api_version']}",
                f"Build boundary: {manifest['game_build']}",
                f"Supported keys: {', '.join(manifest['supported_setting_keys'])}",
                "Future boundary: Shroudtopia requires an independent adapter contract"]

    @Slot(str, str, str, str, bool, bool, bool, bool, str, bool, result=str)
    def promoteCapability(self, capability_id, target_state, current_build, source_research_id,
                          reproducible, runtime_confirmed, recovery_tested,
                          compatibility_documented, owner, rollback_tested):
        if not self.promotion:
            return "Promotion service unavailable"
        operation = self.operations.start("capability-promotion", profile_id=self._selected_profile_id,
                                          capability="promotion", capability_state="plan-only",
                                          recovery_expectation="rollback evidence required") if self.operations else None
        try:
            decision = self.promotion.promote(PromotionEvidence(
                capability_id, current_build, reproducible, runtime_confirmed,
                recovery_tested, compatibility_documented, owner, rollback_tested,
                source_research_id), target_state)
            if operation:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Promoted {capability_id} to {target_state}")
            self.stateChanged.emit()
            return f"Promoted {capability_id} to {target_state}"
        except Exception as exc:
            if operation:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            return str(exc)

    @Property(bool, notify=stateChanged)
    def canBackup(self):
        return bool(self._save_directory)

    @Property(bool, notify=stateChanged)
    def canRestore(self):
        return bool(self._save_directory and self._selected_backup_id
                    and self._restore_preview_backup_id == self._selected_backup_id)

    @Property(bool, notify=stateChanged)
    def canDeploy(self):
        if not self.packages or not self.settings.game_path:
            return False
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            return False
        plan = self.packages.deployment_plan(profile, Path(self.settings.game_path))
        signature = (
            profile.id, str(Path(self.settings.game_path).resolve()),
            tuple((item.package_id, item.status, item.destination, item.reason) for item in plan),
        )
        return self._deployment_plan_signature == signature

    @Property(str, notify=stateChanged)
    def lastSaveMessage(self):
        return self._last_save_message

    @Property(str, notify=stateChanged)
    def tuningAdapterStatus(self):
        if not self.tuning_adapter:
            return "EML adapter unavailable"
        try:
            manifest = self.tuning_adapter.manifest()
            if self._adapter_verified:
                lifecycle = "verified"
            elif self._adapter_deployed:
                lifecycle = "deployed; launch verification pending"
            elif self._staged_adapter_package:
                lifecycle = "payload staged"
            else:
                lifecycle = "not staged"
            return f"EML {manifest['game_build']} · {manifest['feature_state']} · {', '.join(manifest['supported_setting_keys'])} · {lifecycle}"
        except ValueError as exc:
            return f"EML adapter blocked · {exc}"

    @Property(bool, notify=stateChanged)
    def canDeployTuningAdapter(self):
        return bool(self._staged_adapter_package and self.settings.game_path
                    and not self.detector.is_running())

    @Property(bool, notify=stateChanged)
    def canVerifyTuningAdapter(self):
        return bool(self._staged_adapter_operation_id and self._adapter_deployed and self.settings.game_path)

    @Property(bool, notify=stateChanged)
    def canRollbackTuningAdapter(self):
        return bool(self.settings.game_path and not self.detector.is_running())

    @Slot(result=str)
    def prepareTuningOperation(self):
        if not self.tuning_adapter or not self.game_settings:
            return "EML adapter unavailable"
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            return "Select a profile first"
        try:
            values = self.game_settings.values(profile)
            preview = self.tuning_adapter.prepare_operation(
                profile.profile_type,
                bool(self._selected_backup_id and self.save_manager.verify_backup(self._selected_backup_id)),
                self.detector.is_running(),
                values["base_crit_chance"],
                self.tuning_adapter.manifest()["evidence"]["test_value"],
            )
            self._last_save_message = (
                f"Prepared {preview['field']}: {preview['old_value']} → {preview['new_value']}; no game changes made"
            )
            self.stateChanged.emit()
            return self._last_save_message
        except (ValueError, KeyError, OSError) as exc:
            self._last_save_message = str(exc)
            self.stateChanged.emit()
            return self._last_save_message

    @Slot(result=str)
    def stageTuningAdapter(self):
        if not self.tuning_adapter or not self.game_settings:
            return "EML adapter unavailable"
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            return "Select a profile first"
        try:
            values = self.game_settings.values(profile)
            operation = self.operations.start("tuning-adapter-stage", profile_id=profile.id) if self.operations else None
            operation_id = operation.id if operation else "EV-ADAPTER-STAGE"
            source = Path(__file__).parents[1] / "packages" / "eml-tuning-adapter"
            staged = self.tuning_adapter.stage_package(
                source, self.data_root / "staging", values["base_crit_chance"], operation_id
            )
            self._staged_adapter_package = staged
            self._staged_adapter_operation_id = operation_id
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Staged EML adapter payload at {staged}")
            self._last_save_message = f"Staged owned EML adapter for {values['base_crit_chance']} — ready for confirmation"
            self.stateChanged.emit()
            return self._last_save_message
        except (OSError, ValueError, PermissionError) as exc:
            if 'operation' in locals() and operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
            self.stateChanged.emit()
            return self._last_save_message

    @Slot(result=str)
    def verifyTuningAdapter(self):
        if not self.tuning_adapter or not self.settings.game_path:
            return "Configure the game folder first"
        if not self._staged_adapter_operation_id:
            return "Stage an EML adapter payload first"
        if not self._adapter_deployed:
            return "Deploy the staged EML adapter first"
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            return "Select a profile first"
        try:
            operation = self.operations.start("tuning-adapter-verify", profile_id=profile.id) if self.operations else None
            values = self.game_settings.values(profile)
            logs = sorted((Path(self.settings.game_path) / "logs").glob("*.eml.log"),
                          key=lambda path: path.stat().st_mtime, reverse=True)
            if not logs:
                raise ValueError("No EML runtime log was found")
            result = self.tuning_adapter.verify_log_file(
                logs[0], self._staged_adapter_operation_id, values["base_crit_chance"],
                minimum_mtime=self._adapter_deployed_at,
            )
            self._last_save_message = f"Verified EML readback for {result['field']} = {result['new_value']}"
            self._adapter_verified = True
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, self._last_save_message)
            self.stateChanged.emit()
            return self._last_save_message
        except (OSError, ValueError, KeyError) as exc:
            if 'operation' in locals() and operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            rollback_note = ""
            if self._adapter_deployed:
                try:
                    self.tuning_adapter.undeploy_adapter(Path(self.settings.game_path))
                    self._adapter_deployed = False
                    self._adapter_verified = False
                    self._adapter_deployed_at = None
                    rollback_note = " EmberVault adapter was rolled back."
                except (OSError, ValueError, PermissionError) as rollback_exc:
                    rollback_note = f" Rollback also failed: {rollback_exc}."
            self._last_save_message = f"EML verification failed: {exc}.{rollback_note}"
            self.stateChanged.emit()
            return self._last_save_message
    @Slot(result=str)
    def deployStagedTuningAdapter(self):
        if not self._staged_adapter_package or not self.settings.game_path:
            return "Stage the adapter and choose a game folder first"
        try:
            operation = self.operations.start("tuning-adapter-deploy", profile_id=self._selected_profile_id) if self.operations else None
            destination = self.tuning_adapter.deploy_staged_package(
                self._staged_adapter_package, Path(self.settings.game_path),
                game_running=self.detector.is_running(),
            )
            self._last_save_message = f"Deployed owned EML adapter to {destination}; launch verification pending"
            self._adapter_deployed = True
            self._adapter_verified = False
            self._adapter_deployed_at = datetime.now().timestamp()
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, self._last_save_message)
            self.stateChanged.emit()
            return self._last_save_message
        except (OSError, ValueError, PermissionError) as exc:
            if 'operation' in locals() and operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
            self.stateChanged.emit()
            return self._last_save_message

    @Slot(result=str)
    def rollbackTuningAdapter(self):
        if not self.tuning_adapter or not self.settings.game_path:
            return "Configure the game folder first"
        try:
            if self.detector.is_running():
                raise PermissionError("Close Enshrouded before rolling back the adapter")
            operation = self.operations.start("tuning-adapter-rollback", profile_id=self._selected_profile_id) if self.operations else None
            self.tuning_adapter.undeploy_adapter(Path(self.settings.game_path))
            self._adapter_deployed = False
            self._adapter_verified = False
            self._adapter_deployed_at = None
            self._last_save_message = "Removed the EmberVault-owned EML adapter; existing mods were not changed"
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, self._last_save_message)
            self.stateChanged.emit()
            return self._last_save_message
        except (OSError, ValueError, PermissionError) as exc:
            if 'operation' in locals() and operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = f"EML adapter rollback failed: {exc}"
            self.stateChanged.emit()
            return self._last_save_message

    @Property("QStringList", notify=stateChanged)
    def profileOptions(self):
        return [profile.name for profile in self.profiles]

    @Property(int, notify=stateChanged)
    def selectedProfileIndex(self):
        for index, profile in enumerate(self.profiles):
            if profile.id == self._selected_profile_id:
                return index
        return 0

    @Property("QStringList", notify=stateChanged)
    def backupOptions(self):
        return [backup.id for backup in self.save_manager.list_backups()]

    @Property(str, notify=stateChanged)
    def restorePreview(self):
        return self._restore_preview

    @Property("QStringList", notify=stateChanged)
    def recentOperations(self):
        if not self.operations:
            return []
        return [
            f"{operation.operation_type} · {operation.status} · {operation.message}"
            for operation in self.operations.list_recent(8)
        ]

    @Property("QStringList", notify=stateChanged)
    def moduleOptions(self):
        if not self.modules:
            return []
        return [
            f"{module.name} · v{module.version} · {module.publisher} · {module.feature_state} · "
            f"{module.process_mode} · {', '.join(module.capabilities) or 'no declared capabilities'}"
            for module in self.modules.discover().values()
        ]

    @Property("QStringList", notify=stateChanged)
    def embeddedModuleOptions(self):
        if not self.modules:
            return []
        return [
            f"{module.name} · embedded · {module.entrypoint}"
            for module in self.modules.embedded()
        ]

    @Slot()
    def inspectEmbeddedModules(self):
        if not self.modules:
            return
        operation = self.operations.start("embedded-module-inspection") if self.operations else None
        try:
            descriptions = []
            for manifest in self.modules.embedded():
                loaded = self.modules.load_embedded(manifest.id)
                describe = getattr(loaded, "describe", None)
                if not callable(describe):
                    raise ValueError(f"Embedded module has no describe contract: {manifest.id}")
                result = describe()
                if not isinstance(result, dict) or result.get("id") != manifest.id:
                    raise ValueError(f"Embedded module returned an invalid description: {manifest.id}")
                descriptions.append(manifest.id)
            message = f"Inspected {len(descriptions)} embedded module(s)"
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, message)
            self._last_save_message = message
        except (ImportError, OSError, ValueError) as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def packageOptions(self):
        if not getattr(self, "packages", None):
            return []
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            return []
        detected_build = self._build if self._build not in {"Unknown build", "Choose game folder"} else None
        return [
            f"{'Enabled' if self.packages.is_enabled(profile, package.id) else 'Disabled'} · "
            f"{package.name} · {package.package_type} · {package.version} · "
            f"Compatibility: {evaluate(required_builds=list(package.required_builds), detected_build=detected_build).state}"
            + (f" · Depends on: {', '.join(package.dependencies)}" if package.dependencies else "")
            for package in self.packages.list()
        ]

    @Property("QStringList", notify=stateChanged)
    def dependencyGraph(self):
        if not self.packages:
            return []
        return [f"{package_id} → {', '.join(dependencies) if dependencies else 'no dependencies'}"
                for package_id, dependencies in sorted(self.packages.dependency_graph().items())]

    @Property("QStringList", notify=stateChanged)
    def profileComparison(self):
        if not self.packages:
            return []
        current = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        others = [item for item in self.profiles if item.id != self._selected_profile_id]
        if not current or not others:
            return ["No second profile available for comparison."]
        comparison = self.packages.compare_profiles(current, others[0])
        return [f"Compared with {others[0].name}", f"Only in {current.name}: {', '.join(comparison['only_left']) or 'none'}",
                f"Only in {others[0].name}: {', '.join(comparison['only_right']) or 'none'}",
                f"Shared: {', '.join(comparison['shared']) or 'none'}"]

    @Property("QStringList", notify=stateChanged)
    def externalPackageOptions(self):
        if not self.packages or not self.settings.game_path:
            return []
        external = self.packages.inspect_external(Path(self.settings.game_path) / "mods")
        managed = {item.id for item in self.packages.list()}
        return [f"External · {item.name} · v{item.version} · {item.id}"
                for item in external if item.id not in managed]

    @Property("QStringList", notify=stateChanged)
    def deploymentOptions(self):
        if not self.packages or not self.settings.game_path:
            return ["Choose a game folder to inspect deployment readiness."]
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            return []
        plan = self.packages.deployment_plan(profile, Path(self.settings.game_path))
        return (["No enabled packages to deploy."] if not plan else
                [f"{item.status.upper()} · {item.package_id} · {item.reason or item.destination}"
                 for item in plan])

    @Property("QStringList", notify=stateChanged)
    def managedDeploymentOptions(self):
        if not self.packages or not self.settings.game_path:
            return []
        findings = self.packages.inspect_deployments(Path(self.settings.game_path))
        return [f"{item.status.upper()} · {item.package_id} · {item.reason}"
                for item in findings]

    @Slot()
    def inspectDeploymentPlan(self):
        if not self.packages or not self.settings.game_path:
            self._last_save_message = "Choose a game folder before inspecting deployment"
        else:
            profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
            operation = self.operations.start("package-deployment-plan", profile_id=self._selected_profile_id) if self.operations else None
            try:
                plan = self.packages.deployment_plan(profile, Path(self.settings.game_path)) if profile else []
                self._deployment_plan_signature = (
                    profile.id if profile else "",
                    str(Path(self.settings.game_path).resolve()),
                    tuple((item.package_id, item.status, item.destination, item.reason) for item in plan),
                )
                ready = sum(1 for item in plan if item.status == "ready")
                conflicts = sum(1 for item in plan if item.status != "ready")
                message = f"Deployment plan: {ready} ready, {conflicts} requiring attention"
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, message)
                self._last_save_message = message
            except (OSError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def deployReadyPackages(self):
        if not self.packages or not self.settings.game_path:
            self._last_save_message = "Choose a game folder before deploying packages"
        else:
            profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
            path = Path(self.settings.game_path)
            plan = self.packages.deployment_plan(profile, path) if profile else []
            signature = (
                profile.id if profile else "", str(path.resolve()),
                tuple((item.package_id, item.status, item.destination, item.reason) for item in plan),
            )
            if self._deployment_plan_signature != signature:
                self._last_save_message = "Inspect the current deployment plan before deploying packages"
            else:
                operation = self.operations.start("package-deploy", profile_id=self._selected_profile_id) if self.operations else None
                try:
                    deployed = self.packages.deploy_ready(profile, path) if profile else []
                    if operation and self.operations:
                        self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Deployed {len(deployed)} package(s)")
                    self._last_save_message = f"Deployed {len(deployed)} package(s) to the game mods folder"
                except (OSError, ValueError) as exc:
                    if operation and self.operations:
                        self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                    self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def diagnosticOptions(self):
        if not self.troubleshooter:
            return []
        return [f"{item.severity.upper()} · {item.title} · {item.message}" for item in self.troubleshooter.scan()]

    @Slot()
    def runDiagnostics(self):
        if self.troubleshooter:
            operation = self.operations.start("troubleshooter-scan", profile_id=self._selected_profile_id) if self.operations else None
            try:
                findings = self.troubleshooter.scan()
                attention = sum(1 for item in findings if item.severity == "attention")
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Diagnostics completed: {attention} attention finding(s)")
                if self.logs:
                    self.logs.info("Troubleshooter scan completed", operation_id=operation.id if operation else None,
                                    profile_id=self._selected_profile_id, details={"attention": attention})
                self._last_save_message = f"Read-only health scan completed: {attention} attention finding(s)"
            except (OSError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def settingOptions(self):
        if not self.game_settings:
            return []
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            return []
        values = self.game_settings.values(profile)
        return [f"{definition.name} · {values[definition.key]}" for definition in self.game_settings.definitions()]

    @Property("QStringList", notify=stateChanged)
    def researchOptions(self):
        if not self.research:
            return []
        return [f"{item.status.upper()} · {'PUBLISHED' if item.published else 'PRIVATE'} · {item.title} · {len(item.evidence)} evidence note(s)"
                for item in self.research.list() if item.profile_id == self._selected_profile_id
                and (not self._research_query or self._research_query.lower() in (item.title + " " + item.hypothesis + " " + item.experiment_template).lower())]

    @Slot(str)
    def searchResearch(self, query: str):
        self._research_query = query.strip()
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def researchEvidenceOptions(self):
        if not self.research:
            return []
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id]
        if not records:
            return []
        latest = records[-1]
        return [f"Evidence {index + 1}: {value[:180]}" for index, value in enumerate(latest.evidence)] + [
            f"Attachment: {item.get('name', '')} · {item.get('kind', '')}" for item in latest.attachments]

    @Property("QStringList", notify=stateChanged)
    def researchTemplateOptions(self):
        return ["general", "runtime-observation", "compatibility", "content-design", "reproduction"]

    @Property("QStringList", notify=stateChanged)
    def researchCollaborationOptions(self):
        if not self.research:
            return []
        result = []
        for item in self.research.list():
            if item.profile_id != self._selected_profile_id:
                continue
            score = self.research.reproducibility_score(item.id)["score"]
            result.append(f"{item.title} · reproducibility {score}% · {len(item.comparison_runs)} comparisons · {len(item.discussion_notes)} discussion note(s)")
        return result

    @Slot(str)
    def addLatestResearchDiscussion(self, note: str):
        if not self.research:
            return
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id]
        if records:
            try:
                self.research.add_discussion_note(records[-1].id, note)
                self._last_save_message = "Added research discussion note"
            except (KeyError, ValueError) as exc:
                self._last_save_message = str(exc)
        else:
            self._last_save_message = "Create a research record first"
        self.stateChanged.emit()

    @Slot(str, str, str)
    def addLatestResearchComparison(self, label: str, outcome: str, build: str = ""):
        if not self.research:
            return
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id]
        if records:
            try:
                self.research.add_comparison(records[-1].id, label, outcome, build)
                self._last_save_message = "Added comparison run"
            except (KeyError, ValueError) as exc:
                self._last_save_message = str(exc)
        else:
            self._last_save_message = "Create a research record first"
        self.stateChanged.emit()

    @Slot()
    def exportLatestResearchReport(self):
        if not self.research:
            return
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id]
        if records:
            try:
                destination = self.research.export_report(records[-1].id)
                self._last_save_message = f"Exported research report to {destination}"
            except (KeyError, OSError) as exc:
                self._last_save_message = str(exc)
        else:
            self._last_save_message = "Create a research record first"
        self.stateChanged.emit()

    @Slot()
    def promoteLatestResearchToKnowledge(self):
        if not self.research or not self.knowledge:
            return
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id]
        if not records:
            self._last_save_message = "Create a research record first"
        else:
            record = records[-1]
            try:
                if record.status != "completed" or not record.evidence:
                    raise ValueError("Complete research with evidence before promotion")
                entry = self.knowledge.create(record.title, "Research report",
                    record.hypothesis, f"Research report {record.id}: {len(record.evidence)} evidence item(s); "
                    f"reproducibility {self.research.reproducibility_score(record.id)['score']}%.",
                    related_ids=[record.id], evidence_refs=[record.id])
                self.research.link_context(record.id, knowledge=[entry.id])
                self._last_save_message = f"Created private knowledge draft {entry.id}"
            except (KeyError, OSError, ValueError) as exc:
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def knowledgeOptions(self):
        if not self.knowledge:
            return []
        return [f"{entry.category} · {'PUBLIC' if entry.published else 'PRIVATE'} · v{entry.version} · {entry.title} — {entry.summary}"
                for entry in self.knowledge.search(self._knowledge_query)]

    @Slot(str)
    def searchKnowledge(self, query: str):
        self._knowledge_query = query
        self.stateChanged.emit()

    @Slot(str, str, str, str)
    def createKnowledgeEntry(self, title: str, category: str, summary: str, content: str):
        if not self.knowledge:
            return
        operation = self.operations.start("knowledge-entry-create") if self.operations else None
        try:
            entry = self.knowledge.create(title, category, summary, content)
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Created knowledge entry {entry.id}")
            self._last_save_message = f"Created knowledge entry {entry.id}"
        except (OSError, ValueError) as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(str, str, str, str, str, str, str)
    def updateLatestKnowledge(self, title: str, category: str, summary: str, content: str,
                              tags: str, related_ids: str, evidence_refs: str):
        if not self.knowledge:
            return
        entries = self.knowledge.entries()
        if not entries:
            self._last_save_message = "Create a knowledge entry first"
        else:
            operation = self.operations.start("knowledge-entry-update") if self.operations else None
            split_ids = lambda value: [item.strip() for item in value.split(",") if item.strip()]
            try:
                entry = self.knowledge.update(entries[-1].id, title, category, summary, content,
                                              split_ids(tags), split_ids(related_ids), split_ids(evidence_refs))
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Updated knowledge entry {entry.id} to v{entry.version}")
                self._last_save_message = f"Updated knowledge entry {entry.id} to v{entry.version}"
            except (KeyError, OSError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def knowledgeHistoryOptions(self):
        if not self.knowledge or not self.knowledge.entries():
            return []
        entry = self.knowledge.entries()[-1]
        return [f"v{item.get('version', '?')} · {item.get('title', 'Untitled')} · {item.get('saved_at', '')}"
                for item in entry.history]

    def _setLatestKnowledgePublication(self, published: bool):
        if not self.knowledge:
            return
        entries = self.knowledge.entries()
        if not entries:
            self._last_save_message = "Create a knowledge entry first"
        else:
            operation_type = "knowledge-entry-publish" if published else "knowledge-entry-unpublish"
            operation = self.operations.start(operation_type) if self.operations else None
            try:
                entry = (self.knowledge.publish if published else self.knowledge.unpublish)(entries[-1].id)
                message = f"{'Published' if published else 'Unpublished'} knowledge entry {entry.id}"
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, message)
                self._last_save_message = message
            except (KeyError, OSError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def publishLatestKnowledge(self):
        self._setLatestKnowledgePublication(True)

    @Slot()
    def unpublishLatestKnowledge(self):
        self._setLatestKnowledgePublication(False)

    @Slot()
    def exportCatalog(self):
        try:
            from PySide6.QtWidgets import QFileDialog
            selected, _ = QFileDialog.getSaveFileName(None, "Export Ember Vault catalog", "embervault-catalog.json", "JSON (*.json)")
        except ImportError:
            selected = ""
        if selected and self.catalog:
            operation = self.operations.start("catalog-export") if self.operations else None
            try:
                destination = self.catalog.export(Path(selected))
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Exported catalog to {destination}")
                self._last_save_message = f"Catalog exported to {destination}"
            except OSError as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
            self.stateChanged.emit()

    @Slot()
    def stageCommunityHandoff(self):
        if not self.community_sync:
            return
        try:
            destination = self.community_sync.stage()
            self._last_save_message = f"Staged website handoff at {destination}"
        except (OSError, ValueError) as exc:
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def releaseAuditOptions(self):
        if not self.release:
            return []
        audit = self.release.audit(["embervault.trainer", "embervault.research", "embervault.content-creator"])
        return [f"Release candidate: {'READY' if audit['ready'] else 'BLOCKED'}",
                *(f"{item['capability_id']} · {item['state']}" for item in audit["blocked"])]

    @Slot()
    def stageLatestResearchSubmission(self):
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id] if self.research else []
        if not records:
            self._last_save_message = "Create a research record first"
        else:
            record = records[-1]
            try:
                if not record.published:
                    raise ValueError("Publish research locally before staging a website submission")
                payload = {"id": record.id, "title": record.title, "hypothesis": record.hypothesis,
                           "status": record.status, "evidence_count": len(record.evidence),
                           "game_build": record.game_build, "reproducibility": self.research.reproducibility_score(record.id)}
                destination = self.community_sync.stage_record("research", record.id, 1, payload)
                self._last_save_message = f"Staged research submission at {destination}"
            except (OSError, ValueError) as exc:
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def stageLatestKnowledgeSubmission(self):
        entries = self.knowledge.entries() if self.knowledge else []
        if not entries:
            self._last_save_message = "Create a knowledge entry first"
        else:
            entry = entries[-1]
            try:
                if not entry.published:
                    raise ValueError("Publish knowledge locally before staging a website submission")
                payload = {"id": entry.id, "title": entry.title, "category": entry.category,
                           "summary": entry.summary, "content": entry.content, "version": entry.version,
                           "tags": list(entry.tags), "related_ids": list(entry.related_ids),
                           "evidence_refs": list(entry.evidence_refs)}
                destination = self.community_sync.stage_record("knowledge", entry.id, entry.version, payload)
                self._last_save_message = f"Staged knowledge submission at {destination}"
            except (OSError, ValueError) as exc:
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def stageLatestContentSubmission(self):
        projects = [item for item in self.content.list() if item.profile_id == self._selected_profile_id] if self.content else []
        if not projects:
            self._last_save_message = "Create a content project first"
        else:
            project = projects[-1]
            try:
                if not project.published:
                    raise ValueError("Publish content locally before staging a website submission")
                payload = next((item for item in self.catalog.build()["content_projects"] if item["id"] == project.id), None)
                if not payload:
                    raise ValueError("Content project is not present in the public catalog")
                destination = self.community_sync.stage_record("content", project.id, 1, payload)
                self._last_save_message = f"Staged content submission at {destination}"
            except (OSError, ValueError) as exc:
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def contentOptions(self):
        if not self.content:
            return []
        return [
            f"{item.status.upper()} · {item.design_type} · {item.name} · {item.profile_id}"
            + (f" · {item.description}" if item.description else "")
            for item in self.content.list() if item.profile_id == self._selected_profile_id
        ]

    @Property("QStringList", notify=stateChanged)
    def contentPreview(self):
        if not self.content:
            return []
        projects = [item for item in self.content.list() if item.profile_id == self._selected_profile_id]
        if not projects:
            return ["No content project selected"]
        try:
            preview = self.content.preview(projects[-1].id)
        except (KeyError, ValueError):
            return ["Preview unavailable"]
        readiness = "READY FOR DESIGN EXPORT" if preview["ready_for_export"] else "NEEDS DESIGN REVIEW"
        return [
            f"{readiness} · {preview['name']} · {preview['design_type']}",
            f"Assets {preview['asset_count']} · Materials {len(preview['materials'])} · Recipe steps {len(preview['recipe_steps'])}",
            f"Research links {len(preview['research_ids'])} · Knowledge links {len(preview['knowledge_ids'])}",
            f"Traceable design decisions {len(preview['design_decisions'])}",
            "DESIGN-ONLY · Live installation: disabled",
            *(f"Review: {issue}" for issue in preview["validation_issues"]),
        ]

    @Slot()
    def previewLatestContentProject(self):
        if not self.content:
            return
        projects = [item for item in self.content.list() if item.profile_id == self._selected_profile_id]
        if not projects:
            self._last_save_message = "Create a content project first"
        else:
            try:
                preview = self.content.preview(projects[-1].id)
                self._last_save_message = ("Design preview ready" if preview["ready_for_export"]
                                           else f"Design preview has {len(preview['validation_issues'])} review item(s)")
            except (KeyError, ValueError) as exc:
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(str, str, str, str)
    def recordLatestContentDecision(self, decision: str, rationale: str, research_ids: str = "", knowledge_ids: str = ""):
        if not self.content:
            return
        projects = [item for item in self.content.list() if item.profile_id == self._selected_profile_id]
        if not projects:
            self._last_save_message = "Create a content project first"
        else:
            try:
                project = self.content.record_design_decision(
                    projects[-1].id, decision, rationale,
                    [item.strip() for item in research_ids.split(",") if item.strip()],
                    [item.strip() for item in knowledge_ids.split(",") if item.strip()],
                )
                self._last_save_message = f"Recorded design decision for {project.id}"
            except (KeyError, ValueError) as exc:
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(str, str, str, str, str, str, str, str, str, str)
    def createContentProject(self, name: str, description: str = "", design_type: str = "furniture", design_notes: str = "", asset_references: str = "", materials: str = "", dimensions: str = "", recipe_plan: str = "", registration_plan: str = "", compatibility_notes: str = ""):
        if not self.content:
            return
        operation = self.operations.start("content-project-create", profile_id=self._selected_profile_id) if self.operations else None
        try:
            references = [item.strip() for item in asset_references.split(",") if item.strip()]
            material_list = [item.strip() for item in materials.split(",") if item.strip()]
            recipe_list = [item.strip() for item in recipe_plan.split(";") if item.strip()]
            dimension_values = {}
            for item in dimensions.split(","):
                if item.strip():
                    key, value = item.split("=", 1)
                    dimension_values[key.strip()] = float(value.strip())
            project = self.content.create(name, self._selected_profile_id, description, design_type, design_notes, references,
                                          material_list, dimension_values, recipe_list, registration_plan, compatibility_notes)
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Created content project {project.id}")
            self._last_save_message = f"Created content project {project.id}"
        except (OSError, ValueError) as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def syncCatalogFolder(self):
        selected = QFileDialog.getExistingDirectory(None, "Choose Ember Vault catalog folder")
        if selected and self.catalog:
            operation = self.operations.start("catalog-sync") if self.operations else None
            try:
                destination = self.catalog.sync_to_directory(Path(selected))
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Synced catalog to {destination}")
                self._last_save_message = f"Synced public catalog to {destination}"
            except (OSError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
            self.stateChanged.emit()

    @Slot(str)
    def setLatestContentStatus(self, status: str):
        if not self.content:
            return
        projects = [item for item in self.content.list() if item.profile_id == self._selected_profile_id]
        if not projects:
            self._last_save_message = "Create a content project first"
        else:
            operation = self.operations.start("content-project-status", profile_id=self._selected_profile_id) if self.operations else None
            try:
                project = self.content.set_status(projects[-1].id, status)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Content project status {project.status}")
                self._last_save_message = f"Content project is {project.status}"
            except (KeyError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(str, str, str, str, str, str, str, str)
    def updateLatestContentDesign(self, design_type: str, design_notes: str, asset_references: str, materials: str = "", dimensions: str = "", recipe_plan: str = "", registration_plan: str = "", compatibility_notes: str = ""):
        if not self.content:
            return
        projects = [item for item in self.content.list() if item.profile_id == self._selected_profile_id]
        if not projects:
            self._last_save_message = "Create a content project first"
        else:
            operation = self.operations.start("content-design-update", profile_id=self._selected_profile_id) if self.operations else None
            try:
                references = [item.strip() for item in asset_references.split(",") if item.strip()]
                material_list = [item.strip() for item in materials.split(",") if item.strip()]
                recipe_list = [item.strip() for item in recipe_plan.split(";") if item.strip()]
                dimension_values = {}
                for item in dimensions.split(","):
                    if item.strip():
                        key, value = item.split("=", 1)
                        dimension_values[key.strip()] = float(value.strip())
                project = self.content.update_design(projects[-1].id, design_type, design_notes, references,
                                                     material_list, dimension_values, recipe_list, registration_plan, compatibility_notes)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Updated content design {project.id}")
                self._last_save_message = f"Updated design for {project.id}"
            except (KeyError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def publishLatestContentProject(self):
        if not self.content:
            return
        projects = [item for item in self.content.list() if item.profile_id == self._selected_profile_id]
        if not projects:
            self._last_save_message = "Create a content project first"
        else:
            operation = self.operations.start("content-project-publish", profile_id=self._selected_profile_id) if self.operations else None
            try:
                project = self.content.publish(projects[-1].id)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Published content project {project.id}")
                self._last_save_message = f"Published content project {project.id}"
            except (KeyError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def unpublishLatestContentProject(self):
        if not self.content:
            return
        projects = [item for item in self.content.list() if item.profile_id == self._selected_profile_id]
        if not projects:
            self._last_save_message = "Create a content project first"
        else:
            operation = self.operations.start("content-project-unpublish", profile_id=self._selected_profile_id) if self.operations else None
            try:
                project = self.content.unpublish(projects[-1].id)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Unpublished content project {project.id}")
                self._last_save_message = f"Unpublished content project {project.id}"
            except KeyError as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def exportLatestContentProject(self):
        if not self.content:
            return
        projects = [item for item in self.content.list() if item.profile_id == self._selected_profile_id]
        if not projects:
            self._last_save_message = "Create a content project first"
        else:
            project = projects[-1]
            operation = self.operations.start("content-project-export", profile_id=project.profile_id) if self.operations else None
            try:
                destination = self.content.export(project)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Exported content project {project.id}")
                self._last_save_message = f"Exported design manifest to {destination}"
            except OSError as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def characterOptions(self):
        if not self.characters:
            return []
        return [f"{item.name} · level {item.planned_level} · {item.profile_id}"
                + (f" · {item.notes}" if item.notes else "")
                for item in self.characters.list() if item.profile_id == self._selected_profile_id]

    @Property("QStringList", notify=stateChanged)
    def characterPlanningOptions(self):
        if not self.characters:
            return []
        return [f"{item.name} · template {item.build_template} · v{item.version} · goals {len(item.build_goals)} · steps {len(item.progression_plan)}"
                for item in self.characters.list() if item.profile_id == self._selected_profile_id]

    @Property("QStringList", notify=stateChanged)
    def characterTemplateOptions(self):
        return ["general", "tank", "damage", "support", "gatherer"]

    @Slot(str)
    def setLatestCharacterTemplate(self, template: str):
        records = [item for item in self.characters.list() if item.profile_id == self._selected_profile_id] if self.characters else []
        if records:
            try:
                record = self.characters.set_template(records[-1].id, template)
                self._last_save_message = f"Set {record.name} template to {record.build_template}"
            except (KeyError, ValueError) as exc:
                self._last_save_message = str(exc)
        else:
            self._last_save_message = "Create a character project first"
        self.stateChanged.emit()

    @Slot()
    def compareLatestCharacterEquipment(self):
        records = [item for item in self.characters.list() if item.profile_id == self._selected_profile_id] if self.characters else []
        if len(records) < 2:
            self._last_save_message = "Create two character projects to compare equipment"
        else:
            result = self.characters.compare_equipment(records[-2].id, records[-1].id)
            self._last_save_message = f"Compared equipment for {result['left']['id']} and {result['right']['id']} (plan-only)"
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def trainerPlanOptions(self):
        if not self.trainer:
            return []
        return [f"{item.target} · tests {len(item.test_steps)} · recovery {item.recovery_simulation} · evidence {item.evidence_gate}"
                for item in self.trainer.list() if item.profile_id == self._selected_profile_id]

    @Slot(str)
    def addLatestTrainerTestStep(self, step: str):
        plans = [item for item in self.trainer.list() if item.profile_id == self._selected_profile_id] if self.trainer else []
        if plans:
            try:
                self.trainer.add_test_step(plans[-1].id, step)
                self._last_save_message = "Added Trainer test step"
            except (KeyError, ValueError) as exc:
                self._last_save_message = str(exc)
        else:
            self._last_save_message = "Create a Trainer plan first"
        self.stateChanged.emit()

    @Slot(bool)
    def simulateLatestTrainerRecovery(self, verified: bool):
        plans = [item for item in self.trainer.list() if item.profile_id == self._selected_profile_id] if self.trainer else []
        if plans:
            try:
                plan = self.trainer.simulate_recovery(plans[-1].id, verified)
                self._last_save_message = f"Trainer recovery simulation: {plan.recovery_simulation}"
            except KeyError as exc:
                self._last_save_message = str(exc)
        else:
            self._last_save_message = "Create a Trainer plan first"
        self.stateChanged.emit()

    @Slot(int)
    def simulateLatestCharacterProgression(self, level: int):
        records = [item for item in self.characters.list() if item.profile_id == self._selected_profile_id] if self.characters else []
        if records:
            try:
                result = self.characters.simulate_progression(records[-1].id, level)
                self._last_save_message = f"Progression simulation: {result['levels_to_gain']} level(s), plan-only"
            except (KeyError, ValueError) as exc:
                self._last_save_message = str(exc)
        else:
            self._last_save_message = "Create a character project first"
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def riskOptions(self):
        if not self.risk:
            return []
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            return []
        return [
            f"{capability}: {'ready' if self.risk.evaluate(capability, profile).allowed else 'gated'}"
            for capability in ("trainer", "research", "content-creator")
        ]

    def _launchGuardedModule(self, module_id: str, capability: str):
        if not self.launcher:
            return
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            self._last_save_message = "Select a profile first"
            self.stateChanged.emit()
            return
        operation = self.operations.start(f"module-launch-{capability}", profile_id=profile.id) if self.operations else None
        backup_id = self._selected_backup_id or None
        settings_manifest = None
        if capability == "tuning-audit" and self.game_settings:
            settings_manifest = str(self.game_settings.export(profile))
        try:
            process = self.launcher.launch(
                module_id, capability,
                profile,
                LaunchContext(
                    profile.id, self.settings.game_path or None, operation.id if operation else None,
                    backup_id, settings_manifest
                ),
                backup_id,
            )
            output, _ = process.communicate(timeout=15)
            if process.returncode != 0:
                raise RuntimeError(f"Module exited with code {process.returncode}")
            result = output.strip() if output else "no worker output"
            if len(result.encode("utf-8")) > MAX_WORKER_OUTPUT:
                raise RuntimeError("Worker returned too much output")
            try:
                worker_result = json.loads(result)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise RuntimeError("Worker returned invalid JSON") from exc
            if (not isinstance(worker_result, dict)
                    or worker_result.get("contract_version") != 1
                    or worker_result.get("read_only") is not True
                    or worker_result.get("status") != "ready"
                    or not isinstance(worker_result.get("game_path"), str)
                    or not isinstance(worker_result.get("operation"), str)
                    or (module_id == "embervault.research" and
                        (not isinstance(worker_result.get("evidence"), list) or
                         any(not isinstance(item, str) or not item.strip()
                             for item in worker_result.get("evidence", []))))
                    or (module_id == "embervault.trainer" and
                        (not isinstance(worker_result.get("checks"), list) or
                         any(not isinstance(item, str) or not item.strip()
                             for item in worker_result.get("checks", []))))
                    or (module_id == "embervault.content-creator" and
                        (not isinstance(worker_result.get("checks"), list) or
                         any(not isinstance(item, str) or not item.strip()
                             for item in worker_result.get("checks", []))))
                    or (module_id == "embervault.tuning-audit" and
                        (not isinstance(worker_result.get("checks"), list) or
                         any(not isinstance(item, str) or not item.strip()
                             for item in worker_result.get("checks", []))))
                    or worker_result.get("profile") != profile.id
                    or (operation and worker_result.get("operation") != operation.id)):
                raise RuntimeError("Worker returned an invalid or non-read-only contract")
            if module_id == "embervault.research" and self.research:
                records = [item for item in self.research.list()
                           if item.profile_id == profile.id]
                if records:
                    record = records[-1]
                    for observation in worker_result["evidence"]:
                        self.research.add_evidence(record.id, f"worker observation: {observation}")
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Launched {module_id}: {result}")
            if self.logs:
                self.logs.info("Guarded module completed", operation_id=operation.id if operation else None,
                                profile_id=profile.id, details={"module_id": module_id, "output": result})
            if module_id == "embervault.research":
                evidence_count = len(worker_result.get("evidence", []))
                self._last_save_message = (
                    f"Completed guarded {capability} worker: research evidence probe "
                    f"({evidence_count} observations) · {worker_result.get('game_path', '')}"
                )
            elif module_id == "embervault.trainer":
                self._last_save_message = (
                    f"Completed guarded {capability} readiness audit "
                    f"({len(worker_result.get('checks', []))} checks)"
                )
            elif module_id == "embervault.content-creator":
                self._last_save_message = (
                    f"Completed guarded {capability} design audit "
                    f"({len(worker_result.get('checks', []))} checks)"
                )
            elif module_id == "embervault.tuning-audit":
                self._last_save_message = (
                    f"Completed guarded {capability} staged-settings audit "
                    f"({len(worker_result.get('checks', []))} checks)"
                )
            else:
                self._last_save_message = f"Completed guarded {capability} worker: {result}"
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            message = "Guarded module timed out and was terminated"
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, message)
            if self.logs:
                self.logs.error(message, operation_id=operation.id if operation else None,
                                 profile_id=profile.id, details={"module_id": module_id})
            self._last_save_message = message
        except (PermissionError, KeyError, OSError, RuntimeError, ValueError) as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            if self.logs:
                self.logs.error("Guarded module failed", operation_id=operation.id if operation else None,
                                 profile_id=profile.id, details={"module_id": module_id, "error": str(exc)})
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def launchTrainer(self):
        self._launchGuardedModule("embervault.trainer", "trainer")

    @Slot(str, str)
    def createTrainerPlan(self, target: str, notes: str):
        if not self.trainer:
            return
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        backup_id = self._selected_backup_id or ""
        operation = self.operations.start("trainer-plan-create", profile_id=self._selected_profile_id) if self.operations else None
        try:
            if not profile:
                raise ValueError("Select a profile first")
            plan = self.trainer.create(profile, target, notes, backup_id)
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Created Trainer plan {plan.id}")
            self._last_save_message = f"Created Trainer plan {plan.id}"
        except (OSError, ValueError) as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def exportLatestTrainerPlan(self):
        if not self.trainer:
            return
        plans = [item for item in self.trainer.list() if item.profile_id == self._selected_profile_id]
        if not plans:
            self._last_save_message = "Create a Trainer plan first"
        else:
            operation = self.operations.start("trainer-plan-export", profile_id=self._selected_profile_id) if self.operations else None
            try:
                destination = self.trainer.export(plans[-1])
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Exported Trainer plan {plans[-1].id}")
                self._last_save_message = f"Exported Trainer plan to {destination}"
            except OSError as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def launchResearchWorker(self):
        self._launchGuardedModule("embervault.research", "research")

    @Slot()
    def launchContentWorker(self):
        self._launchGuardedModule("embervault.content-creator", "content-creator")

    @Slot()
    def launchTuningAudit(self):
        self._launchGuardedModule("embervault.tuning-audit", "tuning-audit")

    @Slot(str, str)
    def createCharacter(self, name: str, notes: str = ""):
        if not self.characters:
            return
        operation = self.operations.start("character-project-create", profile_id=self._selected_profile_id) if self.operations else None
        try:
            record = self.characters.create(name, self._selected_profile_id, notes)
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Created character project {record.id}")
            self._last_save_message = f"Created character project {record.id}"
        except (OSError, ValueError) as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(int)
    def stageLatestCharacterLevel(self, level: int):
        if not self.characters:
            return
        records = [item for item in self.characters.list() if item.profile_id == self._selected_profile_id]
        if not records:
            self._last_save_message = "Create a character project first"
        else:
            operation = self.operations.start("character-level-stage", profile_id=self._selected_profile_id) if self.operations else None
            try:
                record = self.characters.stage_level(records[-1].id, level)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Staged level {record.planned_level} for {record.id}")
                self._last_save_message = f"Staged level {record.planned_level} for {record.name}"
            except (KeyError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(str)
    def updateLatestCharacterNotes(self, notes: str):
        if not self.characters:
            return
        records = [item for item in self.characters.list() if item.profile_id == self._selected_profile_id]
        if not records:
            self._last_save_message = "Create a character project first"
        else:
            operation = self.operations.start("character-notes-update", profile_id=self._selected_profile_id) if self.operations else None
            try:
                record = self.characters.update_notes(records[-1].id, notes)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Updated character plan {record.id}")
                self._last_save_message = f"Updated character plan {record.id}"
            except (KeyError, OSError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(str, str, str, str, str)
    def updateLatestCharacterPlan(self, goals: str, progression: str, equipment: str, skills: str, backup_id: str):
        if not self.characters:
            return
        records = [item for item in self.characters.list() if item.profile_id == self._selected_profile_id]
        if not records:
            self._last_save_message = "Create a character project first"
        else:
            operation = self.operations.start("character-plan-update", profile_id=self._selected_profile_id) if self.operations else None
            try:
                if backup_id.strip():
                    snapshot = next((item for item in self.save_manager.list_backups() if item.id == backup_id.strip() and item.verified), None)
                    if snapshot is None:
                        raise ValueError("Character plans may reference only an existing verified backup")
                split = lambda value: [item.strip() for item in value.split(";") if item.strip()]
                record = self.characters.update_plan(records[-1].id, split(goals), split(progression), split(equipment), split(skills), backup_id.strip())
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Updated character plan {record.id}")
                self._last_save_message = f"Updated character plan {record.id}"
            except (KeyError, OSError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def exportLatestCharacterPlan(self):
        if not self.characters:
            return
        records = [item for item in self.characters.list() if item.profile_id == self._selected_profile_id]
        if not records:
            self._last_save_message = "Create a character project first"
        else:
            record = records[-1]
            operation = self.operations.start("character-plan-export", profile_id=record.profile_id) if self.operations else None
            try:
                destination = self.characters.export(record)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Exported character plan {record.id}")
                self._last_save_message = f"Exported character plan to {destination}"
            except OSError as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(str, str, str)
    def createResearchRecord(self, title: str, hypothesis: str, experiment_template: str = "general"):
        if not self.research:
            return
        operation = self.operations.start("research-create", profile_id=self._selected_profile_id) if self.operations else None
        try:
            record = self.research.create(title, hypothesis, self._selected_profile_id, experiment_template=experiment_template)
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Created research record {record.id}")
            self._last_save_message = f"Created research record {record.id}"
        except (OSError, ValueError) as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(str)
    def addResearchEvidence(self, note: str):
        if not self.research:
            return
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id]
        if not records:
            self._last_save_message = "Create a research record first"
        else:
            operation = self.operations.start("research-evidence", profile_id=self._selected_profile_id) if self.operations else None
            try:
                record = self.research.add_evidence(records[-1].id, note)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Added evidence to {record.id}")
                self._last_save_message = f"Added evidence to {record.id}"
            except (KeyError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    def _update_latest_research_text(self, text: str, operation_type: str, action) -> None:
        if not self.research:
            return
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id]
        if not records:
            self._last_save_message = "Create a research record first"
        else:
            operation = self.operations.start(operation_type, profile_id=self._selected_profile_id) if self.operations else None
            try:
                record = action(records[-1].id, text)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Updated research {record.id}")
                self._last_save_message = f"Updated research record {record.id}"
            except (KeyError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(str)
    def addResearchReproductionStep(self, step: str):
        self._update_latest_research_text(step, "research-reproduction-step",
                                           lambda record_id, value: self.research.add_reproduction_step(record_id, value))

    @Slot(str)
    def addResearchFailure(self, failure: str):
        self._update_latest_research_text(failure, "research-failure",
                                           lambda record_id, value: self.research.add_failure(record_id, value))

    @Slot(str)
    def requestLatestResearchPromotion(self, note: str):
        self._update_latest_research_text(note, "research-promotion-review",
                                           lambda record_id, value: self.research.set_promotion_review(record_id, "requested", value))

    @Slot(str)
    def approveLatestResearchPromotion(self, note: str):
        self._update_latest_research_text(note, "research-promotion-approval",
                                           lambda record_id, value: self.research.set_promotion_review(record_id, "approved", value))

    @Slot(str)
    def setLatestResearchStatus(self, status: str):
        if not self.research:
            return
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id]
        if not records:
            self._last_save_message = "Create a research record first"
        else:
            operation = self.operations.start("research-status", profile_id=self._selected_profile_id) if self.operations else None
            try:
                record = self.research.set_status(records[-1].id, status)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Research status {record.status}")
                self._last_save_message = f"Research record is {record.status}"
            except (KeyError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def publishLatestResearch(self):
        if not self.research:
            return
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id]
        if not records:
            self._last_save_message = "Create a research record first"
        else:
            operation = self.operations.start("research-publish", profile_id=self._selected_profile_id) if self.operations else None
            try:
                record = self.research.publish(records[-1].id)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Published research {record.id}")
                self._last_save_message = f"Published research record {record.id}"
            except (KeyError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def unpublishLatestResearch(self):
        if not self.research:
            return
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id]
        if not records:
            self._last_save_message = "Create a research record first"
        else:
            operation = self.operations.start("research-unpublish", profile_id=self._selected_profile_id) if self.operations else None
            try:
                record = self.research.unpublish(records[-1].id)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Unpublished research {record.id}")
                self._last_save_message = f"Unpublished research record {record.id}"
            except KeyError as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def exportLatestResearchSummary(self):
        if not self.research:
            return
        records = [item for item in self.research.list() if item.profile_id == self._selected_profile_id]
        if not records:
            self._last_save_message = "Create a research record first"
        else:
            operation = self.operations.start("research-summary-export", profile_id=self._selected_profile_id) if self.operations else None
            try:
                destination = self.research.export_summary(records[-1])
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Exported research summary {records[-1].id}")
                self._last_save_message = f"Exported research summary to {destination}"
            except OSError as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(int)
    def stageSetting(self, index: int):
        if not self.game_settings:
            return
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        definitions = self.game_settings.definitions()
        if not profile or not 0 <= index < len(definitions):
            return
        definition = definitions[index]
        values = self.game_settings.values(profile)
        current = values[definition.key]
        if definition.value_type == "boolean":
            value = not current
        else:
            step = 0.05 if definition.maximum is not None and definition.maximum <= 1.0 else 0.25
            value = float(current) + step
            if definition.maximum is not None and value > definition.maximum:
                value = definition.minimum or 0.0
        operation = self.operations.start("game-setting-stage", profile_id=profile.id) if self.operations else None
        try:
            updated = self.game_settings.stage(profile, definition.key, value)
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Staged {definition.key}")
            self.profiles = [updated if item.id == updated.id else item for item in self.profiles]
            self._last_save_message = f"Staged {definition.name} for {updated.name}"
        except ValueError as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def resetGameSettings(self):
        if not self.game_settings:
            return
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            return
        operation = self.operations.start("game-settings-reset", profile_id=profile.id) if self.operations else None
        updated = self.game_settings.reset(profile)
        if operation and self.operations:
            self.operations.finish(operation, OperationStatus.SUCCEEDED, "Reset game settings")
        self.profiles = [updated if item.id == updated.id else item for item in self.profiles]
        self._last_save_message = f"Reset game settings for {updated.name}"
        self.stateChanged.emit()

    @Slot()
    def exportGameSettings(self):
        if not self.game_settings:
            return
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            return
        operation = self.operations.start("game-settings-export", profile_id=profile.id) if self.operations else None
        try:
            destination = self.game_settings.export(profile)
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Exported settings to {destination.name}")
            self._last_save_message = f"Exported staged settings to {destination}"
        except OSError as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(str)
    def importGameSettings(self, source: str):
        if not self.game_settings:
            return
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile or not source:
            return
        operation = self.operations.start("game-settings-import", profile_id=profile.id) if self.operations else None
        try:
            updated = self.game_settings.import_manifest(profile, Path(source))
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Imported settings for {updated.name}")
            self.profiles = [updated if item.id == updated.id else item for item in self.profiles]
            self._last_save_message = f"Imported staged settings for {updated.name}"
        except ValueError as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Property("QStringList", notify=stateChanged)
    def profileDetails(self):
        return [
            f"{profile.name} · {profile.profile_type} · {profile.description}"
            for profile in self.profiles
        ]

    @Property("QStringList", notify=stateChanged)
    def packageUpdates(self):
        return ["No trusted update feed configured; package upgrades remain explicit and local."]

    @Slot()
    def exportActiveProfile(self):
        profile = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not profile:
            return
        try:
            from PySide6.QtWidgets import QFileDialog
            selected, _ = QFileDialog.getSaveFileName(None, "Export EmberVault profile", f"{profile.id}.json", "JSON (*.json)")
        except ImportError:
            selected = ""
        if selected:
            operation = self.operations.start("profile-export", profile_id=profile.id) if self.operations else None
            try:
                destination = self.profile_service.export_profile(profile.id, Path(selected))
                if operation and self.operations: self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Exported profile to {destination}")
                self._last_save_message = f"Exported profile to {destination}"
            except (OSError, ValueError) as exc:
                if operation and self.operations: self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
            self.stateChanged.emit()

    @Slot()
    def importProfile(self):
        try:
            from PySide6.QtWidgets import QFileDialog
            selected, _ = QFileDialog.getOpenFileName(None, "Import EmberVault profile", "", "JSON (*.json)")
        except ImportError:
            selected = ""
        if selected:
            operation = self.operations.start("profile-import") if self.operations else None
            try:
                profile = self.profile_service.import_profile(Path(selected))
                self.profiles.append(profile); self._selected_profile_id = profile.id; self._profile_name = profile.name
                if operation and self.operations: self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Imported profile {profile.id}")
                self._last_save_message = f"Imported profile {profile.name}"
            except (OSError, ValueError, TypeError) as exc:
                if operation and self.operations: self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
            self.stateChanged.emit()

    @Slot()
    def refresh(self):
        if self.settings.game_path:
            installation = self.detector.detect(Path(self.settings.game_path))
            issues = self.detector.validate(installation)
            self._game_status = "Ready" if not issues else "Needs attention"
            self._build = installation.build_id or "Build unknown"
        else:
            self._game_status = "Not configured"
            self._build = "Choose game folder"
        if self.stateChanged is not None:
            self.stateChanged.emit()

    @Slot()
    def chooseGameFolder(self):
        try:
            from PySide6.QtWidgets import QFileDialog
            selected = QFileDialog.getExistingDirectory(None, "Choose Enshrouded installation folder")
        except ImportError:
            selected = ""
        if selected:
            self.settings.game_path = selected
            self.settings_service.save(self.settings)
            self._last_save_message = f"Game folder set to {selected}"
            self.refresh()

    @Slot(result=str)
    def saveManagerSummary(self):
        return self.saveSummary

    @Slot(int)
    def selectProfile(self, index: int):
        if 0 <= index < len(self.profiles):
            self._selected_profile_id = self.profiles[index].id
            self._profile_name = self.profiles[index].name
            self.stateChanged.emit()

    @Slot(str)
    def createProfile(self, name: str):
        operation = self.operations.start("profile-create") if self.operations else None
        try:
            profile = self.profile_service.create_custom(name)
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Created profile {profile.id}",)
            self.profiles.append(profile)
            self._selected_profile_id = profile.id
            self._profile_name = profile.name
            self._last_save_message = f"Created profile {profile.name}"
        except ValueError as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def deleteActiveProfile(self):
        if self._selected_profile_id in {"default", "research"}:
            self._last_save_message = "Built-in profiles cannot be deleted"
        else:
            operation = self.operations.start("profile-delete", profile_id=self._selected_profile_id) if self.operations else None
            try:
                deleted = self._selected_profile_id
                owned_records = (
                    [item for item in self.research.list() if item.profile_id == deleted] if self.research else []
                ) + (
                    [item for item in self.content.list() if item.profile_id == deleted] if self.content else []
                ) + (
                    [item for item in self.characters.list() if item.profile_id == deleted] if self.characters else []
                )
                if owned_records:
                    raise ValueError("Profile owns project records; remove or migrate them before deletion")
                self.profile_service.delete_custom(deleted)
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, f"Deleted profile {deleted}")
                self.profiles = [item for item in self.profiles if item.id != deleted]
                fallback = next((item for item in self.profiles if item.id == "default"), self.profiles[0])
                self._selected_profile_id = fallback.id
                self._profile_name = fallback.name
                self._last_save_message = f"Deleted profile {deleted}"
            except ValueError as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(int)
    def togglePackage(self, index: int):
        if not getattr(self, "packages", None):
            return
        available = self.packages.list()
        if not 0 <= index < len(available):
            return
        selected = next((item for item in self.profiles if item.id == self._selected_profile_id), None)
        if not selected:
            return
        package = available[index]
        enabled = not self.packages.is_enabled(selected, package.id)
        operation = self.operations.start("package-enable" if enabled else "package-disable", profile_id=selected.id, package_id=package.id) if self.operations else None
        try:
            detected_build = self._build if self._build not in {"Unknown build", "Choose game folder"} else None
            updated = self.packages.set_enabled(selected, package.id, enabled, detected_build)
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, "Package state updated")
            self.profiles = [updated if item.id == updated.id else item for item in self.profiles]
            self._last_save_message = f"{'Enabled' if enabled else 'Disabled'} {package.name} for {updated.name}"
        except (OSError, ValueError) as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def importPackage(self):
        try:
            from PySide6.QtWidgets import QFileDialog
            selected = QFileDialog.getExistingDirectory(None, "Choose package folder")
            if not selected:
                selected, _ = QFileDialog.getOpenFileName(
                    None, "Choose package ZIP", "", "Packages (*.zip)"
                )
        except ImportError:
            selected = ""
        if selected and self.packages:
            try:
                operation = self.operations.start("package-import") if self.operations else None
                package = self.packages.install_from_archive(Path(selected)) if selected.lower().endswith(".zip") else self.packages.install_from_directory(Path(selected))
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.SUCCEEDED, "Package imported")
                self._last_save_message = f"Imported {package.name}"
            except (OSError, ValueError) as exc:
                if operation and self.operations:
                    self.operations.finish(operation, OperationStatus.FAILED, str(exc))
                if self.logs:
                    self.logs.error("Troubleshooter scan failed", operation_id=operation.id if operation else None,
                                    profile_id=self._selected_profile_id, details={"error": str(exc)})
                self._last_save_message = str(exc)
            self.stateChanged.emit()

    @Slot(int)
    def removePackage(self, index: int):
        if not self.packages:
            return
        available = self.packages.list()
        if not 0 <= index < len(available):
            return
        package = available[index]
        operation = self.operations.start("package-remove", package_id=package.id) if self.operations else None
        try:
            self.packages.remove(package.id)
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, "Package removed")
            self._last_save_message = f"Removed {package.name}"
        except (OSError, ValueError) as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(int)
    def undeployPackage(self, index: int):
        if not self.packages or not self.settings.game_path:
            self._last_save_message = "Choose a game folder before undeploying packages"
            self.stateChanged.emit()
            return
        available = self.packages.list()
        if not 0 <= index < len(available):
            return
        package = available[index]
        operation = self.operations.start("package-undeploy", profile_id=self._selected_profile_id,
                                          package_id=package.id) if self.operations else None
        try:
            self.packages.undeploy(package.id, Path(self.settings.game_path))
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.SUCCEEDED, "Package undeployed")
            self._last_save_message = f"Undeployed {package.name}"
        except (OSError, ValueError) as exc:
            if operation and self.operations:
                self.operations.finish(operation, OperationStatus.FAILED, str(exc))
            self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(int)
    def selectBackup(self, index: int):
        backups = self.save_manager.list_backups()
        self._selected_backup_id = backups[index].id if 0 <= index < len(backups) else ""
        self._restore_preview_backup_id = ""
        self._restore_preview = "Backup selected" if self._selected_backup_id else "No restore selected"
        self.stateChanged.emit()

    @Slot()
    def previewRestore(self):
        if not self._selected_backup_id or not self._save_directory:
            self._restore_preview = "Choose a save folder and backup first"
        else:
            try:
                if self.save_workflow:
                    result = self.save_workflow.preview_restore(
                        self._selected_backup_id, Path(self._save_directory), self._selected_profile_id
                    )
                    plan = result.payload
                else:
                    plan = self.save_manager.preview_restore(self._selected_backup_id, Path(self._save_directory))
                self._restore_preview = f"{len(plan['files_to_add_or_replace'])} files will be restored; current state will be backed up first"
                self._restore_preview_backup_id = self._selected_backup_id
            except SaveManagerError as exc:
                self._restore_preview = str(exc)
                self._restore_preview_backup_id = ""
        self.stateChanged.emit()

    @Slot()
    def verifySelected(self):
        if not self._selected_backup_id:
            self._last_save_message = "Choose a backup first"
        else:
            try:
                if self.save_workflow:
                    self.save_workflow.verify(self._selected_backup_id, self._selected_profile_id)
                elif not self.save_manager.verify_backup(self._selected_backup_id):
                    raise SaveManagerError("Backup verification failed")
                self._last_save_message = f"Verified {self._selected_backup_id}"
            except (OSError, SaveManagerError, ValueError) as exc:
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def restoreSelected(self):
        if not self._selected_backup_id or not self._save_directory:
            self._last_save_message = "Choose a save folder and backup first"
        elif self._restore_preview_backup_id != self._selected_backup_id:
            self._last_save_message = "Preview the selected restore before restoring"
        else:
            try:
                if self.save_workflow:
                    result = self.save_workflow.restore(
                        self._selected_backup_id, Path(self._save_directory), self._selected_profile_id
                    )
                    current = result.snapshot
                    operation_id = result.operation.id
                else:
                    current = self.save_manager.backup(Path(self._save_directory), "automatic-before-restore")
                    self.save_manager.restore(self._selected_backup_id, Path(self._save_directory), current_backup=current)
                    operation_id = "legacy"
                self._last_save_message = f"Restored and verified {self._selected_backup_id} ({operation_id})"
                self._safety = f"Current state preserved as {current.id}"
            except (OSError, SaveManagerError) as exc:
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot()
    def chooseSaveFolder(self):
        try:
            from PySide6.QtWidgets import QFileDialog
            selected = QFileDialog.getExistingDirectory(None, "Choose Enshrouded save folder")
        except ImportError:
            selected = ""
        if selected:
            self._save_directory = selected
            self._restore_preview_backup_id = ""
            self._last_save_message = f"Selected {selected}"
            self.stateChanged.emit()

    @Slot()
    def inspectSaves(self):
        if not self._save_directory:
            self._last_save_message = "Choose a save folder first"
        else:
            try:
                if self.save_workflow:
                    result = self.save_workflow.inspect(Path(self._save_directory), self._selected_profile_id)
                    files = result.payload["files"]
                else:
                    files = self.save_manager.inspect(Path(self._save_directory))
                self._last_save_message = f"Inspected {len(files)} file{'s' if len(files) != 1 else ''}"
            except SaveManagerError as exc:
                self._last_save_message = str(exc)
        self.stateChanged.emit()

    @Slot(str)
    def createBackup(self, label: str):
        if not self._save_directory:
            self._last_save_message = "Choose a save folder first"
        else:
            try:
                if self.save_workflow:
                    result = self.save_workflow.backup(Path(self._save_directory), label, self._selected_profile_id)
                    snapshot = result.snapshot
                else:
                    snapshot = self.save_manager.backup(Path(self._save_directory), label)
                self._last_save_message = f"Verified {snapshot.id}"
                self._safety = "Backup verified"
            except (OSError, SaveManagerError) as exc:
                self._last_save_message = str(exc)
        self.stateChanged.emit()
