# Enshrouded Control Center progress snapshot

Date: 2026-09-30 (updated through milestone R31)
Target build: `1076226`  
Release baseline: `1.0.2`  
Verification baseline: 705 tests, milestone R31 passing; capability audit covers all six phases (17 capabilities)

## Current-source update

### Verification refresh — 2026-09-30

The current authoritative snapshot is `CAPABILITY_SNAPSHOT_20260928.json`:

- The full suite passes **723 tests**.
- The milestone gate passes all current checks, including release, installer,
  portable-launch, rollback, save-backup, update-recovery, and research-safety
  gates.
- Release `1.0.2` is rebuilt from the current source; the release manifest and
  installer smoke report match the refreshed portable and installer hashes.
- Research Lab evidence now has first-class `catalog`, `item_info`, `recipe`,
  and `placed_item` categories, with capture and manual-import paths for each.
- The project remains incomplete: 4 capabilities are verified, 5 experimental,
  7 research-only, and 1 unsupported. The eight unresolved capability areas
  remain the authoritative next-work list.
- The guided visual-substitution session completed on the pinned build. The
  cloned Palm Wood Bed appeared in the Carpenter catalog, item information,
  recipe, placed world, and fresh relaunch session. The structured evidence is
  `research/probe_sessions/visual_manual_test_20260930.json` and verifies the
  render-model substitution route. The catalog icon is still blank, so the
  broader icon/material/texture capability remains research-only.

The sections below retain historical dated observations; when a test count or
milestone identifier differs, the current snapshot and latest milestone gate
take precedence.

- The beginner Content Studio and Research Lab workflows now use guided
  wizards with explicit donor, color, validation, safe-test, and launch steps.
- The Research Lab now keeps its advanced research catalog collapsed by default,
  so first-time users see the guided actions before technical probe records.
- BlenderTools imports now have explicit validation guidance for the 65,535
  vertex limit, per-LOD limits, supported collider shapes, texture-slot
  constraints, and the still-unproven custom-icon route.
- The full repository verification suite passes 705 tests, including the
  Blender export validator, LOD/collider checks, screenshot evidence checks,
  release gates, and installer smoke tests.
- Current-source portable and installer artifacts were rebuilt and verified;
  release hashes, clean install, upgrade preservation, and uninstall evidence
  are recorded in the 2026-09-29 release reports.
- The project is still not 100% complete. The capability snapshot remains the
  authoritative status source, with four verified, five experimental, seven
  research-only, and one unsupported capability.

This is a progress assessment, not a completion claim. Percentages are
planning estimates based on verified capabilities and remaining exit gates.

| Area | Estimate | Evidence-backed position | Main remaining gate |
|---|---:|---|---|
| Control Center foundation | 75–85% | Profiles, ownership, quarantine, rollback, diagnostics, installer checks, research cycles, and release gates are implemented. | Continued update/recovery validation across future game builds. |
| Phase 1 clone-and-patch | 65–75% | Furniture identity, recipe, knowledge, registry, fixed-array UI-slot cloning, and fresh localization registration are verified for the bed fixture. | Visible localization readback and field-level runtime promotion. |
| Phase 2 visual/original assets | 25–35% | Visual dependency plans, asset ownership, policy classification, and research-only probes exist. | Fresh in-game proof of model/material/texture substitution and original asset consumption. |
| Phase 3 module platform | 50–60% | Manifests, dependencies, load order, profiles, build checks, recovery, quarantine, evidence, and authoring scaffolding exist. | Third-party authoring workflow and update migration validated end-to-end. |
| Phase 4 gameplay systems | 15–25% | Offline builder workflow and conservative feasibility matrices exist. | Runtime interaction, AI, quest, animation, world-generation, and multiplayer-authority evidence. |
| Overall long-term objective | 40–50% | Platform groundwork and one end-to-end content fixture are strong. | The remaining runtime research areas are broad and not yet promoted. |

## Current verified baseline

- A deterministic generator now creates the first catalog-preview research
  candidate: it assigns a typed `UiTextureResource` to a cloned item's
  `iconImage` while recording preservation of model/scene preview fields.
  The candidate is explicitly research-only, isolated from the stable profile,
  and requires screenshot verdict and cleanup evidence.
- A fresh build-pinned research cycle is prepared and validated for that
  candidate (`catalog_preview_image_only_cycle_20260928_r2`). The live
  preflight is compatible and reports the stable profile isolated with no
  research modules installed; runtime launch and screenshot verdict remain
  intentionally pending.
