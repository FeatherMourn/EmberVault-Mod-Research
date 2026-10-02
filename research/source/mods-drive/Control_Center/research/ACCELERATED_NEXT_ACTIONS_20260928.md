# Accelerated next-action queue

This queue is derived from the current capability snapshot and is ordered to
maximize reusable progress per controlled game session.

## 1. Resolve catalog preview for visual substitution

State: experimental/research-only by field. Controlled runtime registration,
a visibly different placed model, and a nonblank catalog tile are now evidenced
in `probe_sessions/registered_visual_substitution_20260928_r3.json` and
`probe_sessions/catalog_icon_fallback_runtime_evidence_20260928_r2.json`;
the remaining
result is the combined visual/persistence proof for one finished variant. The reusable helper now exposes
`catalog_preview_state` and `assign_catalog_icon` so the next probe can record
and, if needed, provide a valid `UiTextureResource` reference without changing
the placed-model hypothesis. Use one isolated session, one donor, and one
obvious model difference. Do not combine localization or tuning changes with
this test.

Use `VISUAL_SUBSTITUTION_SESSION_CHECKLIST_20260928.md` for the controlled
session, evidence capture, and rollback sequence.

Success evidence: fresh EML log, screenshot of the placed item, and a
machine-readable report linking the exact build and probe hash.

## 2. Promote the generic content compiler across furniture donors

State: experimental/research-only by field. Reuse the verified ItemInfo,
registry, knowledge, recipe, and UI-bundle families. Add donor-schema
validation before generating a project, and keep visual references and
localization payloads explicitly separated from identity/recipe edits.

Success evidence: two additional furniture donors with independent recipe
slots, no vanilla overwrite, restart persistence, and clean-profile validation.

## 3. Finish custom localization UI consumption

State: research-only at the UI boundary. Run a narrowly scoped catalog-label
probe using the existing registration route and compare the rendered label
against the generated localization tag.

Success evidence: fresh-session log plus an in-game screenshot showing the
custom label, not merely successful payload registration.

## 4. Add original-asset import experiments

State: research-only. First validate icon/texture conversion independently,
then model substitution, then a combined content graph. Keep each asset type
in its own probe so an engine rejection identifies the boundary precisely.
The highest-leverage prepared route is the external Blender RenderModel path:

- Validate the generated package with `tools/verify_blender_export.py`.
- Use `research/probe_sessions/blender_render_model_round_trip_plan_20260928.json`.
- Stage only in an isolated research profile and keep the game closed during
  installation/removal.
- Capture visible placement, fresh-launch behavior, donor integrity, and
  rollback before any promotion.
- Reference package validation is recorded in
  `research/probe_sessions/blender_export_package_validation_20260928.json`.

This route demonstrates package construction and EML generation externally,
but Control Center still requires its own target-build runtime evidence.

## 4a. Keep direct color/material writes quarantined

The disposable-copy probes for `ItemInfo.color` and `ItemInfo.material` both
ended with `panic in a function that cannot unwind` before archive registration
completed. The failures are recorded in
`probe_sessions/external_route_color_variant_20260929.json` and
`probe_sessions/external_route_material_reference_20260929.json`; neither
touched the live installation. Do not retry these direct assignments in the
live profile. The next safe route is a typed material/texture resource graph,
validated independently before any color-combination assignment.

## 5. Expand platform promotion only after runtime evidence

State: platform foundations are verified/experimental. Do not promote fields
or asset routes based only on offline schema inspection. A promotion requires
runtime acceptance, restart persistence, clean-profile validation, rollback,
and a documented recovery path.

## Current hard boundaries

- `keen::TemplateResource` remains quarantined because single-resource
  metadata access can block before returning.
- Original mesh import is not runtime-verified.
- Custom localization is not UI-promoted.
- Multiplayer authority remains unsupported and requires engine/network
  evidence before implementation claims are made.

## Fast execution rule

Prepare each session with `tools/prepare_research_cycle.py`, validate its
`RESEARCH_CYCLE.json`, run only one hypothesis, then restore the stable
profile before starting the next action.

## Batch acceleration now available

The tuning audit now produces a reusable ranked queue at
`research/TUNING_RESEARCH_QUEUE_20260928.json`. It can be regenerated for a
new inventory or game build with:

```text
python tools/report_tuning_coverage.py <inventory.json> modules --output <queue.json>
```

The queue currently records 131 reflected families, 22 covered families, and
109 uncovered families. Priority 1 starts with building/blueprint/material,
crafting, and item families so the next research sessions stay aligned with
the builder and custom-content goals.

The catalog-preview matrix can now be validated and converted into a
deterministic disposable run plan:

- `tools/validate_catalog_preview_matrix.py`
- `tools/plan_catalog_preview_batch.py`
- `templates/catalog_preview_probe_matrix.json`
- `probe_sessions/catalog_preview_batch_plan_20260928.json`

The generated plan assigns unique item/recipe IDs, records the exact matrix
hash and target build, and requires a fresh EML session, screenshot verdict,
panic stop, cleanup, and profile restoration for every candidate. This
removes manual bookkeeping and allows the four current UI hypotheses to be
prepared together while retaining isolated evidence. It is a planning and
preflight tool; it does not install or launch a probe automatically.

The batch plan now carries each candidate's field strategy directly: fields to
set, clear, preserve, and any UI schema paths. Before installation,
`tools/verify_catalog_preview_batch.py` checks the build pin, matrix hash,
global ID uniqueness, evidence requirements, and isolation policy. The check
is part of the milestone gate.

Milestone snapshots now receive the freshly measured test count from the same
gate run, preventing release evidence from lagging behind after new tests are
added.
