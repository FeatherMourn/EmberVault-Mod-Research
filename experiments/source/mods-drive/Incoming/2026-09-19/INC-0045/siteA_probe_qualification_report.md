### Architect Toolkit — Site A Observe-Only Probe Implementation & Verification Report

The isolated, observe-only diagnostic runtime probe at **RVA 0x291678** on Enshrouded build 1076226 has been implemented, validated, and qualified offline.

---

### 1. Files Changed

1. [NEW] **`runtime/native/source/ArchitectSiteAProbeEntry.asm`**: Complete 64-bit trampoline entry point preserving GPRs, `RFLAGS`, and `XMM0-XMM8` bit-for-bit, capturing parameters, and executing displaced instructions.
2. [MODIFIED] **`runtime/native/source/ArchitectNativeRuntime.c`**:
   - Added `SiteAProbeEvent` definition and 1024-entry atomic ring buffer.
   - Added non-blocking `architect_siteA_probe_capture` callback.
   - Added `install_siteA_probe` and `uninstall_siteA_probe` with 14-byte signature checks, fail-closed rollback, and instruction cache flushing.
   - Added `flush_siteA_probe_events` and `write_siteA_probe_status` to `bridge/siteA_probe.jsonl` and `bridge/siteA_probe_status.json`.
   - Wired command routing in `dispatch_command` (`diagnostics.siteA_probe.enable|disable|reset`) and standalone `siteA_probe_command.json`.
   - Added cleanup in `worker()` shutdown.
3. [MODIFIED] **`build_scripts/build_dll.py`**: Added `ArchitectSiteAProbeEntry.asm` to `ml64` compilation and linked `ArchitectSiteAProbeEntry.obj`.
4. [MODIFIED] **`build_scripts/run_all_tests.ps1`**: Added the Site A Probe Lifecycle & Rollback suite to the master test harness.
5. [MODIFIED] **`tests/test_direct_patch_integration.c`**: Added stub for `architect_siteA_probe_entry`.
6. [MODIFIED] **`tests/test_command_routing.c`**: Added stub for `architect_siteA_probe_entry`.
7. [MODIFIED] **`tests/build_and_run_transparency.py`**: Added `ArchitectSiteAProbeEntry.asm` assembly and object linking.
8. [MODIFIED] **`tests/test_hook_transparency.c`**: Added Site A hook site to `sites[]` and updated verification loop to 8 sites.
9. [NEW] **`tests/test_siteA_probe_lifecycle.c`**: Dedicated C lifecycle, observe, ring-buffer overflow, byte restoration, and failure-rollback test harness.
10. [NEW] **`tests/build_and_run_siteA_lifecycle.py`**: Compilation and execution runner for the lifecycle suite.

---

### 2. Exact Hook & Trampoline Code

#### Hook Detour Installation

- **Location**: RVA `0x291678` (`0x291678`–`0x291686`, 14 bytes)
- **Detour Format**: Register-neutral 14-byte absolute indirect jump:
  ```
  assembly
  ```
  svgsvg

  FF 25 00 00 00 00 [64-bit absolute address of architect_siteA_probe_entry]

#### Trampoline Code (`ArchitectSiteAProbeEntry.asm`)

```
assembly
```

svgsvg

option casemap\:none

EXTERN architect_siteA_probe_capture\:PROC

EXTERN g_siteAProbeContinue\:QWORD

PUBLIC architect_siteA_probe_entry

.code