- Runtime cycle r6 now proves the corrected generated probe executes through
  EML 1.3 without panic, registers a unique item/recipe/UI link, and launches
  Enshrouded to the play-selection screen. World entry remained on a loading
  screen, so catalog-tile, placement, and persistence verdicts remain open;
  the probe was removed and the stable profile restored.
- Save protection has now been exercised against the current discovered save
  directory: a 135-file timestamped backup was created and hash-verified under
  `profiles/save-backups/20260928T233601Z-autonomous-verification`. Its
  135-file manifest was revalidated and restored into a temporary destination
  with matching hashes. No live save file was edited.
- The save backup/restore exercise is now a structured, versioned milestone
  gate at `research/probe_sessions/save_backup_evidence_20260928.json`; the
  verifier requires a stopped game, matching file counts, manifest integrity,
  temporary restore isolation, and cleanup proof.
- The capability audit now explicitly covers all six plan phases. Loader/API
  hardening and packaging/evidence auditing are recorded as experimental
  capabilities with their current evidence and next gates, rather than being
  omitted from the completion accounting.
- A fresh isolated localization session (`localization_cycle_20260928_r2`)
  launched the current build, completed tag/localization registration without
  panic, reached the saved world, and was fully cleaned up. The custom label
  was not captured in the Carpenter UI, so localization remains experimental
  with its four UI-readback gaps honestly recorded.
- Added `tools/build_visual_variant.py`, a reusable authoring command that
  converts the visual-variant template into a validated research-only plan,
  preserves mechanics, records resource-graph dependencies, and rejects donor
  overwrite. It now also rejects malformed transforms and unsafe preview
  policies. Its focused tests are included in the current baseline.
- Added a known-reference bed/material example and generated research variant
  under `research/variants/bed_material_research_variant.json`. The direct CLI
  path was tested (including standalone package import), and the output records
  both model/material dependencies while remaining research-only.
- The first material-probe staging attempt exposed and fixed a generator bug
  that duplicated an existing model-assignment block. The corrected generator
  now detects pre-instrumented templates, emits one model assignment, and keeps
  material assignment instrumentation intact. A fresh material-only cycle is
  prepared and preflight-valid for the current build; runtime evidence is still
  pending.

- Water-resource coverage now includes bounded runtime reads for
  `WaterDisplacingResource` and `WaterChunkResource` metadata. The latter's
  content hash remains opaque; neither result proves simulation, mutation,
  registration, persistence, or multiplayer behavior.

- `keen::FogVoxelMappingResource` now has fresh runtime evidence: the shared
  world GUID resolves, its bounded 17-entry mapping payload reads successfully,
  and the probe records no voxel/chunk access or mutation. It remains
  research-only pending world-generation authoring and in-game terrain evidence.

- The stable furniture fixture creates a distinct recipe/UI slot without
  overwriting the donor.
- Metadata enumeration is verified for five resource families.
- `keen::TemplateResource` is quarantined after a blocking lookup boundary.
- Research-cycle preparation is portable, self-validating, and included in
  the milestone gate.
- Staged probes have a dry-run-first transactional installer with persistent
  reports, explicit research approval, backup/restore support, and exact EML
  build matching before application. Operation reports now retain the
  expected/observed build comparison.
- Visual-substitution plans preserve mechanics and expose policy-review state.
- The stable profile remains isolated from research-only modules.
- EML API version reporting is verified on a fresh launch; Control Center
  compatibility and health-report paths now consume the observed version.
  See the release manifest for the matching packaged build and verification.
- Quest research now has an automated evidence gate covering standalone typed
  quest creation, donor-preserving registry insertion, isolated runtime
  attachment, and cleanup. It remains research-only pending visible journal,
  persistence, completion/reward, and multiplayer evidence.
- AI research now has an automated evidence gate covering the 41-event donor
  graph, unique sequence cloning, donor parity, isolated attack-reference
  attachment, and cleanup. Behavioral observation and enemy-archetype/spawn
  registration remain open research gates.
- EML API 1.2 supports bounded metadata discovery without allocating for
  the complete game database. Fresh runtime evidence identifies concrete
  animation and world-resource donor GUIDs, replacing a previously stalling
  batch-enumeration route with a fast, read-only next-step workflow.
- The first exact animation-graph donor payload now reads successfully: 108
  nodes, 36 slot/bone mappings, 26 input IDs, and its hierarchy/root IDs are
  build-pinned. All 108 nodes are classified, and EML API 1.3 resolves the 32
  dependency GUIDs to 42 identities across six resource types without payload
  decoding. A unique donor-preserving graph clone now has exact node/type/
  dependency parity. The clone is also attached in isolation to the Hunter NPC
  collection entry without crossing template/entity/world/save boundaries.
  One clone-only edit reroutes `idle` to the existing same-graph
  `idle_Var_02` pose and attaches successfully. Visible changed behavior is
  still unconfirmed and remains research-only. A reusable fail-closed authoring
  definition and generator now produce this class of bounded probe without
  hand-written Lua.
