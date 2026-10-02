# Control Center Capability and Limitations Report

Date: 2026-09-28  
Target game build: `1076226`  
Release baseline: Control Center `1.0.2`

This is the current milestone report, not a claim that the long-term platform
objective is complete. The machine-readable source is
`CAPABILITY_AUDIT_20260927.json`.

## Verified

- Donor-preserving furniture cloning can register a new `ItemInfo` and recipe.
- A cloned furniture recipe can receive a separate crafting UI slot through
  typed recipe-set cloning; direct mutation of fixed-size arrays is unsafe.
- Offline builder catalogs support search, favorites, material totals,
  inventory shortage calculation, and portable build plans without changing
  game state.
- `tools/report_build_plan.py` exposes those calculations as a reusable,
  machine-readable offline workflow.
- Control Center module quarantine, restoration, ownership records, release
  hashing, and capability-evidence validation are implemented and tested.
- Module dependencies, conflicts, and load-order decisions can be exported as
  a read-only machine-readable graph report.
- The existing 1.0.2 installer passes isolated install, upgrade-preservation,
  and uninstall smoke verification; user profile data is preserved.
- Historical test figures belong to earlier milestone snapshots; the current
  source suite passes 720 tests and the current milestone verification passes
  all configured gates.
- EML Lua API version `1.2` is now emitted in fresh runtime logs and consumed
  by Control Center compatibility checks; this API-reporting change has
  source and runtime evidence. Package identity is recorded in the release manifest.
- Single-resource metadata lookup is verified for the proven `keen::ItemInfo`
  donor route; the EML metadata API is exposed at runtime.
- Compiled content and visual-substitution manifests now carry build-aware
  metadata policy state; non-verified visual dependencies set
  `policy_review_required` and are not treated as runtime-approved.

## Experimental

- Identity, localization payloads, recipe metadata, and category/layout plans
  can be authored and generated, but current-build runtime/UI consumption must
  be demonstrated independently for each resource family.
- Runtime registration of a localization tag and collection was freshly
  verified on 2026-09-28 without panic; a fresh-session UI label readback is
  still not available.
- The combined localized-bed probe reproducibly registers its tag and
  collection, then stops before item/recipe completion markers; this is a
  separate unresolved runtime boundary, not evidence of UI consumption.
- `tools/verify_localization_evidence.py` now rejects malformed or falsely
  promoted localization evidence records.
- Portable release builds can be rebuilt and verified, and the existing
  installer artifact is smoke-tested; installer/source rebuild parity remains
  incomplete when Inno Setup is unavailable.

## Research-only

- Custom icon rendering, colors, materials, textures, model references, and
  placed-entity substitutions.
- Read-only donor/candidate visual dependency inventories and substitution
  plans are available, but they do not perform runtime replacement. Plans
  identify verified, unverified, quarantined, or unknown resource policy state.
- A same-build registered clone accepted a replacement `RenderModel` reference
  and reached clone discovery, new item, recipe, and UI-set registration
  without a panic. The
  placed-object entity was registered, but human-visible replacement appearance
  and save persistence remain unverified; catalog presentation is unresolved.
  Fresh evidence: `research/probe_sessions/visual_substitution_runtime_evidence_20260930_r2.json`.
- The chair/stool donor probe independently reached runtime clone registration,
  discovery, knowledge linking, and UI-set insertion without a panic. This is
  still research-only because catalog visibility, placement/interaction, and
  save persistence have not been captured.
- The bench donor probe independently reached the same runtime registration
  boundary without a panic. It is also research-only; catalog visibility,
  placement/interaction, save persistence, and complete dependency closure
  still require evidence.
- Original mesh/resource import and arbitrary resource-graph construction.
- `keen::TemplateResource` metadata lookup is explicitly quarantined because
  controlled calls block before returning; it remains research-only.
- A real interaction-bearing `TemplateResource` candidate was found offline,
  but its nested `ClientInteractionOffer`, `CraftingInteraction`, and
  `InteractionOffer` records cannot be safely addressed through the current
  EML route. Evidence: `research/INTERACTION_DONOR_CANDIDATE_BOUNDARY_20260929.json`.
- New interaction, AI/enemy, quest, animation, and world-generation graphs.
- `tools/report_gameplay_feasibility.py` exports the conservative Phase 4
  research matrix without runtime mutation.
- Interaction probe contracts explicitly record persistence and authority as
  unknown until runtime evidence exists.
- Fresh localization runtime registration is now conclusive; UI consumption
  remains unverified because the probe does not itself prove visible labels.

## Unsupported by the verified route

- Multiplayer authority, replication, or server-owned behavior changes.
- Claims that resource registration alone changes saved-player state, world
  state, or authoritative multiplayer state.
- Direct indexed mutation of opaque Rust-backed registry arrays.
- Promoting an asset or gameplay experiment based only on generated files,
  static archive edits, or a successful Lua assignment.

## Promotion requirements

A capability may move toward verified only when the evidence includes the
relevant runtime registration, same-build in-game behavior, donor-preservation
check, rollback/recovery result, and a fresh-session log boundary. Visual
features additionally require visual evidence. Authority-sensitive features
require explicit multiplayer/server evidence and cannot inherit single-player
resource-patch results.

## Immediate next gates

1. Capture catalog screenshots and placement/interactions for the three-donor
   furniture matrix, then verify repeat-launch de-duplication and safe save
   persistence.
2. Re-run the localization probe and capture a visible game-facing label result.
3. Continue donor-specific visual graph tracing with a controlled model or
   material substitution probe.
4. Rebuild installer parity once the required installer tool is available.
