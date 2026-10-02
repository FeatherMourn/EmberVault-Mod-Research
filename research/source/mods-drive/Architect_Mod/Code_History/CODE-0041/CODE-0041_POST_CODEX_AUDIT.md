# CODE-0041 — Post-Codex audit of F7 foundation refactor

Date: 2026-09-20
Game build scope: Enshrouded 1076226
Baseline source: user-provided Architect Toolkit 0.42.0 intake INC-0062
Baseline ArchitectRuntime.ps1 SHA-256: f2053aea8c14110c12a428149c524f9a38655e8cb70e9fe040da2f6a7a12ac62
Current modified ArchitectRuntime.ps1 SHA-256: 1bbb4e8f379d58a592f554a4e6defb194f89c475781a811144fb6ad3eb06e444
Current admin_action_registry.json SHA-256: 092b83c5146a0a2ab7c63306534a5f0c5938729999e60980be2619dde194c8b3
Status: AUDITED / DO NOT RUNTIME TEST YET

## Executive result

The candidate contains useful UI-foundation work, but it is not safe/complete enough for in-game acceptance testing yet. The Codex summary overstates several points. The current file also regresses multiple fail-closed behaviors that were present in the uploaded 0.42.0 baseline.

Salvage the intended UI/nav work, but repair the regressions before runtime testing.

## Confirmed useful changes

1. `Bind-AdminActionControl` infrastructure was added.
2. Responsive helper constructors were added: `New-AdminPageRoot`, `New-AdminSection`, `New-AdminResponsiveGrid`.
3. The main F7 content surface is now a top-down `FlowLayoutPanel` with a width-tracking resize callback.
4. The 11 requested top-level page names were added to navigation.
5. Many newly exposed unsupported controls are visibly disabled.
6. Auto Loot capability metadata is now marked `STARTUP_CANARY_ONLY` and teleport capability metadata is marked disabled.

## Critical blocker 1 — canonical ActionId binding exists but is unused

`Bind-AdminActionControl` has zero call sites in the modified source. Therefore no executable F7 control is actually bound to a canonical ActionId through the new infrastructure.

This means the central truthfulness blocker identified by CODE-0037C/D/E remains unresolved. The JSON registry still has only 20 action entries.

Required repair: every executable user control must bind to one registry action ID, and the binding must be testable without parsing closure text.

## Critical blocker 2 — responsive helpers exist but are unused

`New-AdminPageRoot`, `New-AdminSection`, and `New-AdminResponsiveGrid` have zero call sites.

Existing page renderers still create fixed-position/fixed-size controls using `New-Panel`, `New-Label`, `New-Button`, direct `.Location`, and direct `.Size`. The new FlowLayoutPanel only stretches the outer child width; it does not reflow controls inside those fixed panels.

Therefore the original resize bug is not actually repaired at page level.

Required repair: migrate page content into responsive layout containers. Do not merely stretch fixed panels.

## Critical blocker 3 — teleport fail-closed was regressed

The uploaded 0.42.0 baseline had `Invoke-PlayerTeleport` return false and the dispatcher explicitly rejected teleport because local-player transform ownership is unresolved.

The modified source reintroduced:
- `NativeMemoryEngine::WritePlayerCoordinates`
- direct teleport success reporting
- direct teleport completion in both `Send-CheatCommand` and `Dispatch-AdminCommand`

This contradicts the capability metadata that says teleport is disabled and violates ADM-TEST-0002/current project safety state.

Required repair: restore hard fail-closed behavior at every dispatch layer. No coordinate write may occur.

## Critical blocker 4 — live Auto Loot is still executable before capability gating

The modified capability table correctly marks Auto Loot `STARTUP_CANARY_ONLY`, but `Send-CheatCommand` handles `loot.auto` / `cheat.autoloot.toggle` before capability checks and calls `NativeMemoryEngine::ToggleAutoLoot()`, returning success.

This bypasses the new metadata and source-consolidation policy.

Required repair: reject live Auto Loot before any mutation call. Startup resource/canary ownership remains the only current path.

## Critical blocker 5 — unproven Glider Flight / Gravity and C# mutation fallbacks were reintroduced