- The first exact `keen::VoxelWorldResource` donor payload now reads safely
  through EML API 1.3. Runtime and offline values match for its dimensions,
  origin, 256-entry material table, seven voxel levels, and bounded first-level
  tile metadata. No resource creation, registration, mutation, attachment,
  world access, or save access occurred; world generation remains research-only.
- The complete offline voxel archive map now covers 135 records, 19,861 unique
  content hashes, 198 table GUIDs, and scene-ownership overlap. A live bounded
  12-entry metadata sample resolved seven entries as other voxel-world
  resources and five as unregistered identities; none were material resources.
  The subsequent complete 198-entry pass resolved exactly 125 entries as the
  125 standalone voxel-world resources, leaving 73 unregistered identifiers.
  This supports, but does not yet prove, a palette/index relationship.
- A live paired read now verifies one shared-GUID scene group: SceneResource
  part 0, solid VoxelWorld part 0, and fog VoxelWorld part 1. All bounded fields
  match the offline exports; attachment and loading semantics remain unproven.
- Same-GUID metadata mapping now covers ten scene/resource families. The tested
  GUID exposes voxel-world parts 0/1, entity parts 0/1, render-model parts 0/1,
  and single-part scene, fog, water, water-chunk, and fog-mapping resources;
  voxel chunk and render-model-grid resources are absent for this scene.
- A bounded `WaterWorldResource` payload read also matches offline data: its
  tile grid is 1×1, origin is 0/0/0, and its behavior table has 256 entries.
  The associated water-chunk binary content remains intentionally unread.
- A corrected material-substitution runtime attempt reached the loader but
  stalled during full `ItemInfo` enumeration before either visual or material
  assignment. It was stopped and rolled back cleanly; the structured result is
  retained as a research-only boundary, not as a material-rendering verdict.
- The follow-up probe now fails closed before enumeration: the current EML 1.3
  surface lacks `get_resource_by_guid`, so the known donor GUID cannot be
  resolved to a mutable resource object. This removes the hang risk and records
  the actual API boundary in `visual_material_substitution_cycle_20260928_r3`.
- A subsequent bounded probe using the documented `game.assets.get_resource`
  path successfully resolved the known render-model resource and reached a
  model assignment (`before=4c7f1c3a-b448-4460-ad5e-a79b3859d2c1`,
  `after=159b5f47-aa61-4db9-8e64-06db850de6f6`) without a panic in the bounded
  session window. This is runtime assignment evidence only: the probe did not
  register a fresh clone in that window, and no catalog/placed-object screenshot
  or fresh-launch persistence evidence exists yet. The structured evidence is
  `visual_material_substitution_cycle_20260928_r4/runtime_evidence.json` and
  remains experimental.
- A fresh isolated full-probe session then combined that assignment with clone
  registration: item `3987654501`, recipe `3987654502`, one knowledge link,
  one UI-slot insertion, and a placed-entity reference were all emitted by the
  same build-pinned run without a panic. The replacement model assignment also
  succeeded. The automatic capture reached the play-selection screen rather
  than the world, so placed-model appearance and restart persistence remain
  unverified. Evidence is
  `visual_substitution_live_20260929_runtime_evidence.json`; the probe was
  removed and the stable profile restored.
- The same probe was subsequently launched through the selected private save
  and automatically entered the live game world. A durable world screenshot is
  recorded at `visual_substitution_live_20260929_world_final.png`; it proves
  the world-load path, but does not show the cloned bed, so placed-object visual
  verification remains open. Post-cleanup live-loader inspection reports only
  the stable `enshrouded_mod_hub`, with no research-only or unclassified modules.
- The installed architect-toolkit audit clarifies an important UI boundary: the
  supported `FbUiBundle` trees observed through EML are crafting-recipe trees,
  while no Construction Hammer category/group collection or ordering resource
  was evidenced. The cloned recipe/UI-slot path therefore cannot be assumed to
  populate the Carpenter/Construction Hammer catalog. This boundary is recorded
  in `export/architect_toolkit/hammer_category_audit.json`; the Hammer menu
  remains an engine/UI research item rather than a failed clone registration.
