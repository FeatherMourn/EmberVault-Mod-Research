# EmberVault Control Center Roadmap

This document is the staged development roadmap for EmberVault Control Center.
It is intentionally version-controlled with the project so the plan remains
available alongside the implementation.

## Development rule

Build modules as complete vertical slices:

```text
Contract
→ Safety boundary
→ Core service
→ Backend wiring
→ QML interface
→ Operation tracking
→ Recovery behavior
→ Tests
→ Catalog integration
→ Packaging
→ Documentation
```

The shared foundation should receive changes only when a real module exposes a
missing shared capability.

## Stage 1 — Foundation and architecture

Status: complete.

- Freeze terminology and naming.
- Define module boundaries.
- Establish the safety model.
- Define profiles and isolation rules.
- Define embedded versus separate-process behavior.
- Preserve the legacy EnshroudedModHub repository as reference material only.
- Define the Core contracts.

Exit criteria:

- Architecture and safety boundaries are documented.
- Legacy UI architecture is not reused.
- Module ownership and process boundaries are explicit.

## Stage 2 — EmberVault Core

Status: complete.

- Game detection.
- Application settings.
- Profiles.
- Compatibility checks.
- Structured logging.
- Operation tracking.
- Risk gates.
- Backup and recovery services.
- Module discovery.

Exit criteria:

- Core services operate independently of the UI.
- Operations are traceable.
- Profiles are isolated.
- Recovery behavior is testable.

## Stage 3 — Control Center shell

Status: complete.

- PySide6 desktop application.
- Qt Quick/QML shell.
- Navigation and Home dashboard.
- Activity history.
- Module registration.
- Embedded module support.
- Separate worker support.

Exit criteria:

- The application launches.
- QML loads successfully.
- Modules can register and appear.
- Separate workers can return results and terminate safely.

## Stage 4 — Save Manager

Status: complete.

- Save inspection.
- Verified backup creation.
- Backup re-verification.
- Restore preview.
- Safe restore.
- Recovery verification.
- Corruption and ownership safeguards.

First-release boundary: Save Manager does not directly edit save contents.

Exit criteria:

- Restore requires explicit confirmation.
- Recovery can be verified.
- No direct save editing exists.

## Stage 5 — Module framework standardization

Status: complete; maintain through module work.

- Standard module manifest.
- Standard module lifecycle.
- Standard operation and result formats.
- Capability states: stable, verified, experimental, research-only, blocked.
- Standard testing template.
- Standard catalog fields.

Exit criteria:

- A new module can be created from a documented template.
- Every module has a contract, safety boundary, tests, and UI registration path.

## Stage 6 — EML runtime adapter

Status: complete for the experimental EML milestone; promotion work remains.

- EML manifest and build compatibility.
- Explicit EML API version compatibility (`1.3` for the reviewed evidence).
- Supported field declarations.
- Research-profile gate.
- Verified-backup gate.
- Game-closed gate.
- Payload staging.
- Owned deployment.
- Runtime readback.
- Operation-bound runtime context evidence for loader, API, and game build.
- Rollback.
- Restart recovery.
- Catalog integration.

Next work:

- Test additional valid values.
- Test repeated launches.
- Test build mismatches.
- Expand rollback and failure evidence.
- Keep the adapter separate from general Game Settings.

The current supported route is limited to the evidenced `baseCritChance`
field and remains experimental.

## Stage 7 — Mods Management

Status: complete for the planned first-release scope; future work may add
additional package formats and deployment adapters.

- Folder and ZIP import.
- Manifest validation.
- Dependencies.
- Compatibility checks.
- Profile enablement.
- Deployment planning.
- Conflict detection.
- Ownership markers.
- Safe undeployment.
- External unmanaged-mod inspection.
- Versioned ownership records and read-only managed/external/unsafe destination
  inspection.

Exit criteria:

- Unowned content is never overwritten or removed.
- Deployments are reversible.
- Profile isolation works.
- Failed deployments roll back safely.

Verification: 226 tests pass, the offscreen launcher smoke test passes, the
fresh wheel contains all 27 required assets, and the synchronized catalog
passes standalone validation.

## Stage 8 — Research and Development

Status: complete for the planned first-release scope; future work may expand
collaboration and richer evidence attachments.

