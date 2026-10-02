# CODE-0037 — F7 Integration Cleanup + First Operational Feature Gate

Work against the **latest Architect Toolkit working tree that produced the most recent coding-agent candidate**, but **DO NOT replace or designate `Architect_Mod/Current`** in this task. The canonical Current baseline remains the user-designated Drive package at:

`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\architect_toolkit.zip`

Game build scope is **Enshrouded revision 1076226** only.
Exact game EXE SHA-256 gate must remain:

`af2f5a1227911d8aa06b3908d6bd0211838211cae14ea91099cb57d0df990781`

Use the project method: observe → capture → map → validate → minimally modify → verify. Do not invent offsets, pointers, layouts, APIs, or runtime behavior. Fail closed on uncertainty. Preserve working infrastructure and do not redesign unrelated systems.

## Purpose

The latest coding-agent candidate contains real progress, but the source is not currently qualified because later edits occurred after the reported 289/289 run and several unsafe/duplicate paths were reintroduced. CODE-0037 is a **cleanup/hardening build**, not a feature-expansion build.

The goal is to produce one final package that is safe and truthful enough for a focused runtime session testing:

1. Storage expansion
2. Auto Loot canary (Stone + Fog Essence only)
3. Free Craft ON/OFF

Do **not** implement new flight, teleport, player-vitals, inventory spawning, or world-mutation features in this task.

## Evidence and required interpretations

Treat these as established project constraints for build 1076226:

- Current Glider patch at RVA `0x39E73C` is **DISPROVEN as Infinite Glider Stamina**. User-confirmed gameplay shows it slows glide movement and only indirectly reduces stamina drain. Do not expose it as Infinite Glider Stamina.
- Teleport/local-player transform ownership is **UNSOLVED**. Previous transform experimentation caused severe runtime failures. Teleport must remain fail-closed.
- Auto Loot KFC/resource mapping is strong: current KFC validates the donor component family `keen::ecs::IsPlayerInRange`, `keen::ecs::PickupItemZone`, `keen::ecs::TriggerShape`, with catalogs of 47 gravity-loot templates, 46 material-loot templates, and 462 gather/drop templates. Runtime Auto Loot semantics are still unproven.
- Storage KFC mapping validates 12 storage templates using `keen::ecs::InventorySetup` and the expected `genericSlotCount` / `availableSlotCount` fields. Runtime behavior is still pending.
- Stack-size resource mutation already produced runtime `stack=1901`, matching the current KFC stackable ItemInfo count. Preserve this path unless a test proves it broken.
- Free Craft native target is currently the strongest new native candidate and must be preserved:
  - RVA `0x3822D1`
  - original bytes: `44 8B A5 08 01 00 00`
  - patch bytes: `41 BC 00 00 00 00 90`
  - length 7
  - latest packaged runtime evidence reported `patchFreeCraftReady=true` with mutation backend ready.
  This proves readiness/expected-byte convergence, **not gameplay semantics**. Runtime ON/OFF validation is still required.
- Historical Shroudtopia Flight Mod is useful external evidence but the latest C# Always Flying implementation is **not qualified** as equivalent. Do not repair/replace flight in CODE-0037; only disarm the unsafe current implementation.

## Required source changes

### 1. Re-disarm teleport completely

Find every teleport path, including special cases before the normal fail-closed dispatcher.

Required final behavior:

- `Send-CheatCommand` must not bypass the registry/capability gate for teleport.
- `Invoke-PlayerTeleport` must not write coordinates.
- `NativeMemoryEngine.WritePlayerCoordinates` must perform **no `WriteProcessMemory` mutation** while local-player transform ownership is unresolved.
- No fallback may return success/"queued" after a failed or skipped write.
- Teleport-related UI/actions remain visibly unavailable/disabled with a truthful reason.
- Add regression tests proving every known teleport alias/action fails closed and no write path is reachable.

Do not delete historical diagnostic/read-only structures if other code uses them; isolate mutation instead.

### 2. Make Auto Loot single-owner and canary-only

The current candidate has two competing mechanisms: vanilla ECS/resource composition plus simulated `E` key presses. Remove the simulated-input owner.

Required final behavior:

- Remove/disable all Auto Loot `keybd_event`, `VK_E`, timer/pulse, or equivalent simulated-interact logic from `NativeMemoryEngine` and PowerShell/UI routing.
- Auto Loot must be owned only by the startup EML/resource path.
- Set config to:
  - `scope = "canary"`
  - `tuneGatherDrops = false`
- Canary targets must be limited to the existing Stone gravity-loot target and Fog Essence material-loot target already defined by the QoL profile.
- Keep the full 47/46/462 catalogs in data/profile form for future expansion, but do not activate them in this build.
- Preserve fail-closed donor validation and Variant access via `component.type` / `component.value`.
- Preserve rollback/skip behavior if donor components cannot be copied safely.
- Status output must clearly report template index count, storage patch count, Auto Loot scope, gravity/material patch counts, gather tuning state, and first error.

Expected successful runtime canary status is approximately:

`stack=1901 storage=12 autoLoot=canary gravity=1 material=1 errors=0`

Do not hardcode success solely to those counts; publish actual counts and fail closed on mismatch.

### 3. Disarm the current Always Flying C# mutation

The latest implementation rewrites a RIP-relative `movss` target and contains an unqualified hardcoded fallback. It is not sufficiently proven.

Required final behavior:

- No Always Flying memory mutation is reachable in CODE-0037.
- Remove/disable the hardcoded fallback RVA/address path.
- UI/registry should show flight as unavailable/experimental with a truthful reason.
- Preserve any read-only candidate/signature metadata useful for the next research task.
- Do not implement a replacement flight hook in this task.

