### Architect Toolkit — Site A Probe Safety Correction & Production Lifecycle Closure

The safety corrections, transactional lifecycle state machine, and comprehensive 26-case test suite for the **Site A observe-only runtime probe** (RVA `0x291678`) on Enshrouded build `1076226` are fully implemented, verified, and packaged.

---

### 1. Master Suite Dynamic Verification Results

The complete master suite (`build_scripts\run_all_tests.ps1`) passed **16 / 16 test suites** and **289 / 289 individual invariants (100% Passing)**:

```
text
```

svgsvg

\========================================================================================

Architect Toolkit F7 Dynamic Verification Summary

\========================================================================================

Native DLL Compilation                             : 1 / 1 PASS

C# Compilation                                     : 72 / 72 PASS

PowerShell AST Syntax                              : 4 / 4 PASS

Packaging Verification                             : 1 / 1 PASS

Nested-ZIP Verification                            : 1 / 1 PASS

Command Routing Independence                       : 14 / 14 PASS

Direct Patch Integration                           : 3 / 3 PASS

Patch Engine Behavioral Lifecycle                  : 15 / 15 PASS

Synthetic Hook Transparency Harness                : 8 / 8 PASS

Site A Probe Lifecycle & Rollback                  : 26 / 26 PASS

Patch Readiness Regression Test                    : 13 / 13 PASS

Pipeline Regression Suite                          : 10 / 10 PASS

ADM-TEST-0002 Teleport Disarmament                 : 15 / 15 PASS

INC-0015 Hook-Off Baseline                         : 3 / 3 PASS

F7 Truthfulness & Safety Contract                  : 72 / 72 PASS

Headless WinForms UI Smoke                         : 31 / 31 PASS

\----------------------------------------------------------------------------------------

TOTAL SUITES TESTED: 16

TOTAL INVARIANTS TESTED & VERIFIED: 289 / 289 (100% Passing)

\========================================================================================

---

### 2. Comprehensive Production Lifecycle Suite (26 / 26 Raw Cases)

The lifecycle suite (`tests\test_siteA_probe_lifecycle.c`) was executed directly against production code with deterministic failure injection callbacks. All 26 explicit test cases passed:

| **#Raw Test NameResultVerified Semantics** |                                                          |          |                                                                                                                                                      |
| ------------------------------------------ | -------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1                                          | `clean install`                                          | **PASS** | Target validated, original bytes saved, RWX granted, detour written, readback verified, cache flushed, protection restored, and state initialized    |
| 2                                          | `detour readback`                                        | **PASS** | Exact detour-byte readback verification; byte mismatch triggers automatic fail-closed recovery                                                       |
| 3                                          | `signature mismatch`                                     | **PASS** | Fail-closed without memory write when target does not match 14-byte signature `F3 0F 58 30 F3 0F 11 30 41 B8 88 00 00 00`                            |
| 4                                          | `initial VirtualProtect failure`                         | **PASS** | Target pointer and continuation cleared; `INITIAL_VIRTUAL_PROTECT_FAILED` recorded                                                                   |
| 5                                          | `detour-write failure`                                   | **PASS** | Injected detour write failure triggers automatic recovery; original bytes restored                                                                   |
| 6                                          | `install FlushInstructionCache failure`                  | **PASS** | Injected flush failure triggers recovery; target restored                                                                                            |
| 7                                          | `install protection-restore failure`                     | **PASS** | Failure restoring original protection triggers recovery; error recorded                                                                              |
| 8                                          | `recovery success`                                       | **PASS** | Explicit recovery restores vanilla bytes, verifies readback, flushes cache, and resets `recoveryRequired = FALSE`                                    |
| 9                                          | `recovery byte-restore failure`                          | **PASS** | Failure during recovery byte restoration raises persistent `recoveryRequired = TRUE`                                                                 |
| 10                                         | `recovery cache-flush failure`                           | **PASS** | Cache flush failure during recovery raises `recoveryRequired = TRUE`                                                                                 |
| 11                                         | `recovery protection-restore failure`                    | **PASS** | Protection restore failure during recovery raises `recoveryRequired = TRUE`                                                                          |
| 12                                         | `recoveryRequired persistence`                           | **PASS** | While `recoveryRequired = TRUE`, all install and uninstall attempts fail-closed immediately with `RECOVERY_REQUIRED`                                 |
| 13                                         | `clean uninstall`                                        | **PASS** | Transactional uninstall restores vanilla bytes, verifies readback, flushes cache, restores protection, and clears probe state                        |
| 14                                         | `uninstall ownership mismatch`                           | **PASS** | Refuses uninstall if target bytes do not match Architect's exact installed detour                                                                    |
| 15                                         | `uninstall VirtualProtect failure`                       | **PASS** | Fails closed on initial RWX transition failure                                                                                                       |
| 16                                         | `uninstall restore/write failure`                        | **PASS** | Readback mismatch during uninstall triggers `recoveryRequired = TRUE`                                                                                |
| 17                                         | `uninstall byte-readback failure`                        | **PASS** | Byte corruption detected post-write in uninstall; sets `UNINSTALL_BYTE_READBACK_FAILED`                                                              |
| 18                                         | `uninstall FlushInstructionCache failure`                | **PASS** | Instruction cache flush failure raises `recoveryRequired = TRUE`                                                                                     |
| 19                                         | `uninstall protection-restore failure`                   | **PASS** | Protection restore failure raises `recoveryRequired = TRUE`                                                                                          |
| 20                                         | `in-flight disable/quiescence success`                   | **PASS** | `uninstall_siteA_probe()` safely waits for concurrent in-flight executions (`g_siteAInFlight == 0`) before retiring state                            |
| 21                                         | `in-flight quiescence timeout/failure`                   | **PASS** | Bounded wait loop times out after 500ms if thread remains in-flight; returns `IN_FLIGHT_QUIESCENCE_TIMEOUT`                                          |
| 22                                         | `continuation remains valid for an in-flight trampoline` | **PASS** | Continuation pointer `g_siteAProbeContinue` remains valid across quiescence timeout; ASM preloads continuation before decrementing `g_siteAInFlight` |
| 23                                         | `double enable`                                          | **PASS** | Idempotent clean enable without memory re-write or corruption                                                                                        |
| 24                                         | `double disable`                                         | **PASS** | Idempotent clean disable without error                                                                                                               |
| 25                                         | `reset while active policy`                              | **PASS** | `diagnostics.siteA_probe.reset` clears buffer indices and dropped counts under producer lock while keeping probe installed and active                |
| 26                                         | `exact vanilla-byte restoration`                         | **PASS** | 100% bit-for-bit restoration of original 14 vanilla bytes validated                                                                                  |