- Experiment records.
- Hypotheses.
- Build and version context.
- Evidence and reproduction steps.
- Failure records.
- Research-only profiles.
- Promotion reviews.
- Sanitized research exports.
- Records now preserve build/version context, reproduction steps, failure
  records, and promotion-review state without exporting private evidence text.
- Research actions are operation-tracked, profile-scoped, linked to package,
  module, and knowledge context, and protected by publication retraction when
  material context changes.

Exit criteria:

- Experiments are reproducible or clearly documented as failed.
- Evidence can link to adapters, mods, and knowledge articles.

Verification: 228 tests pass, the offscreen launcher smoke test passes, the
fresh wheel contains all 27 required assets, and the synchronized catalog
passes standalone validation.

## Stage 9 — Knowledge Base

Status: complete for the planned first-release scope; future work may add
 richer collaboration and remote editorial workflows.

- Articles.
- Categories and tags.
- Search.
- Cross-links.
- Draft and published states.
- Version history.
- Evidence references.
- Public export.
- Articles now support tags, cross-links, evidence references, version history,
  metadata search, operation-tracked editing, and sanitized catalog export.

Exit criteria:

- Private notes remain separate from published knowledge.

Verification: 229 tests pass, the offscreen launcher smoke test passes, the
fresh wheel contains all required assets, and the synchronized catalog passes
standalone validation.
- Articles can reference research and mod records.
- Public records contain no private paths or sensitive data.

## Stage 10 — Content Creator

Status: complete for the planned first-release scope; future work may add
reviewed asset tooling without crossing the mutation boundary.

- Furniture projects.
- Asset references.
- Materials and dimensions.
- Recipes and registration plans.
- Compatibility notes.
- Design validation.
- Design-only exports.

First-release boundary: no direct live game mutation or untracked asset
injection.

Verification: 230 tests pass, the offscreen launcher smoke test passes, the
fresh wheel contains all required assets, and design exports remain separate
from game and save state.

## Stage 11 — Character tools

Status: complete for the planned first-release scope; direct save mutation
remains outside the boundary.

- Character profiles.
- Build goals.
- Progression plans.
- Equipment and skill notes.
- Backup associations.
- Validation.
- Plan exports.

Direct save mutation requires a separate evidence and safety review.

Verification: 231 tests pass, the offscreen launcher smoke test passes, the
fresh wheel contains all required assets, and character plans remain separate
from live save contents.

## Stage 12 — Trainer

Status: complete for the planned first-release scope; future live trainer
mutation requires a separate evidence and safety review.

- Trainer targets.
- Backup-bound sessions.
- Readiness checks.
- Separate-process execution.
- Timeout and crash handling.
- Operation tracking.
- Recovery instructions.

The first release remains read-only or plan-only.

Verification: 231 tests pass, the offscreen launcher smoke test passes, the
fresh wheel contains all required assets, and trainer plans remain bound to
verified backups without mutating saves or live game data.

## Stage 13 — EmberVault website and community platform

Status: separate web-repository workstream.

- Public mod catalog.
- Mod detail pages.
- Research archive.
- Knowledge base.
- Shared project pages.
- Forums.
- User accounts and roles.
- Moderation.
- Submission and review workflows.
- Catalog synchronization.

The desktop Control Center publishes sanitized records; it does not become the
entire community platform.

## Stage 14 — Cross-module integration

Connect modules through contracts rather than private implementation details.

Required relationships:

- Mods ↔ Profiles.
- Mods ↔ Compatibility.
- Research ↔ Knowledge.
- Research ↔ Runtime Adapters.
- Content Creator ↔ Research.
- Character Tools ↔ Save Manager.
- Trainer ↔ Save Manager.
- All modules ↔ Operations.
- All modules ↔ Catalog Export.

Every cross-module action should preserve an operation ID, profile ID,
capability state, and recovery expectation.

## Stage 15 — Release hardening

- Windows testing.
- Linux testing.
- Clean installation testing.
- Installed-wheel testing.
- QML smoke tests.
- Contract validation.
- Corrupt-data tests.
- Interrupted-operation tests.
- Rollback tests.
- Upgrade and migration tests.
- User and recovery documentation.
- Release notes.

Exit criteria:

- Fresh installs work.
- Existing user data migrates safely.
- Packaging and CI are green.
- Release assets validate.

