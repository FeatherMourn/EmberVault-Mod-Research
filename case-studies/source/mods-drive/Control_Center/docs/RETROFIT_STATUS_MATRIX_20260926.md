# Control Center Retrofit Status Matrix

This matrix records the current evidence boundary for the 50 requested
upgrades. “Implemented” means the Control Center has a tested local path;
“research-only” means it is deliberately not treated as runtime-proven;
“verified” additionally has evidence from the controlled EML/KFC bed fixture.

| # | Upgrade | Status | Evidence / boundary |
|---:|---|---|---|
| 1 | Unified GUI entry point | Implemented | `gui/launcher.py`; legacy routes preserved, headless status mode added, and Content Studio exposes resource import/validation workflows. |
| 2 | Service layer | Implemented | `core/` services mediate UI and files. |
| 3 | Game-build detection | Implemented | `GameBuildDetector` prefers explicit metadata and authoritative EML type-registry logs; ignores arbitrary cache timestamps and uses Steam only as fallback. |
| 4 | Runtime health detection | Implemented | Authoritative `.eml.log` parsing honors structured `ERROR`/`FATAL`/`PANIC` levels, preserves multiline details, and distinguishes failed startup from degraded recovery after later success events. |
| 5 | Feature states | Implemented | Stable/experimental/research-only/disabled gates. |
| 6 | Dependencies | Implemented | `ModuleGraphService`. |
| 7 | Load order | Implemented | Dependency graph plus priority ordering. |
| 8 | Conflict detection | Implemented | Manifest resource-edit conflicts. |
| 9 | Automatic quarantine | Implemented | Single-candidate crash recovery; ambiguous/live-game cases require review, and the same failure log is processed only once. |
| 10 | Crash-safe rollback | Implemented | Full owned-package snapshots and recovery with fail-closed process-state checks. |
| 11 | Transactional deployment | Implemented | Staging, ownership, verify, rollback; project, resource, asset, and release operations restore/avoid partial state on commit failure. |
| 12 | Versioned backups | Implemented | Installer and local third-party replacement backups use timestamped restore-point directories, preserve prior versions, expose a restore-point catalog, recognize legacy pre-versioned backups safely, and provide a stopped-game, ownership-checked restore operation. |
| 13 | Build compatibility profiles | Implemented | Persistent build snapshot and migration plan. |
| 14 | KFC schema diff | Implemented | `ResourceInspector.compare`. |
| 15 | Update warnings | Implemented | Build-change detection; update-mode migration marks undeclared modules for review and incompatible modules for disable. |
| 16 | API negotiation | Implemented | Canonical capability registry. |
| 17 | Legacy API shims | Implemented | Manifest capability adapters. |
| 18 | Automatic IDs | Implemented | Namespace-scoped deterministic numeric IDs. |
| 19 | Deterministic GUIDs | Implemented | UUID5 identity service. |
| 20 | Namespace ownership | Implemented | Persistent identity claims. |
| 21 | Donor schema validation | Implemented | Clone plans and project validation fail closed on donor/candidate type changes; `mod.json`/`content.json` may declare `donor_validation` file pairs. |
| 22 | Resource inspector/browser | Implemented | Read-only scan, GUI summary, and primary-dashboard resource import entry point. |
| 23 | Resource cloning wizard | Implemented | Non-destructive GUI clone-plan export. |
| 24 | Recipe editor | Implemented | Content Studio exposes non-destructive recipe editing; the backend applies allowlisted field/type/range validation and preserves the donor, alongside safe recipe cloning. |
| 25 | Typed-array-safe helpers | Verified | Replacement/cloned-set strategy covered by tests and bed result. |
| 26 | UI catalog editor | Verified | `FbUiBundle` cloned-set path; never appends fixed entries. |
| 27 | Custom localization payloads | Runtime verified / UI research-only | Latest isolated live build `1076226` catalog confirms direct `LocaTag`, matching locale collection, binary payload, item/recipe registration, and cloned UI-set link; visual UI consumption remains unproven. |
| 28 | Localization fallback/validation | Implemented | Deterministic keys with collision rejection, normalized language/region fallback, and saved-payload validation wired into content-project validation. |
| 29 | Custom visual assets | Implemented | Transactional hashed icon/texture import with kind, extension, size, symlink, and unlisted-file checks. |
| 30 | Model/asset packaging | Implemented | Models/audio accept explicit supported formats, perform lightweight glTF/GLB/OBJ container checks, and record `packaged-unverified-engine-import`; manifest verification is fail-closed, while engine import remains unverified. |
| 31 | Content project generator | Implemented | Validator-ready self-contained project plus transactional JSON resource import and generation rollback with deterministic identity assignment and package regeneration. |
| 32 | Mod template generator | Implemented | Generated EML entrypoint and helper. |
| 33 | Existing-layout import/export | Implemented | Safe migration service with provenance; secrets and symbolic links are rejected. |
| 34 | Hash manifests | Implemented | Package and asset SHA-256/size verification; malformed entries, unlisted files, and symlinks are rejected. Package paths are normalized and semantic versions are required. |
| 35 | Dependency/capability declarations | Implemented | Module/package manifests and release metadata carry declarations; manifest shape is validated and local installation blocks missing, malformed, or version-incompatible dependencies. |
| 36 | Pre-launch validation | Implemented | Review/apply blocks invalid content, including donor-schema and capability declaration errors; resource import rolls back on validation failure and installer rejects tampered package payloads. |
| 37 | Dry-run previews | Implemented | Installer and local-mod previews. |
| 38 | Generated-content smoke tests | Implemented | Package, entrypoint, helper, and hash checks. |
| 39 | Structured diagnostics | Implemented | JSON EML records are parsed as single events, including multiline reports; runtime health and diagnostic output agree on structured error levels, latest-log and historical errors remain separated, and scans use bounded recent-log windows. |
| 40 | Searchable log viewer | Implemented | Settings search action supports text plus error/warning/info level filtering and bounded recent-log display, preventing long-running logs from blocking the dashboard. |
| 41 | Reproducible probes | Implemented | Deterministic KFC read probes and localization runtime probes with explicit log markers; Content Center exposes case-insensitive controlled-validation preflight, which refuses incomplete probes, build mismatches, missing/incompatible declared dependencies, or an active game session. |
| 42 | Research cataloging | Implemented | Idempotent build/log-hash catalog plus latest-run structured content-fixture cataloging for localization and bed runs, including scoped visual-evidence links and recovery from older failed runs. |
| 43 | Developer SDK | Implemented | SDK contract, docs, example, capability manifest. |
| 44 | Stable helper packaging | Verified | Helper packaged beside generated modules. |
| 45 | Profile/world cloning | Implemented | Independent cloned profiles with world IDs; launch re-verifies the prepared profile hash and blocks uncertain/already-running process state. |
| 46 | Live-config synchronization | Implemented | Dynamic-only atomic live config service. |
| 47 | Update/migration assistant | Implemented | Review and optional disable plan. |
| 48 | Health/support bundles | Implemented | Machine-readable health and bounded ZIP bundle; health reports include installed-mod inventory, integrity verification, and available restore-point counts, rejecting unsafe paths/symlinks, while bundles include bounded research catalogs/validation provenance without secrets. |
| 49 | Bed/future fixtures | End-to-end verified | Bed IDs, resource families, staging schema, safety contract, donor-profile validation, live registration, and UI-slot rendering are verified for the current bed fixture; a unique recipe GUID was required to prevent catalog deduplication. Custom localization, independent assets, and broader content classes remain follow-up work. |
| 50 | Release/upgrade channels | Implemented | Stable/beta/nightly builds use temporary archives, atomic metadata commits, strict metadata validation, archive safety checks, and refuse silent artifact overwrites. Verified releases can be cataloged, channel-gated, installed from Content Studio through the transactional local-mod installer, and blocked from silent downgrades; game-build checks and research-only approval remain enforced. |

## Verified runtime boundary

The strongest game-level evidence is the controlled EML/KFC bed fixture:
runtime resource registration, registry growth, knowledge linkage, typed
`HashKey32`, and cloned `FbUiBundle` set behavior were observed in logs and
the additional bed slot was visually confirmed. Static KFC repacking is not
treated as update-resistant runtime behavior.

Custom localization injection, broader model import, and additional content
classes remain gated until their exact donor schemas and loader capabilities
are independently verified on the target game build. The content-class service
now records those required resource families and fails closed for the verified
bed class while warning for research-only classes.
