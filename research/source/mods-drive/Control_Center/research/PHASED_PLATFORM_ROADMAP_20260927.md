# Enshrouded Control Center platform roadmap

## Stage 1 — reusable furniture/content pipeline

1. Keep clone registration, donor preservation, recipe cloning, and fixed-size
   UI-set cloning behind generated research-only projects.
2. Add field-level donor schema validation before permitting identity,
   localization, layout, icon, stats, or mechanics edits.
   The compiler now exposes a side-effect-free definition validator and makes
   mechanics preservation explicit (`preserve` by default; `replace` remains
   research-only).
3. Make live evidence first-class: fresh-session boundaries, unique manifest
   IDs, marker classification, rollback, and clean-install checks.
4. Promote a capability only after the same resource family is visible in-game
   on the current game/EML build.

Exit gate: a generated furniture definition can produce a new visible recipe
slot without overwriting its donor, and the Control Center can inspect/adopt/
restore the project safely.

The current localization follow-up is split into two gates: first diagnose the
combined probe's reproducible stop after tag/collection registration, then
capture a game-facing label before promotion.

## Stage 2 — visual and asset substitution

1. Verify icon-resource cloning and custom PNG import independently.
2. Trace ItemInfo visual fields to model, scene, placed-entity, and material
   resource graphs.
3. Build donor-specific asset substitution plans that preserve mechanics while
   changing only visual references.
4. Add import validation, resource GUID ownership, dependency packaging, and
   rollback for custom assets.

Exit gate: one controlled furniture variant uses a different verified visual
resource while retaining donor placement/mechanics, or the engine limitation is
documented with a reproducible failed probe.

## Stage 3 — module platform

1. Formalize manifests, dependencies, load order, profiles, build
   compatibility, ownership, and version migration.
   Live preflight now optionally compares the observed EML build with an
   expected exact build and fails compatibility checks on mismatch.
2. Add quarantine and recovery for malformed modules or loader failures.
3. Add portable/installer parity, support bundles, update detection, and
   clean-install/upgrade/uninstall verification.
4. Expose authoring plans, evidence state, and rollback actions in the Control
   Center UI.

Exit gate: third-party research modules can be installed, inspected,
quarantined, restored, and verified without touching unrelated mods.

## Stage 4 — builder and gameplay research

Prioritize low-risk, data-driven capabilities first:

1. build/furnishing catalogs, JSON import, search, favorites, material
   calculators, portable build plans, and placement presets;
2. custom recipes, resources, and interaction prototypes;
3. AI/enemy and quest experiments using existing authoritative schemas;
4. animation, world-generation, and multiplayer-authority feasibility probes.

Every capability must be labeled verified, experimental, research-only, or
unsupported. New authority-sensitive behavior must not be presented as a
single-player data patch.

The current builder implementation is offline-only: it does not move the
player, place objects, bypass collisions, or alter multiplayer authority.

## Current position

The stable furniture fixture proves one visible cloned recipe/UI slot. The
generated clone route now proves ItemInfo and recipe registration on build
1076226, with compact evidence cataloging in
`generated_content_fixture_catalog_20260927.json`. Typed registry internals
remain opaque from Lua, so registry length is not treated as catalog proof.
Generated UI registration is verified for the furniture fixture, and clone-only
model substitution is now verified with catalog, placed-object, persistence,
and rollback evidence. Custom localization UI consumption and material,
texture, color, and original-mesh import remain research-only until their
independent runtime evidence is captured.
Manifests and live preflight can now pin either numeric build ranges or the
complete EML build identity, including branch and timestamp, for
update-sensitive mods. The accelerated execution order is maintained in
`ACCELERATED_NEXT_ACTIONS_20260928.md`; use it to select one hypothesis per
controlled session. The current source tree provides the release safety gate
with 537 passing tests across the current milestone gates. The generated live hub manifest now
declares `feature_state: stable`, so the live-loader preflight classifies it as
isolated and production-ready.