## Stage 16 — Capability promotion

Capabilities move through:

```text
Research-only
→ Experimental
→ Verified
→ Stable
```

Promotion requires current-build evidence, reproducibility, runtime
confirmation, recovery testing, compatibility documentation, clear ownership,
and rollback behavior.

## Recommended execution order from the current baseline

1. Finish and reuse the module-development template.
2. Continue EML adapter evidence and compatibility testing.
3. Harden Mods Management.
4. Expand Research and Evidence workflows.
5. Improve the Knowledge Base.
6. Build Content Creator design tools.
7. Expand Character planning.
8. Harden Trainer isolation.
9. Continue the EmberVault website/community platform.
10. Add cross-module integration.
11. Perform final release hardening.
12. Promote proven capabilities.

## Forward roadmap: post-Stage 16

The foundational roadmap is complete through Stage 16. The next stages shift
from architecture and release hardening toward product expansion and ecosystem
integration.

### Stage 17 — Capability Governance

- Capability dashboard.
- Research-only, Experimental, Verified, and Stable status display.
- Promotion evidence checklist.
- Owner, compatibility, rollback, and promotion history views.
- Missing-evidence and rejection explanations.
- UI controls for reviewing promotion readiness.

Goal: make capability status understandable and auditable inside Control Center.

### Stage 18 — Runtime Adapter Expansion

- Expand beyond the current narrow EML adapter.
- Add supported gameplay settings and current-build compatibility matrices.
- Add adapter-specific evidence, failure-session, recovery, and rollback reports.
- Add adapter version management and future Shroudtopia adapter boundaries.

Goal: support more gameplay tuning without weakening evidence requirements.

### Stage 19 — Mods Management 2.0

- Improve the mod library, dependencies, compatibility matrix, and load-order planning.
- Add profile comparison, batch actions, update detection, profile import/export,
  and safer package upgrades.

Goal: make mod installation and profile management practical for daily use.

### Stage 20 — Schema Migration and Data Recovery

- Version every local record schema.
- Add migration handlers, previews, reports, and rollback.
- Back up data before migration and quarantine corrupt records.
- Add upgrade tests across historical versions.

Goal: allow users to update EmberVault without losing work or configuration.

### Stage 21 — Content Creator 2.0

- Expand furniture, building, recipe, asset, material, dimension, and registration workflows.
- Add research-linked design decisions, exportable design packages, and previews.
- Preserve the separation between design output and live installation.

Goal: make content development productive while retaining design-only safety boundaries.

### Stage 22 — Research and Knowledge Collaboration

- Add experiment templates, evidence attachments, runtime log imports, comparison runs,
  build tracking, reproducibility scoring, and research reports.
- Improve research-to-knowledge promotion, discussion notes, search, and filtering.

Goal: make research repeatable, discoverable, and useful to the modding community.

### Stage 23 — Character Tools and Trainer Expansion

- Add character build templates, equipment comparison, progression simulation,
  build versioning, and save-linked planning.
- Expand Trainer test plans, process isolation, recovery simulation, and evidence gates.

Goal: improve planning tools without prematurely enabling unsafe mutation.

### Stage 24 — Website and Community Integration

- Connect catalog publishing, research submissions, project publishing, knowledge
  synchronization, discussion links, versioned records, and conflict handling.
- Keep authentication, moderation, and remote community authority in the EmberVault website.

Goal: connect Control Center to the broader EmberVault community and research hub.

### Stage 25 — Distribution and Updates

- Add Windows and Linux distribution packages, update checking, release channels,
  backup-before-update, migration previews, repair installation, and data-preserving uninstall.

Goal: move from developer installation to a user-friendly product release.

### Stage 26 — Stable Capability Release

- Promote only evidence-backed capabilities to Stable.
- Finalize compatibility, recovery, user, and release documentation.
- Prepare a public version 1.0 release candidate.

Goal: release a dependable first public version without claiming unsupported live mutation.

### Recommended forward execution order

1. Capability Governance.
2. Runtime Adapter Expansion.
3. Mods Management 2.0.
4. Schema Migration and Data Recovery.
5. Content Creator 2.0.
6. Research and Knowledge Collaboration.
7. Character Tools and Trainer Expansion.
8. Website and Community Integration.
9. Distribution and Updates.
10. Stable Capability Release.