### 4. Retire the false Infinite Glider Stamina semantic

- Disable the existing user-facing Infinite Glider Stamina control/action that resolves to the `0x39E73C` movement-scalar patch.
- Do not present reduced drain as infinite stamina.
- Preserve the underlying target as research evidence only if useful.
- If keeping any diagnostic label, use a neutral description such as `glider movement scalar candidate`, not a stamina claim.
- Add a truthfulness regression test so this action cannot become available again without new evidence.

### 5. Preserve and harden Free Craft; do not broaden it

Keep the native `0x3822D1` Free Craft patch in the hardened Architect patch engine.

Requirements:

- Exact build fingerprint gate remains mandatory.
- Expected original bytes must match before readiness becomes true.
- Apply uses the existing patch engine lifecycle and readback.
- Revert restores exact original bytes with readback.
- Failure sets truthful failure/recovery state.
- Do not add fallback addresses or a second mutation owner.
- Do not couple Free Craft to the monolithic hook framework if it is a direct-patch action.
- Add/retain explicit tests for readiness, apply, readback, revert, double-toggle, failed protection/write/readback recovery, and command-routing independence where applicable.

Do not claim Free Craft is PROVEN in gameplay; this build only needs to make the runtime test safe and truthful.

### 6. Fix test drift and make the master suite authoritative again

The current `VERIFICATION_REPORT.txt` is stale because significant source edits occurred after it, and `tests/code0036/test_qol_integration.py` is not included in the master runner.

Required final state:

- `build_scripts/run_all_tests.ps1` must invoke `tests/code0036/test_qol_integration.py`.
- Add a CODE-0037 regression suite covering at minimum:
  - teleport fully disarmed/no reachable write
  - no Auto Loot E-key simulation
  - Auto Loot config is canary and gather tuning false
  - Always Flying mutation/fallback disarmed
  - false Infinite Glider Stamina action unavailable
  - Free Craft remains routed through the hardened native direct-patch owner
  - build identity is single-sourced
- Do not weaken or delete existing safety tests simply to make the suite green.
- Packaging test must fail on nested ZIPs anywhere in the release package.
- Do not report a fixed invariant count in advance. Report the actual suite count after CODE-0036/CODE-0037 tests are included.

### 7. Bump and single-source the build identity

Create the next identity through the existing authoritative identity architecture, not duplicated literals.

Use:

- version: `0.41.0`
- buildId: `architect-v041-f7-integration-code0037-20260919`
- mode: `hybrid_observer_and_admin_mutation`

`runtime/build_identity.json` remains authoritative. The native header must be generated/synchronized through the existing build process, and the injector/launcher must consume the same authoritative definition.

Preserve the exact Enshrouded EXE SHA gate. Generate a new DLL SHA after the final build and update the existing hash file/check mechanism normally.

## Verification order — mandatory

Do not declare success because the code compiles.

Use this exact sequence:

1. Make all source changes.
2. Run targeted CODE-0036 and CODE-0037 tests while iterating.
3. Build the native DLL from final source.
4. Run the complete master suite from the final source tree.
5. Package the toolkit.
6. Verify zero nested ZIPs and required files in the package.
7. Extract the exact final ZIP to a clean temporary directory.
8. Run the complete master suite against the extracted packaged tree (or the maximum equivalent package-linked verification if a specific test cannot run from extraction; explicitly identify any exception).
9. Compute final SHA-256 values for DLL and ZIP.
10. **No source edits after the final package-linked master verification.** If any source file changes, repeat steps 3–9.

## Runtime-test handoff to produce

Do not run or claim in-game proof yourself unless you actually have a live game process and captured runtime evidence. Produce a concise runtime handoff for the user with this sequence:

1. Fresh Enshrouded process, build 1076226.
2. Inject/launch Architect and verify:
   - candidate DLL SHA matches `SHA256.txt`
   - `loadedInsideGame=true`
   - `buildFingerprintValidated=true`
   - version/buildId/mode match 0.41/CODE-0037 exactly
   - no identity warning
3. Verify QoL startup status before gameplay:
   - no error
   - storage patched on expected templates
   - Auto Loot `scope=canary`
   - gravity patched = 1
   - material patched = 1
   - gather tuning disabled
4. Storage gameplay test: inspect multiple affected containers and confirm expanded slots without corruption.
5. Auto Loot Stone canary: approach dropped/mined Stone from several meters away; verify pickup behavior and no repeated-interact side effects.
6. Auto Loot Fog Essence canary: same validation.
7. Free Craft OFF baseline: craft/build something and confirm normal material consumption.
8. Free Craft ON: enable once; require accepted/applied/verified/success, then craft/build comparable item and observe material behavior.
9. Free Craft OFF: require exact revert/readback, then confirm vanilla material consumption returns.
10. Clean shutdown; preserve status/log files.

Do not test Teleport, Always Flying, or Infinite Glider Stamina in CODE-0037; they must be disabled.

## Deliverables

Return:

- exact files changed with one-line purpose each
- root-cause summary for every removed/disarmed path
- targeted-test results
- final master-suite results with actual invariant count
- packaged-extraction verification results
- final DLL SHA-256 and size
- final ZIP SHA-256 and size
- nested ZIP count
- final identity values
- runtime-test handoff
- explicit statement that `Architect_Mod/Current` was not replaced

Also state clearly which features are:

- `OFFLINE_QUALIFIED_RUNTIME_TEST_READY`
- `DISABLED_UNPROVEN`
- `RUNTIME_PROOF_PENDING`

Do not promote any feature to PROVEN based only on compilation or offline tests.
