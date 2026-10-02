# Roadmap status

## Working

- Frozen terminology and module-boundary contracts in
  `docs/TERMINOLOGY.md` and `docs/MODULE_BOUNDARIES.md`.
- Core composition, settings, game detection, profiles, structured logs, and
  operation tracking.
- Save Manager inspection, verified backup, re-verification, restore preview,
  safe restore, and post-restore verification.
- Contract-discovered embedded/separate module framework.
- PySide6/Qt Quick shell with Home, Profiles, Mods, Game Settings,
  Troubleshooter, Character Editor, Trainer, Content Creator, Research Lab,
  Knowledge, Modules, and Activity workspaces.
- Profile-scoped package discovery, folder/ZIP import, enablement, compatibility
  reporting, safe removal, conflict-free deployment, and ownership-protected
  undeploy, plus read-only inspection of existing external `mod.json` mods and
  managed, external, or invalid game destinations in the Mods workspace.
- Isolated research records/evidence, character projects, content projects, and
  backup-bound Trainer plans, plus versioned public catalog export.
- Public catalog module records now preserve the validated embedded/separate
  process boundary for website consumers.
- Guarded Trainer, Research, and Content Creator process workflows with UI
  launch controls, captured worker output, timeout termination, and audited
results. Trainer now has a backup-bound plan layer, while its worker remains
deliberately non-mutating; Research includes a
  bounded evidence probe, Trainer includes a readiness audit, and Content
  Creator includes a design-boundary audit.

## Guarded or incomplete

- Gameplay settings are validated, profile-scoped staged values and can be
  exported or imported as portable manifests. The reviewed EML adapter route
  can stage, deploy, and verify one evidence-backed scalar in a separate
  process, but general live tuning and automatic in-game application remain
  unsupported. The boundary and evidence are documented in
  `docs/GAME_SETTINGS_BOUNDARY.md`.
- Character projects can be exported as plan-only manifests; content projects
  can be exported as design-only manifests, while direct game mutation is not
  implemented.
- Catalog synchronization to the public EmberVault repository is implemented
  through the validated export and `tools/sync_catalog.py`; community forums,
  moderation, and remote catalog hosting remain outside the desktop repository
  and use the export contract.
- The seeded Trainer performs a bounded, read-only readiness audit; the Research
  worker performs a bounded filesystem observation probe; and Content Creator
  performs a bounded design-boundary audit. The tuning-audit worker performs a
  bounded review of staged settings without applying them to the game. Worker
  launch paths are covered by success, denial, and timeout tests.

## Stage 14 integration status

- Cross-module handoffs use the versioned integration context carrying
  operation ID, profile ID, capability state, and recovery expectation.
- Mods deployment actions carry profile and compatibility state; incompatible
  builds are blocked before deployment.
- Research records accept operation-bound sanitized runtime adapter evidence,
  and content projects can reference stable research IDs.
- Save Manager exposes the shared verified-backup handoff used by Trainer and
  optionally by Character Tools; direct save mutation remains unsupported.
- Catalog and release verifiers enforce the integration-context contract.

## Stage 17 governance status

- The Control Center includes a Capability Governance workspace with lifecycle
  state, evidence readiness, ownership, missing requirements, and promotion history.
- Governance review is read-only; promotion remains operation-tracked and
  fail-closed through the promotion evidence contract.
- Runtime adapter availability and compatibility evidence remain explicit rather
  than being inferred as stable capability.

## Stage 19 Mods Management status

- Mods Management includes dependency graphs, profile comparison, batch package
  actions, compatibility-aware deployment, managed/external distinction, profile
  portability, update detection, and reviewable upgrade staging.
- Upgrade staging never replaces an installed package automatically; the staged
  manifest remains subject to explicit review and existing ownership gates.

## Stage 20 migration status

- Local JSON data can be previewed, version-stamped, backed up, migrated,
  quarantined when corrupt, and rolled back from a migration backup.
- Migration is exposed through a preview-first, operation-tracked Control Center
  workflow and remains separate from game/save mutation.

## Release evidence

- Python unit suite currently covers the Core services, workflows, module gates,
  profile isolation, package contracts, packaging assets, and installed-process
  contracts, strict manifest validation, and interrupted deployment cleanup
  ownership inspection, interrupted deployment cleanup, and research
  publication retraction safeguards (229 tests). Knowledge now supports
  structured metadata, version history, references, and sanitized publication.
- Content Creator supports furniture and other design projects with asset
  references, materials, dimensions, recipe/registration plans, compatibility
  notes, validation, and design-only exports (230 tests).
- Character Tools supports structured build goals, progression, equipment and
  skill notes, verified-backup associations, validation, and plan-only exports
  without save mutation (231 tests).
- Trainer provides research-profile and verified-backup gates, plan-only target
  sessions, separate-process readiness audits, timeout/crash handling, tracked
  operations, and recovery guidance.
- QML is smoke-tested through an offscreen Qt application.
- Wheels have been built and installed into isolated temporary targets; the
  packaged launcher passes its offscreen smoke test, which asserts discovery of
  five modules and eight knowledge entries. The package-manifest schema is
  present in the installed wheel data.
- Save Manager remains inspection/backup/verification/restore-only.
- A fresh wheel build has passed release-asset verification with all 29 required
  packaged assets, and the offscreen launcher smoke test passes. The default
  catalog sync command includes the reviewed adapter and seeded knowledge assets;
  isolated exports can still provide `--data-root` explicitly.
- CI also generates and independently validates a catalog handoff on every
  verification run.
