# Control Center evidence index — 2026-09-27

This index routes future work to the strongest available evidence. A research
report or passing static test does not promote a capability to runtime-verified
status by itself.

## Phase 1 — clone and patch

- `PHASE1_CAPABILITY_MATRIX_20260927.md` — field-level capability states.
- `CAPABILITY_AUDIT_20260927.json` — machine-readable maturity policy.
- `FULL_ICON_MODEL_BED_PROBE_V2_EVIDENCE_20260927.md` — stable furniture
  registration and UI-link evidence.
- `runtime/kfc_content_registry.lua` — reusable registration helper.
- `core/content_patch.py` — donor-preserving, hash-checked patch planner.

## Phase 2 — visual and original-content research

- `VISUAL_SUBSTITUTION_PROBE_EVIDENCE_20260927.md` — resource-graph boundary.
- `CUSTOM_ICON_IMPORT_ROUTE_20260927.md` — icon import route and limits.
- `RENDER_MODEL_GUID_EVIDENCE_20260927.md` — donor render-model findings.
- `BED_VISUAL_FIELD_EVIDENCE_20260927.md` — build-specific visual-field scan.
- `VISUAL_DEPENDENCY_INVENTORY_20260927.json` — 40-reference staged render-model
  inventory; runtime substitution remains unverified.
- `VISUAL_SUBSTITUTION_COMPARISON_20260927.json` — donor/candidate comparison
  with 30 missing candidate references and a failed completeness gate.
- `VISUAL_SUBSTITUTION_COMPARISON_FINDINGS_20260927.md` — interpretation and
  next resource-graph research step.
- `VISUAL_GRAPH_CONSTRUCTION_PLAN_20260927.json` — measured blockers and
  fail-closed steps for constructing a compatible candidate graph.
- `VISUAL_SUBSTITUTION_DEPENDENCY_AVAILABILITY_20260927.json` — four referenced
  dependencies resolved and validated as `RenderMaterialResource` JSON files.
- `VISUAL_CANDIDATE_SEARCH_20260927.md` — six exact-shape RenderModel candidates
  found among 12,713 extracted resources.
- `VISUAL_CANDIDATE_STEAM_PROBE_EVIDENCE_20260927.md` — Steam-path runtime
  discovery of candidate `159b5f47` and all five direct dependencies.
- `ITEM_VISUAL_CANDIDATE_159B_EVIDENCE_20260927.md` — clone-only runtime
  RenderModel assignment succeeded without registry mutation.
- `TEMPLATE_VISUAL_CANDIDATE_159B_PLAN_20260927.md` — static placed-model graph
  candidate changes exactly one TemplateResource model edge.
- `TEMPLATE_TYPE_NAME_RUNTIME_BOUNDARY_20260927.md` — both TemplateResource
  lookup spellings stall at the runtime API boundary on this build.
- `core/asset_substitution.py` and `core/asset_service.py` — dependency-aware
  research plans without silent runtime mutation.
- `EML_METADATA_ENUMERATION_RELEASE_20260927.md` — reproducible EML build and
  metadata-only asset enumeration API evidence.
- `SETTINGS_METADATA_PROBE_EVIDENCE_20260927.md` — isolated runtime discovery
  of both settings families without payload decode or mutation.

## Phase 3 — platform and release safety

- `MODULE_MATURITY_MIGRATION_20260927.md` — built-in module migration.
- `MODULE_GRAPH_STRICT_AUDIT_20260927.json` — 28-module strict audit.
- `LIVE_LOADER_PREFLIGHT_20260927.json` — current live inventory.
- `LIVE_LOADER_ISOLATION_PREFLIGHT_20260927.json` — strict isolation result.
- `docs/CLEAN_INSTALL_VERIFICATION_20260927.md` — 1.0.1 historical evidence plus
  isolated 1.0.2 install, upgrade-preservation, and uninstall verification.
- `tools/verify_installer_smoke.py` and
  `research/INSTALLER_SMOKE_1.0.2_20260927.json` — repeatable isolated
  installer smoke verification with a valid install/upgrade/uninstall result.
- `tools/verify_milestone.py` — installer smoke is now a first-class release
  gate, so the versioned milestone snapshot cannot pass without install and
  recovery verification.
- `tools/verify_localization_evidence.py` — localization evidence schema and
  promotion claims are validated as part of the milestone gate.
- `research/LOCALIZATION_COMBINED_BED_LIVE_SMOKE_20260927.md` — fresh
  same-build combined localized-bed registration smoke; UI consumption remains
  unverified.
- `research/localization_combined_bed_results_1076226.json` — conservative
  machine-readable catalog of the combined probe markers; final item/recipe
  registration was not claimed because the session ended before that marker.
- `docs/INTEGRITY_OWNERSHIP_MIGRATION_20260927.md` — ownership and restore evidence.
- `TUNING_COVERAGE_1076226.json` and `TUNING_COVERAGE_FINDINGS_20260927.md` —
  complete reflection-family versus module coverage audit.
- `WORLD_DIFFICULTY_RUNTIME_BOUNDARY_20260927.md` — native panic evidence and
  fail-closed classification for the unsafe GameSettings/FbUiBundle path.

## Phase 4 — gameplay and builder research

- `GAMEPLAY_FEASIBILITY_20260927.json` — interaction, AI, quest, animation,
  world-generation, and multiplayer-authority feasibility states.