architect_siteA_probe_entry PROC

    pushfq

    push    rax

    push    rcx

    push    rdx

    push    r8

    push    r9

    push    r10

    push    r11

    sub     rsp, 0C0h

    movdqu  xmmword ptr [rsp + 30h], xmm0

    movdqu  xmmword ptr [rsp + 40h], xmm1

    movdqu  xmmword ptr [rsp + 50h], xmm2

    movdqu  xmmword ptr [rsp + 60h], xmm3

    movdqu  xmmword ptr [rsp + 70h], xmm4

    movdqu  xmmword ptr [rsp + 80h], xmm5

    movdqu  xmmword ptr [rsp + 90h], xmm6

    movdqu  xmmword ptr [rsp + 0A0h], xmm7

    movdqu  xmmword ptr [rsp + 0B0h], xmm8

    mov     rcx, rax                     ; arg 1: accumulatorAddress (rax)

    movaps  xmm1, xmm6                   ; arg 2: delta (xmm6 before addss)

    movaps  xmm2, xmm0                   ; arg 3: distance3D (xmm0)

    movaps  xmm3, xmm8                   ; arg 4: distance_weight_scalar (xmm8)

    mov     rax, qword ptr [rsp + 150h]  ; tuple slot 4 (Component 4)

    mov     qword ptr [rsp + 20h], rax   ; arg 5: component4

    mov     rax, qword ptr [rsp + 158h]  ; tuple slot 5 (Component 5)

    mov     qword ptr [rsp + 28h], rax   ; arg 6: component5

    call    architect_siteA_probe_capture

    movdqu  xmm8, xmmword ptr [rsp + 0B0h]

    movdqu  xmm7, xmmword ptr [rsp + 0A0h]

    movdqu  xmm6, xmmword ptr [rsp + 90h]

    movdqu  xmm5, xmmword ptr [rsp + 80h]

    movdqu  xmm4, xmmword ptr [rsp + 70h]

    movdqu  xmm3, xmmword ptr [rsp + 60h]

    movdqu  xmm2, xmmword ptr [rsp + 50h]

    movdqu  xmm1, xmmword ptr [rsp + 40h]

    movdqu  xmm0, xmmword ptr [rsp + 30h]

    add     rsp, 0C0h

    pop     r11

    pop     r10

    pop     r9

    pop     r8

    pop     rdx

    pop     rcx

    pop     rax

    popfq

    ; Displaced instructions (semantics preserved exactly)

    addss   xmm6, dword ptr [rax]

    movss   dword ptr [rax], xmm6

    mov     r8d, 88h

    jmp     qword ptr [g_siteAProbeContinue]

architect_siteA_probe_entry ENDP

END

---

### 3. Expected Bytes

- **Target RVA**: `0x291678` (span: 14 bytes, ending at `0x291686`)
- **Expected Byte Sequence**:
  ```
  F3 0F 58 30 F3 0F 11 30 41 B8 88 00 00 00
  ```
- **Uniqueness Check**: Verified exactly **1 occurrence** in the `.text` section of target executable `enshrouded.exe` (SHA-256 `AF2F5A12...`, build 1076226).

---

### 4. Uninstall and Rollback Behavior

- **Uninstall Lifecycle**:
  1. Calls `VirtualProtect(g_siteAProbeTarget, 14, PAGE_EXECUTE_READWRITE, &oldProtect)`.
  2. Copies saved vanilla bytes (`g_siteAProbeOriginal`) back into `g_siteAProbeTarget`.
  3. Executes `FlushInstructionCache(GetCurrentProcess(), g_siteAProbeTarget, 14)`.
  4. Restores original memory protection.
  5. Clears target pointers (`g_siteAProbeTarget = 0`, `g_siteAProbeContinue = 0`) and sets `g_siteAProbeInstalled = FALSE`, `g_siteAProbeActive = FALSE`.
  6. Verified **100% bit-for-bit byte restoration** in unit and package tests.
- **Fail-Closed Rollback**:
  - If target bytes do not match `SITE_A_PROBE_EXPECTED` or if `VirtualProtect` fails, installation aborts immediately before modifying any memory.
  - Sets `g_siteAProbeLastError` to `"SIGNATURE_MISMATCH"` or `"VIRTUAL_PROTECT_RWX_FAILED"`.
  - Leaves target memory 100% untouched (no partial overwrite).

---

### 5. Telemetry Schema & Formats

#### Telemetry Record Structure

```
c
```

svgsvg

