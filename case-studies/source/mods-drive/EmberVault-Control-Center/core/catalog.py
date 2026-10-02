"""Portable catalog export for the Ember Vault website and research hub."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .knowledge import KnowledgeService
from .modules import ModuleRegistry
from .packages import PackageService
from .research import ResearchService
from .content import ContentProjectService
from .storage import write_json_atomic


class CatalogExportService:
    def __init__(self, root: Path, modules: ModuleRegistry, packages: PackageService,
                 knowledge: KnowledgeService, research: ResearchService, tuning_adapter=None, promotion=None):
        self.root = Path(root)
        self.modules = modules
        self.packages = packages
        self.knowledge = knowledge
        self.research = research
        self.tuning_adapter = tuning_adapter
        self.promotion = promotion
        self.content = None

    def set_content(self, content: ContentProjectService) -> None:
        self.content = content

    def build(self) -> dict:
        packages = sorted(self.packages.list(), key=lambda item: item.id)
        modules = sorted(self.modules.discover().values(), key=lambda item: item.id)
        knowledge = sorted((item for item in self.knowledge.entries() if item.published), key=lambda item: item.id)
        research = sorted((item for item in self.research.list() if item.published), key=lambda item: item.id)
        content = sorted((item for item in (self.content.list() if self.content else []) if item.published), key=lambda item: item.id)
        promotions = []
        if self.promotion:
            for item in self.promotion.decisions():
                evidence = item["evidence"]
                promotions.append({"capability_id": evidence.get("capability_id"), "target_state": item.get("target_state"), "current_build": evidence.get("current_build"), "source_research_id": evidence.get("source_research_id", "")})
        tuning_adapters = []
        if self.tuning_adapter:
            try:
                manifest = self.tuning_adapter.manifest()
            except ValueError:
                manifest = None
            if manifest:
                tuning_adapters.append({
                    "id": manifest["id"], "name": manifest["name"], "version": manifest["version"],
                    "loader": manifest["loader"], "game_build": manifest["game_build"],
                    "supported_setting_keys": manifest["supported_setting_keys"],
                    "feature_state": manifest["feature_state"], "process_mode": manifest["process_mode"],
                    "evidence_state": "reversible-runtime-evidence",
                })
        public_modules = []
        for item in modules:
            public_modules.append({
                "id": item.id, "name": item.name, "version": item.version,
                "publisher": item.publisher, "executable": item.executable,
                "minimum_core_version": item.minimum_core_version,
                "capabilities": list(item.capabilities), "feature_state": item.feature_state,
                "entrypoint": item.entrypoint, "process_mode": item.process_mode,
                "path": None,
            })
        return {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "contract_versions": {"module_manifest": 1, "package_manifest": 1, "research_record": 1, "content_project": 1, "tuning_adapter": 1, "integration_context": 1},
            "packages": [asdict(item) | {"path": None} for item in packages],
            "modules": public_modules,
            "tuning_adapters": tuning_adapters,
            "knowledge": [{"id": item.id, "title": item.title, "category": item.category,
                           "summary": item.summary, "content": item.content,
                           "published_at": item.published_at or "seeded", "tags": list(item.tags),
                           "related_ids": list(item.related_ids), "evidence_refs": list(item.evidence_refs),
                           "version": item.version} for item in knowledge],
            "research": [{"id": item.id, "title": item.title, "hypothesis": item.hypothesis,
                          "status": item.status, "evidence_count": len(item.evidence),
                          "created_at": item.created_at, "published_at": item.published_at,
                          "game_build": item.game_build, "game_version": item.game_version,
                          "reproduction_step_count": len(item.reproduction_steps),
                          "failure_count": len(item.failures), "promotion_status": item.promotion_status,
                          "linked_package_count": len(item.linked_package_ids),
                          "linked_module_count": len(item.linked_module_ids),
                          "linked_knowledge_count": len(item.linked_knowledge_ids)} for item in research],
            "content_projects": [{"id": item.id, "name": item.name, "status": item.status,
                                  "published_at": item.published_at} for item in content],
            "promotions": promotions,
        }

    @staticmethod
    def validate(payload: dict) -> None:
        """Validate the public handoff without requiring a web runtime."""
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise ValueError("Catalog schema version must be 1")
        required = ("generated_at", "contract_versions", "packages", "modules", "tuning_adapters", "knowledge", "research", "content_projects", "promotions")
        if any(key not in payload for key in required) or set(payload) != {"schema_version", *required}:
            raise ValueError("Catalog is missing a required collection")
        if not isinstance(payload["generated_at"], str) or not payload["generated_at"].strip():
            raise ValueError("Catalog generation timestamp is required")
        if not isinstance(payload["contract_versions"], dict):
            raise ValueError("Catalog contract versions must be an object")
        for key in ("module_manifest", "package_manifest", "research_record", "content_project", "tuning_adapter", "integration_context"):
            version = payload["contract_versions"].get(key)
            if not isinstance(version, int) or isinstance(version, bool) or version < 1:
                raise ValueError(f"Catalog contract version is missing: {key}")
        for collection in ("packages", "modules", "tuning_adapters", "knowledge", "research", "content_projects", "promotions"):
            if not isinstance(payload[collection], list):
                raise ValueError(f"Catalog collection is not an array: {collection}")
        for collection in ("packages", "modules"):
            for item in payload[collection]:
                if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
                    raise ValueError(f"{collection.title()} catalog records must contain an id")
                if collection == "modules" and item.get("process_mode") not in {"embedded", "separate"}:
                    raise ValueError("Module catalog records must declare embedded or separate process_mode")
        for item in payload["tuning_adapters"]:
            required_fields = {"id", "name", "version", "loader", "game_build", "supported_setting_keys", "feature_state", "process_mode", "evidence_state"}
            if not isinstance(item, dict) or set(item) != required_fields:
                raise ValueError("Tuning adapter catalog records must match the public contract")
            if any(not isinstance(item[key], str) or not item[key].strip() for key in ("id", "name", "version", "loader", "game_build", "feature_state", "evidence_state")):
                raise ValueError("Tuning adapter catalog records must contain non-empty fields")
            if not isinstance(item["supported_setting_keys"], list) or not all(isinstance(key, str) and key.strip() for key in item["supported_setting_keys"]):
                raise ValueError("Tuning adapter supported keys must be strings")
            if item["process_mode"] not in {"embedded", "separate"}:
                raise ValueError("Tuning adapter records must declare embedded or separate process_mode")
        for item in payload["knowledge"]:
            if not isinstance(item, dict) or set(item) != {"id", "title", "category", "summary", "content", "published_at", "tags", "related_ids", "evidence_refs", "version"}:
                raise ValueError("Knowledge catalog records must match the public contract")
            if any(not isinstance(item[key], str) or not item[key].strip()
                   for key in ("id", "title", "category", "summary", "content", "published_at")):
                raise ValueError("Knowledge catalog records must contain non-empty fields")
            if any(not isinstance(item[key], list) or not all(isinstance(value, str) and value.strip() for value in item[key])
                   for key in ("tags", "related_ids", "evidence_refs")) or not isinstance(item["version"], int) or item["version"] < 1:
                raise ValueError("Knowledge catalog metadata is invalid")
        for item in payload["research"]:
            required_fields = {"id", "title", "hypothesis", "status", "evidence_count", "created_at", "published_at",
                               "game_build", "game_version", "reproduction_step_count", "failure_count", "promotion_status",
                               "linked_package_count", "linked_module_count", "linked_knowledge_count"}
            if not isinstance(item, dict) or set(item) != required_fields:
                raise ValueError("Research catalog records must remain sanitized")
            if item["status"] != "completed" or not isinstance(item["evidence_count"], int) or item["evidence_count"] < 1:
                raise ValueError("Research catalog records must be completed with evidence")
            if item["promotion_status"] not in {"not-requested", "requested", "approved", "rejected"}:
                raise ValueError("Research catalog promotion status is invalid")
            for key in ("reproduction_step_count", "failure_count", "linked_package_count", "linked_module_count", "linked_knowledge_count"):
                if not isinstance(item[key], int) or item[key] < 0:
                    raise ValueError("Research catalog counts must be non-negative integers")
        for item in payload["content_projects"]:
            if not isinstance(item, dict) or set(item) != {"id", "name", "status", "published_at"}:
                raise ValueError("Content catalog records must remain sanitized")
            if item["status"] != "ready":
                raise ValueError("Only ready content projects may be public")
        for item in payload["promotions"]:
            if not isinstance(item, dict) or set(item) != {"capability_id", "target_state", "current_build", "source_research_id"}:
                raise ValueError("Promotion catalog records must remain sanitized")
            if item["target_state"] not in {"research-only", "experimental", "verified", "stable"}:
                raise ValueError("Promotion catalog state is invalid")

    def export(self, destination: Path) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = self.build()
        self.validate(payload)
        write_json_atomic(destination, payload)
        return destination

    def sync_to_directory(self, destination: Path) -> Path:
        """Write a validated repository-ready snapshot into a chosen folder."""
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        return self.export(destination / "embervault-catalog.json")