- The bounded blueprint payload probe then crossed the prior userdata boundary:
  mapped `__index`/`__len` access read 120 `blueprintItems` entries, including
  item IDs, dimensions, compressed-data flags, and bounded first/last records.
  No mutation occurred. This upgrades the Carpenter route from metadata-only to
  payload-readable research, while registration, menu visibility, placement,
  persistence, and rollback remain open. Evidence is
  `research/probe_sessions/voxel_blueprint_registry_payload_cycle_20260929_evidence.json`.

## Fastest path forward

1. Run one isolated visual-substitution session and capture rendered evidence.
2. Run one isolated localization-label session and capture UI readback (runtime registration is now verified; visible consumption remains open).
3. Generalize the verified furniture compiler to two additional donors.
4. Reassess promotion only after restart, rollback, and clean-profile checks.

The authoritative execution order is maintained in
`ACCELERATED_NEXT_ACTIONS_20260928.md`.

## Post-release update — 2026-09-29

- Release `v1.0.2` is tagged and synchronized to GitHub at
  `FeatherMourn/EnshroudedModHub`.
- The Content Studio now validates and stages BlenderTools-generated EML
  packages into `custom_content/imports/` without installing them into the
  live game.
- The Research Lab now captures game-window screenshots into the evidence
  workflow and labels them as raw evidence rather than automatic promotion.
- A fresh registered-visual-substitution session completed model assignment,
  clone/recipe registration, UI-link insertion, and cleanup without panic.
  It remains experimental because the captured screen did not show the cloned
  placed object and save persistence was not tested.
- The stable live profile was rechecked after cleanup: Enshrouded is closed,
  only the stable Control Center module is present, and isolation is ready.
- The latest milestone gate is `research/MILESTONE_GATE_20260929_R8.json`;
  all 655 automated tests and all current gates pass.

## Donor expansion update — 2026-09-29

- The extracted build now has a second concrete furniture donor candidate:
  `Prop_Decoration_Comfort1_T0_Chair_Stool`.
- Its item, recipe, knowledge, placed-template, render-model, and icon references
  are recorded in `research/content_clone_candidates/chair_stool_clone_candidate.json`.
- The candidate remains `DESIGN_ONLY_NOT_INJECTED` until complete
  `TemplateResource` dependency closure and runtime-safe registration are proven.
- The asset-import boundary verifier and 70 focused content/navigation tests pass.
- The chair/stool clone probe then completed a fresh isolated runtime session:
  unique item and recipe registration, clone discovery, knowledge linkage,
  UI-set insertion, and unique identity all succeeded without a loader panic.
  Evidence is `research/probe_sessions/chair_stool_clone_runtime_evidence_20260929.json`.
  This is experimental registration evidence only; catalog visibility, placement,
  and fresh-launch persistence still require in-game proof.
- A third donor, `furniture_tier_two_bed_20260928`, also completed a fresh
  isolated registration session with unique item/recipe identity, knowledge
  linkage, UI insertion, and preserved placement entity. Evidence is
  `research/probe_sessions/tier_two_bed_clone_runtime_evidence_20260929.json`.
  The three-donor runtime-registration acceptance criterion is now met;
  visual catalog, placement, and persistence acceptance remains open.

## Verification update — 2026-09-29

- Full automated verification remains green: 655 tests passed.
- Milestone gate R9 passed all current gates, including packaging, rollback,
  save-backup verification, installer smoke tests, evidence validation, and
  capability-audit checks.
- The completion audit still correctly reports `project_complete: false` with
  eight unresolved or research-only capability areas; no completion claim is
  being made from the green test suite alone.

## Carpenter probe safety update — 2026-09-29

- The building-catalog discovery probe was repaired after a fatal runtime
  boundary. The unsafe `Type` userdata enumeration path was removed; the probe
  now queries only a fixed list of known qualified resource names.
- A fresh session completed without panic or loader error and observed seven
  `VoxelBlueprintConfig` resources plus the blueprint item-registry,
  material-pool, `FbUiBundle`, item-registry, and recipe-registry families.
- The probe was removed afterward and the stable profile was restored. This is
  safe read-only research evidence only; it does not establish Construction
  Hammer catalog visibility, placement, persistence, or writable registration.
  Evidence: `research/probe_sessions/building_catalog_resource_discovery_runtime_evidence_20260929_r2.json`.

## R12 verification and authoring UX update — 2026-09-29

- Milestone gate R12 passed all current gates with 658 automated tests,
  including packaging, rollback, save-backup, compatibility, recovery, and
  stable-profile isolation checks. Evidence: `research/MILESTONE_GATE_20260929_R12.json`.