Compared with the 0.42.0 baseline, the modified source re-enables or directly calls several `NativeMemoryEngine` mutation paths, including Glider Flight, gravity patching, survival patch fallbacks, and direct byte-patch dispatch.

CODE-0036 established the in-process native runtime as sole mutation owner. The baseline intentionally avoided C# cross-process mutation in `Send-CheatCommand` and marked unproven Glider Flight unavailable.

Required repair: restore baseline ownership/safety semantics. UI refactor must not revive deprecated mutation paths.

## Critical blocker 6 — glider-stamina semantic safety was lost

The baseline explicitly forced the current glider-stamina patch unavailable because runtime evidence showed the patch slowed gliding but did not provide true infinite glider stamina semantics.

The modified capability code removed that semantic disable and can treat the patch as ready based on patch availability.

Required repair: restore the semantic mismatch block. A technically applicable patch is not equivalent to proven gameplay semantics.

## Critical blocker 7 — source-consolidation and CT catalog preservation was removed

The baseline loaded:
- `source_consolidation_catalog.json`
- `cheat_table_1013216_catalog.json`

and exposed Source Map / CT Catalog pages. The modified source removes those imports, summary state, renderers, and navigation entries rather than nesting them under Developer & Diagnostics.

This violates the requirement to preserve the 224-entry CT catalog and external-source provenance.

Required repair: restore these data sources and expose them under Developer & Diagnostics.

## Critical blocker 8 — CODE-0022B behavior was altered by deletion, not clean crash-guard presentation

The modified file removes `Publish-PlayerAttributeDiscoveryCommand` and the old dedicated Player Attributes page rather than preserving the crash-guarded research state with truthful disabled controls.

The product requirement is editable attributes/derived stats eventually, but the current crashy observer must stay disarmed. The correct UI state is planned/research + disabled, not silent deletion and not live ARM controls.

Required repair: restore provenance/status presentation without re-enabling the hook.

## Critical blocker 9 — headless-test guard regressed

The baseline skipped the executor mutex when `ARCHITECT_HEADLESS_TEST=1`. The modified source removed this condition and always enters the mutex path when newly created.

This is unrelated to the requested UI refactor and can interfere with headless test execution.

Required repair: restore the baseline headless-test guard unless a separately documented reason proves the change necessary.

## Navigation is only partially migrated

The 11 labels exist, but several are mapped to old combined renderers rather than true page ownership. Examples:
- World & Environment and Camera & Presentation both call `Render-WorldCameraPage`.
- Mods & Configuration calls the old `Render-SettingsDevPage`.
- Developer & Diagnostics calls Diagnostics + Codex, but Source Map and CT Catalog were removed.
- Player uses a large fixed-position combined renderer rather than responsive sections.

This is acceptable as an intermediate wiring step only if clearly labeled, but it is not a completed page migration.

## Registry remains incomplete

`admin_action_registry.json` still contains 20 actions. The new binding helper cannot solve truthfulness until the registry is expanded to every executable F7 control/action.

Do not bulk-enable actions while expanding the registry. Metadata may describe unsupported actions with `enabled=false`, explicit evidence state, backend, reason, risk, and readback/revert requirements.

## Verification assessment

`PS_PARSE_OK` proves only PowerShell syntax. It does not establish:
- safe dispatch behavior,
- complete canonical action binding,
- page-level responsive layout,
- truthfulness invariants,
- preservation of source catalogs,
- runtime behavior.

Because direct teleport/Auto Loot/mutation regressions are present, this candidate should not be runtime-tested until repaired.

## Next implementation pass

Perform a safety-first repair pass using the user-provided 0.42.0 baseline as the authoritative pre-refactor behavior source. Preserve only the intended UI/nav improvements that do not contradict baseline safety/evidence. Then:

1. restore fail-closed semantics and source catalogs;
2. actually bind every executable control to canonical ActionId;
3. expand the registry truthfully;
4. migrate page internals to responsive containers;
5. strengthen headless responsive/truthfulness tests;
6. only then run the in-game F7 resize acceptance test.
