import re
import sys

with open('runtime/native/source/ArchitectNativeRuntime.c', 'r') as f:
    c = f.read()

patches = [
    ("cheat.shroud.toggle", "patchShroudReady", "cheat_toggle_shroud"),
    ("cheat.durability.toggle", "patchDurabilityReady", "cheat_toggle_durability"),
    ("cheat.falldamage.toggle", "patchFallDamageReady", "cheat_toggle_falldamage"),
    ("cheat.stealth.toggle", "patchStealthReady", "cheat_toggle_stealth"),
    ("cheat.oxygen.toggle", "patchOxygenReady", "cheat_toggle_oxygen"),
    ("cheat.cold.toggle", "patchColdReady", "cheat_toggle_cold"),
    ("cheat.parry.toggle", "patchParryReady", "cheat_toggle_parry"),
    ("cheat.world.altar_area", "patchAltarAreaReady", "cheat_toggle_altar_area"),
    ("cheat.world.altar_far", "patchAltarFarReady", "cheat_toggle_altar_far"),
    ("cheat.world.build_range", "patchBuildRangeReady", "cheat_toggle_build_range"),
    ("cheat.world.plant_growth", "patchPlantGrowthReady", "cheat_toggle_plant_growth"),
    ("cheat.world.glider_stamina", "patchGliderStaminaReady", "cheat_toggle_glider_stamina"),
    ("cheat.skills.reset", "patchSkillResetReady", "cheat_toggle_skill_reset")
]

passed = 0
failed = 0

print("================================================================")
print("     NATIVE COMMAND ROUTING INDEPENDENCE VERIFICATION           ")
print("================================================================")

for action, readyFlag, func in patches:
    # Need to match non-greedy blocks
    regex = r'\} else if \(ascii_equal\(action, "' + action + r'"\)\) \{.*?if \(!curState\.buildSupported\) \{.*?\} else if \(!curState\.' + readyFlag + r'\) \{.*?\} else \{.*?applied = ' + func + r'\(\);'
    match = re.search(regex, c, re.DOTALL)
    
    if match:
        block = match.group(0)
        if "cheat_correlation_begin" in block:
            print(f"    -> FAIL: {action} incorrectly calls cheat_correlation_begin")
            failed += 1
        else:
            print(f"[PASS] {action} routed independently of hook framework.")
            passed += 1
    else:
        print(f"    -> FAIL: {action} does not have the independent routing gate.")
        failed += 1

print("----------------------------------------------------------------------------------------")
print(f"TEST RESULTS: {passed} / {passed + failed} PASSED")

if failed > 0:
    sys.exit(1)



worker_match = re.search(r'static DWORD __stdcall worker\(LPVOID ignored\) \{.*?architect_bind_patch_engine_runtime\(\);\s*cheat_correlation_initialize\(', c, re.DOTALL)
if not worker_match:
    print('FAIL: worker() does not call architect_bind_patch_engine_runtime() right before cheat_correlation_initialize()')
    import sys
    sys.exit(1)
print('[PASS] worker() structural binding order verified')