typedef struct {

    QWORD timestamp;

    DWORD serial;

    QWORD accumulatorAddress;   // rax (ECS Tuple Slot 10)

float accumulatorBefore;    // [rax] before addss

float delta;                // xmm6 before addss

float accumulatorAfter;     // before + delta

float distance3D;           // xmm0

float scalar;               // xmm8 (distance_weight_scalar)

    QWORD component4;           // Tuple Slot 4 (Component 4)

    QWORD component5;           // Tuple Slot 5 (Component 5)

} SiteAProbeEvent;

- **Data File**: `bridge/siteA_probe.jsonl`
  ```
  json
  ```
  svgsvg

  {"timestamp":1726765800,"serial":1,"accumulatorAddress":"0x000001FA82A31050","accumulatorBefore":42.500000,"delta":3.250000,"accumulatorAfter":45.750000,"distance3D":7.800000,"scalar":1.000000,"component4":"0x000001FA82A31020","component5":"0x000001FA82A31028"}
- **Status File**: `bridge/siteA_probe_status.json`
  ```
  json
  ```
  svgsvg

  {

  "probeInstalled": true,

  "probeActive": true,

  "probeEventCount": 1024,

  "droppedEventCount": 0,

  "probeLastError": "NONE"

  }

---

### 6. Hook Transparency Test Results

Harness: `tests/test_hook_transparency.c` linking `ArchitectSiteAProbeEntry.asm` and `ArchitectCheatCorrelationEntry.asm`.

```
svgsvg
```

\================================================================

     NATIVE HOOK TRANSPARENCY & REGISTER PURITY VERIFICATION    

\================================================================

[1/8] Testing Movement Hook Site (RVA 0x23AE34, 16 bytes)... -> PASS (100% BIT-FOR-BIT)

[2/8] Testing Stamina Hook Site  (RVA 0x23423F, 22 bytes)... -> PASS (100% BIT-FOR-BIT)

[3/8] Testing Health Hook Site   (RVA 0x233F82, 14 bytes)... -> PASS (100% BIT-FOR-BIT)

[4/8] Testing Mana Hook Site     (RVA 0x2343EB, 19 bytes)... -> PASS (100% BIT-FOR-BIT)

[5/8] Testing Jump Hook Site     (RVA 0x392A0B, 15 bytes)... -> PASS (100% BIT-FOR-BIT)

[6/8] Testing Skills Hook Site   (RVA 0x26CB30, 15 bytes)... -> PASS (100% BIT-FOR-BIT)

[7/8] Testing Daytime Hook Site  (RVA 0xCE518A, 20 bytes)... -> PASS (100% BIT-FOR-BIT)

[8/8] Testing SiteA Hook Site    (RVA 0x291678, 14 bytes)... -> PASS (100% BIT-FOR-BIT)

VERDICT: ALL 8 HOOK TRANSPARENCY TESTS PASSED WITH REGISTER PURITY.

---

### 7. Complete Master-Suite Result

Command: `powershell -ExecutionPolicy Bypass -File build_scripts/run_all_tests.ps1`

```
svgsvg
```

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

Site A Probe Lifecycle & Rollback                  : 8 / 8 PASS

Patch Readiness Regression Test                    : 13 / 13 PASS

Pipeline Regression Suite                          : 10 / 10 PASS

ADM-TEST-0002 Teleport Disarmament                 : 15 / 15 PASS

INC-0015 Hook-Off Baseline                         : 3 / 3 PASS

F7 Truthfulness & Safety Contract                  : 72 / 72 PASS

Headless WinForms UI Smoke                         : 31 / 31 PASS

\----------------------------------------------------------------------------------------

TOTAL SUITES TESTED: 16

TOTAL INVARIANTS TESTED & VERIFIED: 271 / 271 (100% Passing)

\========================================================================================

---

### 8. Packaged Artifact Extraction Verification

