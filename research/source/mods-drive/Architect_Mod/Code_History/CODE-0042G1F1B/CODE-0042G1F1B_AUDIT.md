# CODE-0042G1F1B — Registry normalization audit + position-read safety finding

Date: 2026-09-20
Build scope: Enshrouded 1076226
Current ArchitectRuntime.ps1 SHA-256: a0e97140bde5c77a328c083adfed08f6b5813ca0cd8a45b7a7babd2c4f655397
Current admin_action_registry.json SHA-256: 26cbca50914043a6ce038d0148e91319d23fdd3592b82923672009f8b68523cf
Registry actions: 54
Enabled: 17
Disabled: 37
Status: REGISTRY SCHEMA SOURCE-VERIFIED / NEW NATIVE-SAFETY BLOCKER FOUND / NO RUNTIME CLAIM

## G1F1B source verification

The current registry is now normalized to the preserved `architect.admin_action_registry.v2` vocabulary.

Independent source checks show:

- invalid `controlType`: 0
- invalid `evidenceStatus`: 0
- invalid `runtimeMode`: 0
- invalid `authority`: 0
- invalid `backend`: 0
- backendAdapter names outside the established adapter table: 0
- command IDs: 54 unique
- enabled actions: 17
- disabled actions: 37

`movement.position.read` remains correctly fail-closed:

- enabled: false
- evidenceStatus: `UNSOLVED`
- backend: `NONE`
- backendAdapter: `MovementAdapter`
- runtimeMode: `UNAVAILABLE`
- authority: `unknown`
- risk: `mutation`

The reported real `Import-AdminActionRegistry` PASS and lifecycle/test results are user/Codex-reported; the normalized registry content itself is source-verified here.

## Critical safety finding: `Get-CurrentPlayerPosition` still mutates native process state

The registry correctly disables `movement.position.read`, but the shared helper itself remains unsafe.

Current `Get-CurrentPlayerPosition` calls:

`[NativeMemoryEngine]::ReadPlayerCoordinates(...)`

twice: once with a zero pointer, then again with a candidate transform pointer.

Current `NativeMemoryEngine.ReadPlayerCoordinates(...)` unconditionally calls:

`EnsurePositionHook();`
`ReadCapturedPlayerTransform();`

before reading coordinates.

`EnsurePositionHook()` installs executable process state:
- allocates remote executable storage;
- writes code/data with `WriteProcessMemory`;
- patches the target instruction with a detour;
- changes page protection and flushes the instruction cache.

Therefore `Get-CurrentPlayerPosition` is not a read-only helper.

## Why this is urgent

`Render-DashboardPage` currently calls:

`$pos = Get-CurrentPlayerPosition`

unconditionally while rendering the Home page.

That means merely opening/rendering F7 Home can reach the executable position-hook installation path even though the canonical `movement.position.read` action is disabled.

The same helper is also used by:
- the disabled Mobility "READ CURRENT POS" handler;
- F8 corner-capture controls.

The safest minimal correction is to make `Get-CurrentPlayerPosition` itself fail closed and non-mutating. This protects every caller at the shared boundary.

## Required next step before scanner canonicalization

1. Remove all `NativeMemoryEngine.ReadPlayerCoordinates` calls from `Get-CurrentPlayerPosition`.
2. Do not substitute another guessed pointer/offset/native reader.
3. Use only an already-qualified non-mutating observer source if one actually exists in current source/evidence; otherwise return `$null`.
4. Make Home telemetry handle `$null` explicitly as "Coordinates: unavailable / safe source unresolved."
5. Remove the misleading Home label `AOB Scanner Verified`; scanner is still intentionally uncanonicalized and mutation-coupled.
6. Keep `movement.position.read` disabled and unchanged.
7. Add a regression test proving Home render cannot reach `ReadPlayerCoordinates` / `EnsurePositionHook` through `Get-CurrentPlayerPosition`.
8. Leave AOB Scanner raw for the subsequent G1F2 pass.

Only after this shared helper is fail-closed should scanner canonicalization continue.
