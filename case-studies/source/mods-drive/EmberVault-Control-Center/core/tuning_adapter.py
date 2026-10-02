"""Evidence-backed, fail-closed runtime tuning adapter metadata."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

MAX_RUNTIME_LOG_BYTES = 4 * 1024 * 1024


class TuningAdapterService:
    """Loads reviewed evidence without granting mutation authority by itself."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.manifest_path = self.root / "adapters" / "eml-balancing-table.json"

    def manifest(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("Unable to read tuning adapter manifest") from exc
        self.validate(payload)
        return payload

    def compatibility_report(self, *, loader: str, loader_api_version: str,
                             game_build: str) -> dict[str, Any]:
        """Return a fail-closed compatibility matrix result for this adapter."""
        manifest = self.manifest()
        expected = {
            "adapter_id": manifest["id"], "adapter_version": manifest["version"],
            "loader": manifest["loader"], "loader_api_version": manifest["loader_api_version"],
            "supported_builds": [manifest["game_build"]],
            "supported_setting_keys": list(manifest["supported_setting_keys"]),
            "future_adapters": ["shroudtopia"],
        }
        compatible = (str(loader) == manifest["loader"] and
                      str(loader_api_version) == manifest["loader_api_version"] and
                      str(game_build) in expected["supported_builds"])
        return expected | {"compatible": compatible,
                           "state": "compatible" if compatible else "incompatible"}

    def capture_failure_session(self, operation_id: str, failure: str,
                                *, phase: str, recovery_started: bool = False) -> Path:
        """Persist a small sanitized failure record for Research review."""
        if not isinstance(operation_id, str) or not operation_id.strip() or not isinstance(failure, str) or not failure.strip():
            raise ValueError("Failure session requires an operation and description")
        if phase not in {"stage", "deploy", "verify", "rollback"}:
            raise ValueError("Unknown adapter failure phase")
        destination = self.root / "runtime-evidence" / f"{operation_id}-failure.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps({"schema_version": 1, "adapter_id": self.manifest()["id"],
                                           "operation_id": operation_id, "phase": phase,
                                           "failure": failure.strip()[:2000],
                                           "recovery_started": bool(recovery_started)}, indent=2) + "\n", encoding="utf-8")
        return destination

    @staticmethod
    def recovery_report(operation_id: str, backup_id: str, *, readback_verified: bool,
                         rollback_verified: bool, failure_session: str = "") -> dict[str, Any]:
        if not operation_id.strip() or not backup_id.strip():
            raise ValueError("Recovery report requires operation and backup IDs")
        return {"schema_version": 1, "operation_id": operation_id, "backup_id": backup_id,
                "readback_verified": bool(readback_verified), "rollback_verified": bool(rollback_verified),
                "failure_session": failure_session, "recovery_state":
                "recovered" if rollback_verified else "recovery-required"}

    @staticmethod
    def validate(payload: dict[str, Any]) -> None:
        required = {
            "schema_version", "id", "name", "version", "process_mode",
            "loader", "game_build", "supported_setting_keys", "evidence",
            "loader_api_version",
            "backup_requirements", "mutation_scope", "verification_steps",
            "feature_state",
            "owned_package_id",
        }
        if not isinstance(payload, dict) or set(payload) != required:
            raise ValueError("Tuning adapter manifest has an invalid shape")
        if payload["schema_version"] != 1 or payload["process_mode"] != "separate":
            raise ValueError("Unsupported tuning adapter manifest")
        if payload["loader"] != "EML" or payload["loader_api_version"] != "1.3" or payload["game_build"] != "1076226":
            raise ValueError("Adapter is not compatible with the reviewed EML build")
        keys = payload["supported_setting_keys"]
        if keys != ["baseCritChance"]:
            raise ValueError("Only the evidenced scalar tuning key may be enabled")
        evidence = payload["evidence"]
        if not isinstance(evidence, dict) or evidence.get("write_ok") is not True \
                or evidence.get("readback_ok") is not True \
                or evidence.get("restore_ok") is not True \
                or evidence.get("panic") is not False \
                or evidence.get("probe_removed") is not True \
                or evidence.get("stable_profile_restored") is not True:
            raise ValueError("Adapter lacks complete reversible runtime evidence")
        if payload["feature_state"] != "experimental":
            raise ValueError("Adapter must remain experimental until behavior is verified")
        if payload["owned_package_id"] != "embervault.eml-tuning-adapter":
            raise ValueError("Adapter ownership is not recognized")

    def validate_runtime_context(self, *, loader: str, loader_api_version: str,
                                 game_build: str) -> dict[str, str]:
        """Fail closed unless the observed runtime matches reviewed evidence."""
        manifest = self.manifest()
        expected = {
            "loader": manifest["loader"],
            "loader_api_version": manifest["loader_api_version"],
            "game_build": manifest["game_build"],
        }
        observed = {
            "loader": str(loader),
            "loader_api_version": str(loader_api_version),
            "game_build": str(game_build),
        }
        if observed != expected:
            raise ValueError(
                "EML runtime is incompatible: expected "
                f"{expected['loader']} API {expected['loader_api_version']} build {expected['game_build']}"
            )
        return observed

    def prepare_operation(self, profile_type: str, backup_verified: bool,
                          game_running: bool, staged_value: float,
                          current_value: float) -> dict[str, Any]:
        """Build a fail-closed preview; this method never writes game state."""
        manifest = self.manifest()
        if profile_type != "research":
            raise ValueError("EML tuning requires the Research profile")
        if not backup_verified:
            raise ValueError("A verified recovery point is required")
        if game_running:
            raise ValueError("Close Enshrouded before preparing a tuning operation")
        if not isinstance(staged_value, (int, float)) or not 0.0 <= staged_value <= 1.0:
            raise ValueError("baseCritChance must be between 0.0 and 1.0")
        if not isinstance(current_value, (int, float)) or not 0.0 <= current_value <= 1.0:
            raise ValueError("The current adapter value is invalid")
        return {
            "adapter_id": manifest["id"],
            "loader": manifest["loader"],
            "game_build": manifest["game_build"],
            "resource": manifest["evidence"]["resource"],
            "field": manifest["evidence"]["field"],
            "old_value": float(current_value),
            "new_value": float(staged_value),
            "mutation_performed": False,
            "state": "prepared",
        }

    def execute_operation(self, preview: dict[str, Any], *, profile_type: str,
                          backup_verified: bool, game_running: bool,
                          mutation_enabled: bool = False) -> dict[str, Any]:
        """Refuse live writes until an explicitly owned adapter target exists.

        The EML probe already proves the in-process write path. This method is
        the Control Center transaction gate; it deliberately has no implicit
        target path or permission to modify the installed game.
        """
        if not mutation_enabled:
            raise PermissionError("The EML adapter is not enabled for live mutation")
        if profile_type != "research":
            raise PermissionError("EML tuning requires the Research profile")
        if not backup_verified:
            raise PermissionError("A verified recovery point is required")
        if game_running:
            raise PermissionError("Close Enshrouded before applying tuning")
        if preview.get("state") != "prepared" or preview.get("mutation_performed"):
            raise ValueError("Only an unused prepared preview can be executed")
        raise PermissionError("No owned EML adapter package target is configured")

    def render_payload(self, staged_value: float, operation_id: str) -> str:
        """Render an owned, transaction-specific EML Lua payload in memory."""
        manifest = self.manifest()
        if not isinstance(operation_id, str) or not operation_id.strip():
            raise ValueError("A transaction operation ID is required")
        if not isinstance(staged_value, (int, float)) or not 0.0 <= staged_value <= 1.0:
            raise ValueError("baseCritChance must be between 0.0 and 1.0")
        value = format(float(staged_value), ".12g")
        return "\n".join([
            "-- Generated by EmberVault Control Center; do not edit directly.",
            f"-- adapter={manifest['id']} operation={operation_id}",
            "local PREFIX = '[EMBERVAULT-EML-TUNING] '",
            f"print(PREFIX .. 'context|loader=EML|api={manifest['loader_api_version']}|build={manifest['game_build']}|operation={operation_id}')",
            "local resources = game.assets.get_resources_by_type('keen::BalancingTable') or {}",
            "if #resources ~= 1 then error(PREFIX .. 'expected_one_balancing_table|count=' .. tostring(#resources)) end",
            "local resource = resources[1]",
            "local original = resource.data.baseCritChance",
            f"resource.data.baseCritChance = {value}",
            "local readback = resource.data.baseCritChance",
            f"print(PREFIX .. 'write|field=baseCritChance|old=' .. tostring(original) .. '|new=' .. tostring(readback) .. '|operation={operation_id}')",
            "return {}",
            "",
        ])

    def stage_package(self, source_package: Path, staging_root: Path,
                      staged_value: float, operation_id: str) -> Path:
        """Create an isolated adapter package copy with a generated payload."""
        source_package = Path(source_package)
        if source_package.name != "eml-tuning-adapter" or not source_package.is_dir():
            raise ValueError("Only the owned EML adapter package may be staged")
        manifest = json.loads((source_package / "package.json").read_text(encoding="utf-8"))
        if manifest.get("ownership") != "embervault-control-center":
            raise PermissionError("Adapter package ownership is not recognized")
        destination = Path(staging_root) / f"{operation_id}-eml-tuning-adapter"
        if destination.exists():
            raise FileExistsError("Adapter staging destination already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_package, destination)
        (destination / "mod.lua").write_text(
            self.render_payload(staged_value, operation_id), encoding="utf-8"
        )
        return destination

    @staticmethod
    def parse_runtime_readback(log_text: str, operation_id: str) -> dict[str, Any]:
        """Parse one operation-bound context and readback pair."""
        marker = re.escape(f"operation={operation_id}")
        context_lines = [line for line in log_text.splitlines()
                         if re.search(rf"(?:^|[|\s]){marker}(?:$|\s)", line)
                         and "[EMBERVAULT-EML-TUNING] context|" in line]
        lines = [line for line in log_text.splitlines()
                 if re.search(rf"(?:^|[|\s]){marker}(?:$|\s)", line)
                 and "[EMBERVAULT-EML-TUNING] write|" in line]
        if len(context_lines) != 1:
            raise ValueError("Expected exactly one EML adapter runtime context line")
        if len(lines) != 1:
            raise ValueError("Expected exactly one EML adapter readback line")
        context = re.search(r"loader=([^|\s]+)\|api=([^|\s]+)\|build=([^|\s]+)", context_lines[0])
        if not context or (context.group(1), context.group(2), context.group(3)) != ("EML", "1.3", "1076226"):
            raise ValueError("EML adapter runtime context does not match reviewed evidence")
        match = re.search(r"field=([^|\s]+)\|old=([^|\s]+)\|new=([^|\s]+)", lines[0])
        if not match:
            raise ValueError("EML adapter readback is malformed")
        if match.group(1) != "baseCritChance":
            raise ValueError("EML adapter readback field is outside the reviewed scope")
        return {"operation_id": operation_id, "field": match.group(1), "loader": "EML",
                "loader_api_version": "1.3", "game_build": "1076226",
                "old_value": float(match.group(2)), "new_value": float(match.group(3)),
                "readback_verified": True}

    def verify_log_file(self, log_path: Path, operation_id: str,
                        expected_value: float, minimum_mtime: float | None = None) -> dict[str, Any]:
        """Verify one fresh EML log readback for the requested operation."""
        log_path = Path(log_path)
        if log_path.is_symlink():
            raise ValueError("Refusing to verify a symlinked EML runtime log")
        try:
            stat = log_path.stat()
            if stat.st_size > MAX_RUNTIME_LOG_BYTES:
                raise ValueError("The EML runtime log exceeds the verification size limit")
            text = log_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError("Unable to read the EML runtime log") from exc
        if minimum_mtime is not None:
            try:
                if stat.st_mtime < float(minimum_mtime):
                    raise ValueError("The EML runtime log predates adapter deployment")
            except OSError as exc:
                raise ValueError("Unable to inspect the EML runtime log timestamp") from exc
        result = self.parse_runtime_readback(text, operation_id)
        if abs(result["new_value"] - float(expected_value)) > 1e-9:
            raise ValueError("EML readback value does not match the staged value")
        return result | {"log_path": str(log_path), "status": "verified"}

    def deploy_staged_package(self, staged_package: Path, game_directory: Path,
                              *, game_running: bool) -> Path:
        """Deploy only the owned staged adapter to an empty mods destination."""
        if game_running:
            raise PermissionError("Close Enshrouded before deploying the adapter")
        staged_package = Path(staged_package)
        manifest = json.loads((staged_package / "package.json").read_text(encoding="utf-8"))
        if manifest.get("id") != "embervault.eml-tuning-adapter" \
                or manifest.get("ownership") != "embervault-control-center":
            raise PermissionError("Staged package ownership is not recognized")
        loader_manifest_path = staged_package / "mod.json"
        if not loader_manifest_path.is_file():
            raise ValueError("Staged adapter is missing its EML mod manifest")
        loader_manifest = json.loads(loader_manifest_path.read_text(encoding="utf-8"))
        if loader_manifest.get("id") != "embervault.eml-balancing-table" \
                or loader_manifest.get("entrypoint") != "mod.lua":
            raise ValueError("Staged EML manifest does not match the adapter contract")
        if not (staged_package / "mod.lua").is_file():
            raise ValueError("Staged adapter is missing its EML entrypoint")
        destination = Path(game_directory) / "mods" / manifest["id"]
        if destination.exists():
            raise FileExistsError("Adapter destination already exists; refusing to overwrite")
        created = False
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(staged_package, destination)
            (destination / ".embervault-managed.json").write_text(json.dumps({
                "package_id": manifest["id"],
                "managed_by": "embervault-control-center",
            }, indent=2) + "\n", encoding="utf-8")
            created = True
            return destination
        except (OSError, shutil.Error):
            if created or destination.exists():
                shutil.rmtree(destination, ignore_errors=True)
            raise

    def undeploy_adapter(self, game_directory: Path) -> None:
        """Remove only the adapter destination bearing EmberVault ownership."""
        destination = Path(game_directory) / "mods" / "embervault.eml-tuning-adapter"
        marker = destination / ".embervault-managed.json"
        if not destination.is_dir() or destination.is_symlink():
            raise ValueError("Managed adapter destination does not exist")
        metadata = json.loads(marker.read_text(encoding="utf-8"))
        if metadata.get("package_id") != "embervault.eml-tuning-adapter" \
                or metadata.get("managed_by") != "embervault-control-center":
            raise PermissionError("Refusing to remove an unowned adapter")
        shutil.rmtree(destination)