---

### 3. Synthetic Hook Transparency Harness (8 / 8 Passing)

All 8 native hook and probe entry points passed bit-for-bit register and flag purity:

```
text
```

svgsvg

[1/8] Testing Movement Hook Site (RVA 0x23AE34, 16 bytes)...     -> PASS (100% BIT-FOR-BIT)

[2/8] Testing Stamina Hook Site (RVA 0x23423F, 22 bytes)...      -> PASS (100% BIT-FOR-BIT)

[3/8] Testing Health Hook Site (RVA 0x233F82, 14 bytes)...       -> PASS (100% BIT-FOR-BIT)

[4/8] Testing Mana Hook Site (RVA 0x2343EB, 19 bytes)...         -> PASS (100% BIT-FOR-BIT)

[5/8] Testing Jump Hook Site (RVA 0x392A0B, 15 bytes)...         -> PASS (100% BIT-FOR-BIT)

[6/8] Testing Skills Hook Site (RVA 0x26CB30, 15 bytes)...       -> PASS (100% BIT-FOR-BIT)

[7/8] Testing Daytime Hook Site (RVA 0xCE518A, 20 bytes)...      -> PASS (100% BIT-FOR-BIT)

[8/8] Testing SiteA Hook Site (RVA 0x291678, 14 bytes)...        -> PASS (100% BIT-FOR-BIT)

VERDICT: ALL 8 HOOK TRANSPARENCY TESTS PASSED WITH REGISTER PURITY.

---

### 4. Packaged Source Verification from Clean Temporary Directory

The packaged artifact was extracted to a clean temporary directory and audited strictly from the packaged files (not the working tree):

1. **Worker Sequence**:
   - `worker()` calls `architect_bind_patch_engine_runtime()` immediately before `cheat_correlation_initialize(...)`: **VERIFIED**.
2. **Backend Readiness Definition**:
   - `out->mutationBackendReady = g_cc.buildSupported && architect_patch_engine_bound()`: **VERIFIED**.
3. **All 13 ****`patch*Ready`**** Definitions**:
   - Every definition (`patchShroud`, `patchDurability`, `patchFallDamage`, `patchStealth`, `patchOxygen`, `patchCold`, `patchParry`, `patchSkillReset`, `patchAltarArea`, `patchAltarFar`, `patchBuildRange`, `patchPlantGrowth`, `patchGliderStamina`) strictly gates on `out->mutationBackendReady` and requires `!record.recoveryRequired`: **VERIFIED**.
4. **Glider Dispatcher Gates**:
   - `cheat.world.glider_stamina` strictly checks:
     - `BUILD_UNSUPPORTED`
     - `MUTATION_BACKEND_UNAVAILABLE`
     - `PATCH_RECOVERY_REQUIRED`
     - `PATCH_TARGET_NOT_READY`
     - Writes `g_lastCommandFailureReason`: **VERIFIED**.
5. **Site A Command Isolation**:
   - `siteA_probe_command.json` is completely absent from the package: **VERIFIED**.
   - Single command path via `bridge\command.json` actions `diagnostics.siteA_probe.enable|disable|reset`: **VERIFIED**.
   - `recoveryRequired`, `inFlight`, `installedByArchitect`, and `installReadbackValid` verified in packaged state: **VERIFIED**.
6. **In-Package Test Execution**:
   - Both `build_and_run_siteA_lifecycle.py` (26/26) and `build_and_run_transparency.py` (8/8) executed and passed inside the extracted package: **VERIFIED**.

---

### 5. Final Artifact Identifiers & Hashes

| **ArtifactLocationSHA-256Size** |                                                              |                                                                    |                  |
| ------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------ | ---------------- |
| **Target Game Executable**      | `H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe` | `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781` | 34,302,536 bytes |
| **Native Runtime DLL**          | `runtime\native\ArchitectNativeRuntime.dll`                  | `18bf637df113fd6f599956d111d5486b7027d84e47405cf9de79405535dac77f` | 282,112 bytes    |
| **Final Packaged ZIP**          | `Export\Test_Builds\architect_toolkit.zip`                   | `28552e49ad433e29dac24032704b41eb4e7cd9f652dfdbeae3101b917165bb9d` | 22,317,449 bytes |

*(Note: **`Architect_Mod/Current`** was neither designated nor modified).*