- `CAPABILITY_LIMITATIONS_REPORT_20260927.md` — conservative public boundary.
- `PHASED_PLATFORM_ROADMAP_20260927.md` — prioritized next research stages.

## Reusable authoring artifacts

- `research/templates/content_definition_customization_contract.json` —
  donor-based content definition starter with explicit mechanics preservation.
- `research/CONTENT_DEFINITION_CUSTOMIZATION_CONTRACT_20260927.md` — compiler
  maturity and donor-behavior contract.

## Current interpretation

The platform foundation and donor-preserving furniture route are operationally
verified. Clone-only RenderModel field assignment is experimentally verified,
but placed-object substitution, original assets, AI/quest/world-generation,
and multiplayer authority remain research-only or unsupported until fresh,
build-matched runtime evidence exists.

- `research/MILESTONE_QUALITY_GATE_20260927.json` — machine-readable snapshot
  of the complete 365-test release gate and supporting audits.
# Stable production smoke

- `research/STABLE_LOADER_SMOKE_EVIDENCE_20260927.md` — fresh clean-log
  launch verified the stable hub, 1,910 patches, and runtime attachment on
  build 1076226 without enabling research-only modules.
- `research/STABLE_LOADER_SMOKE_EVIDENCE_20260927_2150.md` — second controlled
  launch verified a fresh EML session, no-change cache handling, stable-module
  isolation, runtime attachment, and a running process with no observed
  panic/error/fatal entries.

- `research/PROBE_MANIFEST_SAFETY_20260927.md` — all research probe
  generators are explicitly classified and covered by regression testing.
- `research/PROBE_GENERATOR_AUDIT_20260927.json` — machine-readable result of
  the probe-generator classification audit.
- `research/VISUAL_CANDIDATE_GRAPH_PROBE_V2_20260927.md` — staged, read-only
  RenderModel candidate probe with exact build and isolation evidence.
- `research/VISUAL_CANDIDATE_GRAPH_LIVE_SMOKE_20260927.md` — build-matched live
  read-only probe loaded successfully, scanned 12,713 RenderModel resources,
  and was fully removed after the test; visual substitution remains unproven.
- `core/template_graph.py` plus `tests/test_template_graph.py` — donor graph
  source-hash enforcement prevents stale plans from producing candidates after
  the extracted donor changes; covered by the 361-test gate.
- `tools/verify_template_candidate.py` plus
  `tests/test_verify_template_candidate.py` — reusable pre-package verifier
  reports donor hash, planned model edge, and unintended graph differences;
  covered by the 364-test gate.
- `tools/build_visual_candidate_probe.py` plus
  `tests/test_build_visual_candidate_probe.py` — generated visual probes now
  pin the candidate SHA-256 in both manifests, preserving reproducibility when
  extracted resources change.
- `core/gameplay_feasibility.py` and
  `tools/report_gameplay_feasibility.py` — interaction probe contracts now
  describe donor readback and persistence observations while explicitly
  recording unknown authority and `runtime_mutation: false`; covered by the
  364-test gate.
- `research/INTERACTION_PROBE_CONTRACT_20260927.md` — reusable Phase 4
  interaction research contract and promotion boundary.
- `research/EML_BUILD_VERIFICATION_20260928.json` — current-source cargo
  verification for `mod-loader-lua` and `dinput8-proxy` on the target build.
- `research/PORTABLE_LAUNCH_SMOKE_PROCESS_TREE_20260928.json` — packaged
  portable launch evidence proving both bootloader processes were responsive
  and the complete process tree terminated with no remaining PIDs.
- `research/probe_sessions/blender_render_model_round_trip_runtime_evidence_20260928.json` — controlled runtime registration evidence for custom textures, material, model, item, recipe, and UI entry, with rollback proof and explicit visual-evidence gaps.
- `tools/verify_blender_runtime_log.py` — machine verifier for the matching EML log milestones; the evidence gate requires it to pass before runtime registration evidence is accepted.
- `research/POST_ROLLBACK_STABLE_LAUNCH_EVIDENCE_20260928.json` — fresh build-matched launch after research-probe rollback, with only the stable module present and no observed panic or probe error.
- `research/EML_API_VERSION_RUNTIME_VERIFICATION_20260928.md` and
  `research/EML_API_VERSION_RUNTIME_EVIDENCE_20260928.json` — fresh EML
  sessions report Lua API `1.2`; Control Center detects it after the newest
  registry boundary, tied to game build `1076226` and the installed proxy hash.
- `tools/verify_loader_api_runtime.py` — captures and validates fresh-session
  API evidence; stale-session, wrong-build, and current-session-error cases
  are covered by tests and a milestone gate.
- `research/MILESTONE_VERIFICATION_20260928.json` — historical aggregate result
  retained for traceability. The current milestone has since been refreshed to
  711 passing tests with all configured gates passing. The separate completion
  audit remains false because eight capability areas still need runtime or
  engine-boundary work.
- `docs/CURRENT_SOURCE_RELEASE_VERIFICATION_20260928.md` and
  `research/INSTALLER_CURRENT_SOURCE_20260928.json` — current-source portable
  and installer build evidence, exact embedded-payload hash matching, clean
  install, profile-preserving upgrade, owned-file uninstall, and GUI launch.

