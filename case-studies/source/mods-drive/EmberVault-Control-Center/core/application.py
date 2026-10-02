"""Composition root for EmberVault Core services."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .game_detection import GameDetector
from .game_settings import GameSettingsService
from .characters import CharacterService
from .catalog import CatalogExportService
from .content import ContentProjectService
from .knowledge import KnowledgeService
from .launch import ModuleLaunchService
from .logging_service import StructuredLogService
from .modules import ModuleRegistry
from .operations import OperationService
from .packages import PackageService
from .profiles import ProfileService
from .research import ResearchService
from .risk import RiskGateService
from .save_manager import SaveManagerService
from .save_workflow import SaveWorkflowService
from .settings import SettingsService
from .troubleshooter import TroubleshooterService
from .trainer import TrainerPlanService
from .tuning_adapter import TuningAdapterService
from .promotion import PromotionService
from .migrations import MigrationService
from .community_sync import CommunitySyncService
from .distribution import DistributionService
from .release import ReleaseCandidateService


@dataclass
class EmbervaultRuntime:
    root: Path
    settings: SettingsService
    profiles: ProfileService
    logs: StructuredLogService
    operations: OperationService
    saves: SaveManagerService
    modules: ModuleRegistry
    game: GameDetector
    save_workflow: SaveWorkflowService
    packages: PackageService
    troubleshooter: TroubleshooterService
    game_settings: GameSettingsService
    research: ResearchService
    knowledge: KnowledgeService
    characters: CharacterService
    risk: RiskGateService
    launcher: ModuleLaunchService
    catalog: CatalogExportService
    content: ContentProjectService
    trainer: TrainerPlanService
    tuning_adapter: TuningAdapterService
    promotion: PromotionService
    migrations: MigrationService
    community_sync: CommunitySyncService
    distribution: DistributionService
    release: ReleaseCandidateService

    @classmethod
    def create(cls, root: Path) -> "EmbervaultRuntime":
        root = Path(root)
        runtime = cls(
            root=root,
            settings=SettingsService(root),
            profiles=ProfileService(root),
            logs=StructuredLogService(root / "logs" / "events.jsonl"),
            operations=OperationService(root / "operations.jsonl"),
            saves=SaveManagerService(root),
            modules=ModuleRegistry(root / "modules"),
            game=GameDetector(),
            save_workflow=None,  # wired immediately below after shared services exist
            packages=None,  # wired immediately below after profiles exist
            troubleshooter=None,
            game_settings=None,
            research=None,
            knowledge=None,
            characters=None,
            risk=None,
            launcher=None,
            catalog=None,
            content=None,
            trainer=None,
            tuning_adapter=None,
            promotion=None,
            migrations=None,
            community_sync=None,
            distribution=None,
            release=None,
        )
        runtime.save_workflow = SaveWorkflowService(runtime.saves, runtime.operations, runtime.logs)
        runtime.profiles.ensure_defaults()
        runtime.packages = PackageService(root, runtime.profiles)
        runtime.packages.discover()
        runtime.troubleshooter = TroubleshooterService(
            root, runtime.settings, runtime.profiles, runtime.modules, runtime.packages, runtime.game
        )
        runtime.game_settings = GameSettingsService(runtime.profiles)
        runtime.research = ResearchService(root)
        runtime.knowledge = KnowledgeService(root)
        # Character plans remain storage-only by default; guarded callers can
        # inject Save Manager explicitly when a verified backup is required.
        runtime.characters = CharacterService(root)
        runtime.risk = RiskGateService(runtime.saves)
        runtime.tuning_adapter = TuningAdapterService(root)
        runtime.promotion = PromotionService(root)
        runtime.migrations = MigrationService(root)
        runtime.launcher = ModuleLaunchService(runtime.modules, runtime.risk, runtime.promotion)
        runtime.catalog = CatalogExportService(root, runtime.modules, runtime.packages, runtime.knowledge, runtime.research, runtime.tuning_adapter, runtime.promotion)
        runtime.content = ContentProjectService(root)
        runtime.trainer = TrainerPlanService(root, runtime.saves)
        runtime.catalog.set_content(runtime.content)
        runtime.community_sync = CommunitySyncService(root, runtime.catalog)
        runtime.distribution = DistributionService(root)
        runtime.release = ReleaseCandidateService(root, runtime.promotion)
        runtime.modules.discover()
        runtime.logs.info("EmberVault Core initialized")
        return runtime

    def health(self) -> dict:
        settings = self.settings.load()
        installation = self.game.detect(Path(settings.game_path)) if settings.game_path else None
        return {
            "core": "ready",
            "game": installation.to_dict() if installation else None,
            "profiles": len(self.profiles.list()),
            "modules": len(self.modules.discover()),
            "backups": len(self.saves.list_backups()),
            "packages": len(self.packages.list()),
            "research": len(self.research.list()),
            "knowledge": len(self.knowledge.entries()),
            "content_projects": len(self.content.list()),
            "trainer_plans": len(self.trainer.list()),
        }