- The Research Lab now shows capability totals and a beginner-readable
  remaining roadmap. Each unresolved capability includes its current state so
  users can distinguish experimental work, research-only work, and engine
  boundaries.
- The current audit remains intentionally incomplete: 4 capabilities are
  verified, 5 experimental, 7 research-only, and 1 unsupported. The project
  is not being marked complete until the full goal plan is satisfied.

## Interaction donor boundary update — 2026-09-29

- Offline extraction found a real interaction-bearing record with nested
  `ClientInteractionOffer`, `CraftingInteraction`, and `InteractionOffer`
  data, plus a concrete interaction key. The record is owned by
  `TemplateResource`, however, which remains quarantined for the current EML
  build. It is therefore not safe to install as a runtime probe.
- The candidate and exact quarantine reason are recorded in
  `research/INTERACTION_DONOR_CANDIDATE_BOUNDARY_20260929.json`. This advances
  the interaction research from “no donor found” to “donor exists but its
  owner resource is not safely addressable.”

- A fresh metadata-only `TemplateResource` probe confirmed the boundary: the
  mod runner started, but the metadata call stalled before returning. The
  probe was stopped and removed, and the stable profile passed isolation
  checks. Evidence: `research/probe_sessions/template_resource_metadata_interaction_boundary_20260929_evidence.json`.

- The probe installer now hard-quarantines `keen::TemplateResource`, including
  metadata-only probes, unless an explicit unsafe-boundary override is used.
  The complete automated suite passes with 660 tests after this policy change.

## Catalog-preview boundary update — 2026-09-29

- The isolated registration-only catalog probe safely created an independent
  `ItemInfo`, inserted it into `ItemRegistryResource`, kept the parallel debug
  name array aligned, assigned zero-GUID visual fields, and rediscovered the
  item without a panic. Evidence:
  `research/probe_sessions/catalog_preview_registration_only_20260929_r2_runtime_evidence.json`.
- This narrows the remaining catalog work to a menu-scoped native catalog
  refresh/render path. The combined recipe/UI probe remains research-only and
  is not being reused because it reached the known EML panic boundary.

## R13 live isolation confirmation — 2026-09-29

- The post-R13 live-loader check reports `status: ready` and `isolation_ready:
  true` for build `1076226`.
- Only the stable `enshrouded_mod_hub` module is installed; research-only and
  unclassified module counts are zero, and the loader reports no warnings.
- Enshrouded is closed after the verification pass, leaving the installation
  ready for the next isolated experiment.

## Tuning probe safety boundary — 2026-09-29

- The generated build-pinned KFC read probe was refused before installation
  because its broad batch also referenced the known-stalling
  `keen::WaterWorldResource` family. No tuning values were written and no
  research module was installed.
- The game was stopped immediately after the refused launch attempt; the
  stable live-loader check returned ready with only `enshrouded_mod_hub`
  installed. The next tuning step is to split the read inventory into safe
  resource-family batches before runtime testing.

## Safe BalancingTable read batch — 2026-09-29

- A build-pinned, read-only batch safely queried one `keen::BalancingTable`
  resource and read `baseCritChance`, `damageMod2Handed`, and `comfortSetup`.
- The session produced no panic and no mutation. The probe was removed after
  the run, and the stable live-loader check returned ready with no warnings.
- This is experimental read evidence only; it does not yet prove that writing
  tuning values is stable or that gameplay behavior changed. Evidence:
  `research/probe_sessions/balancing_table_read_batch_safe_20260929_evidence.json`.

## Reversible BalancingTable write — 2026-09-29

- A one-field isolated probe changed `keen::BalancingTable.baseCritChance`
  from `0.3` to `0.425`, read the changed value back, and restored `0.3`.
- The run completed without a panic. The game was stopped, the probe removed,
  and the stable profile returned to `status: ready` with no warnings.
- Tuning remains experimental: this proves a controlled reversible runtime
  mutation, but not persistent gameplay behavior or compatibility of every
  tuning family. Evidence:
  `research/probe_sessions/balancing_table_scalar_write_safe_20260929_evidence.json`.

## Catalog preview retry boundary — 2026-09-29

- A fresh isolated retry of the image-only catalog-preview cycle completed
  clone discovery, icon assignment, recipe registration, and UI-link logging
  without a panic.
- The session again did not reach a verified world/catalog state, so catalog
  visibility, placement, and persistence remain unproven. The probe was
  removed and the stable profile returned to ready with no warnings.
- Evidence:
  `research/probe_sessions/catalog_preview_retry_20260929_evidence.json`.
