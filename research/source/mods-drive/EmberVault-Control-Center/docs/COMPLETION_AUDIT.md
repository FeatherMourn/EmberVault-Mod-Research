# Completion audit

This document records what the current release evidence proves and what remains
outside the first-release mutation boundary.

## Verified in the Control Center repository

- Core composition, profiles, detection, settings, structured logs, operation
  tracking, compatibility checks, and hybrid module discovery are implemented.
- Save Manager supports inspection, verified backup, restore preview, safe
  restore, and recovery verification. It does not edit save contents directly.
- Package management supports import, profile enablement, compatibility
  reporting, conflict-free deployment, and ownership-protected removal.
- Game Settings support profile-scoped staged values, portable import/export,
  read-only audits, and the experimental evidence-backed EML adapter lifecycle:
  stage, deploy, verify, rollback, and restart recovery.
- Character, Trainer, Content Creator, and Research workflows are explicitly
  isolated and plan/design/read-only by contract where live mutation is not
  proven.
- Stage 8 research records support reproducibility, failures, promotion review,
  linked project context, operation tracking, and sanitized public export.
- The catalog handoff is sanitized, independently validated, packaged, and
  covered by CI.

## Release evidence

- 231 unit tests pass.
- Stage 11 Character Tools supports structured plans, verified-backup
  associations, validation, operation-tracked UI editing, and save-safe export.
- Stage 12 Trainer is guarded, backup-bound, separate-process, operation-tracked,
  and read-only/plan-only with timeout and recovery coverage.
- Stage 10 Content Creator projects support structured design data, validation,
  operation-tracked UI editing, and design-only exports without game mutation.
- Stage 9 knowledge records support metadata, references, local version history,
  operation-tracked editing, search, and sanitized public publication.
- The offscreen QML smoke test passes.
- A fresh wheel contains and verifies all 29 required release assets.
- Catalog generation and standalone catalog validation pass.
- Windows and Linux packaging/smoke paths are defined in CI.

## Intentionally incomplete or external

- General live gameplay tuning is not supported; only the reviewed EML scalar
  route is experimental and evidence-gated.
- Direct character/save/content mutation is not supported in the first release.
- Forums, moderation, accounts, and remote hosting belong to the EmberVault web
  repository and consume the validated catalog contract rather than living in
  this desktop repository.

These items are boundaries, not silently assumed completion claims. Promotion
requires new runtime evidence, a reviewed contract, recovery coverage, and an
explicit change to the relevant safety boundary.