- Generated release archive: **`Export/Test_Builds/architect_toolkit.zip`**
- Extracted into a clean temporary verification directory (`temp_verify_probe`).
- **Packaged Verification Invariants**:
  - `ArchitectSiteAProbeEntry.asm` present in packaged source: **PASS**
  - `ArchitectNativeRuntime.c` probe implementations present: **PASS**
  - Standalone `test_siteA_probe_lifecycle.py` executed inside extracted package: **8 / 8 PASS**
  - Standalone `build_and_run_transparency.py` executed inside extracted package: **8 / 8 PASS**
  - Temporary verification directory cleaned up.

---

### 9. Final Artifact Hashes

| **ArtifactLocationSizeSHA-256** |                                                              |                   |                                                                    |
| ------------------------------- | ------------------------------------------------------------ | ----------------- | ------------------------------------------------------------------ |
| **Target Game Executable**      | `H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe` | 34,302,536 bytes  | `af2f5a1227911d8aa06b3908d6bd0211838211cae14ea91099cb57d0df990781` |
| **Native Runtime DLL**          | `runtime\native\ArchitectNativeRuntime.dll`                  | 278,528 bytes     | `7d89833691062afd955849c3d134b9f8f63660a105529fc1b48c42feee9db357` |
| **Packaged Release ZIP**        | `Export\Test_Builds\architect_toolkit.zip`                   | 237,534,213 bytes | `c9b837b96a4b5b54adb7d1f34eeea2aa7c95a21d0c408dc614358cf44447339d` |

*(Note: **`Architect_Mod/Current`** was neither designated nor replaced).*

---

### 10. Controlled Runtime Test Protocol

To run the diagnostic experiment in a clean game process:

1. **Deploy Toolkit**: Extract `architect_toolkit.zip` into the Enshrouded root folder and launch `enshrouded.exe` with injector.
2. **Start Probe**: Write to `bridge/command.json`:
   ```
   json
   ```
   svgsvg

   {"action": "diagnostics.siteA_probe.enable", "commandId": "cmd_probe_start"}

   (Or create `bridge/siteA_probe_command.json` containing `{"action": "enable"}`). Verify in `bridge/siteA_probe_status.json`: `"probeInstalled": true, "probeActive": true`.
3. **Execute Movement Sequence**:
   - **Phase 1 (Idle baseline)**: Stand stationary for 5 seconds. (Confirm `distance3D == 0` or near 0, `delta == 0`).
   - **Phase 2 (Ordinary walking)**: Walk forward in a straight line for 5 seconds.
   - **Phase 3 (Sprint)**: Sprint for 5 seconds.
   - **Phase 4 (Vanilla Glide)**: Jump from a cliff and glide normally with Glider Stamina OFF for \~5 seconds.
   - **Phase 5 (Enable Glider Patch)**: Enable the current glider stamina direct patch via F7 or command:
     ```
     json
     ```
     svgsvg

     {"action": "cheat.world.glider_stamina", "commandId": "cmd_glider_patch_on"}
   - **Phase 6 (Patched Glide)**: Glide from approximately the same height for \~5 seconds with Glider Stamina ON.
   - **Phase 7 (Disable Glider Patch)**: Disable glider patch:
     ```
     json
     ```
     svgsvg

     {"action": "cheat.world.glider_stamina", "commandId": "cmd_glider_patch_off"}
   - **Phase 8 (Stop Probe)**: Write to `bridge/command.json`:
     ```
     json
     ```
     svgsvg

     {"action": "diagnostics.siteA_probe.disable", "commandId": "cmd_probe_stop"}
4. **Inspect Telemetry**: Examine `bridge/siteA_probe.jsonl`.
   - Compare the same `accumulatorAddress` across Phase 4 (Vanilla Glide) vs Phase 6 (Patched Glide).
   - Check the sign and magnitude of `scalar` (`xmm8`).
   - If Phase 6 shows a residual nonzero `distance3D` and `delta` corresponding precisely to vertical descent rate (`dz`), the vertical-distance accumulation hypothesis is confirmed.