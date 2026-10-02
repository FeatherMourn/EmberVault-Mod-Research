import os
import re
import sys

base_dir = r"temp_verify\architect_toolkit\runtime\native\source"
anr = os.path.join(base_dir, "ArchitectNativeRuntime.c")
cch = os.path.join(base_dir, "CheatCorrelationHarness.c")

if not os.path.exists(anr) or not os.path.exists(cch):
    print("Extracted source files not found.")
    sys.exit(1)

with open(anr, 'r') as f:
    anr_code = f.read()

with open(cch, 'r') as f:
    cch_code = f.read()

errors = []

# 1. Verify worker() binding order
worker_match = re.search(r'static DWORD __stdcall worker\(LPVOID ignored\) \{.*?architect_bind_patch_engine_runtime\(\);\s*cheat_correlation_initialize\(', anr_code, re.DOTALL)
if not worker_match:
    errors.append("worker() does not call architect_bind_patch_engine_runtime() before cheat_correlation_initialize()")
else:
    print("[PASS] worker() -> architect_bind_patch_engine_runtime() -> cheat_correlation_initialize(...)")

# 2. Verify mutationBackendReady
if 'out->mutationBackendReady = g_cc.buildSupported && architect_patch_engine_bound();' not in cch_code:
    errors.append("mutationBackendReady is not correctly initialized.")
else:
    print("[PASS] mutationBackendReady = g_cc.buildSupported && architect_patch_engine_bound()")

# 3. Verify all 13 patch*Ready use out->mutationBackendReady and !record.recoveryRequired
patches = ["Shroud", "Durability", "FallDamage", "Stealth", "Oxygen", "Cold", "Parry", "SkillReset", "AltarArea", "AltarFar", "BuildRange", "PlantGrowth", "GliderStamina"]
for p in patches:
    # Ensure it uses out->mutationBackendReady
    if f'out->patch{p}Ready = out->mutationBackendReady &&' not in cch_code:
        errors.append(f"patch{p}Ready does not use out->mutationBackendReady")
    # Ensure it requires !recoveryRequired
    # We map the Ready variable name to the Record variable name roughly
    rec = p
    if p == "GliderStamina": rec = "Glider"
    if p == "Stealth": rec = "StealthMode"
    if f'!g_patch{rec}Record.recoveryRequired' not in cch_code:
        errors.append(f"patch{p}Ready does not require !g_patch{rec}Record.recoveryRequired")

if not any("patch" in e for e in errors):
    print("[PASS] All 13 patch*Ready definitions use out->mutationBackendReady and require !record.recoveryRequired")

# 4. Verify Glider dispatcher gates
glider_block = re.search(r'cheat\.world\.glider_stamina"(.*?)cheat\.skills\.reset"', anr_code, re.DOTALL)
if not glider_block:
    errors.append("Could not find Glider dispatcher block.")
else:
    block = glider_block.group(1)
    if 'BUILD_UNSUPPORTED' not in block or 'MUTATION_BACKEND_UNAVAILABLE' not in block or 'PATCH_RECOVERY_REQUIRED' not in block or 'PATCH_TARGET_NOT_READY' not in block:
        errors.append("Glider dispatcher does not contain all required gates.")
    else:
        print("[PASS] Glider dispatcher gates: BUILD_UNSUPPORTED, MUTATION_BACKEND_UNAVAILABLE, PATCH_RECOVERY_REQUIRED, PATCH_TARGET_NOT_READY")

# 5. Verify lastCommandFailureReason in JSON output
if '"lastCommandFailureReason": ' not in anr_code:
    errors.append("lastCommandFailureReason not found in JSON output string (write_cheat_correlation_status).")
else:
    print("[PASS] lastCommandFailureReason JSON publication is present")

if errors:
    print("\\nERRORS FOUND:")
    for e in errors: print(f" - {e}")
    sys.exit(1)

print("\\nALL PACKAGED SOURCE INVARIANTS VERIFIED.")
sys.exit(0)
