import re

c_file = "runtime/native/source/ArchitectNativeRuntime.c"
with open(c_file, "r") as f:
    code = f.read()

patches = [
    ("cheat.shroud.toggle", "patchShroudReady", "g_patchShroudRecord", "cheat_toggle_shroud"),
    ("cheat.durability.toggle", "patchDurabilityReady", "g_patchDurabilityRecord", "cheat_toggle_durability"),
    ("cheat.falldamage.toggle", "patchFallDamageReady", "g_patchFallDamageRecord", "cheat_toggle_falldamage"),
    ("cheat.stealth.toggle", "patchStealthReady", "g_patchStealthModeRecord", "cheat_toggle_stealth"),
    ("cheat.oxygen.toggle", "patchOxygenReady", "g_patchOxygenRecord", "cheat_toggle_oxygen"),
    ("cheat.cold.toggle", "patchColdReady", "g_patchColdRecord", "cheat_toggle_cold"),
    ("cheat.parry.toggle", "patchParryReady", "g_patchParryRecord", "cheat_toggle_parry"),
    ("cheat.world.altar_area", "patchAltarAreaReady", "g_patchAltarAreaRecord", "cheat_toggle_altar_area"),
    ("cheat.world.altar_far", "patchAltarFarReady", "g_patchAltarFarRecord", "cheat_toggle_altar_far"),
    ("cheat.world.build_range", "patchBuildRangeReady", "g_patchBuildRangeRecord", "cheat_toggle_build_range"),
    ("cheat.world.plant_growth", "patchPlantGrowthReady", "g_patchPlantGrowthRecord", "cheat_toggle_plant_growth"),
    ("cheat.world.glider_stamina", "patchGliderStaminaReady", "g_patchGliderRecord", "cheat_toggle_glider_stamina"),
    ("cheat.skills.reset", "patchSkillResetReady", "g_patchSkillResetRecord", "cheat_toggle_skill_reset")
]

for action, ready_flag, record_var, toggle_func in patches:
    # We look for:
    # } else if (ascii_equal(action, "ACTION")) {
    #     accepted = TRUE;
    #     applied = TOGGLE();
    #     verified = applied;
    #     ok = applied;
    
    old_block_pattern = r'(\} else if \(ascii_equal\(action, "' + action + r'"\)\) \{)\s*accepted = TRUE;\s*applied = ' + toggle_func + r'\(\);\s*verified = applied;\s*ok = applied;'
    
    new_block = (
        r'\1\n'
        r'            if (!curState.buildSupported) {\n'
        r'                const char* msg = "' + action + r' rejected: BUILD_UNSUPPORTED.\\r\\n";\n'
        r'                append_file(g_logPath, msg, cstrlen(msg));\n'
        r'            } else if (!curState.' + ready_flag + r') {\n'
        r'                if (' + record_var + r'.recoveryRequired) {\n'
        r'                    const char* msg = "' + action + r' rejected: PATCH_RECOVERY_REQUIRED.\\r\\n";\n'
        r'                    append_file(g_logPath, msg, cstrlen(msg));\n'
        r'                } else {\n'
        r'                    const char* msg = "' + action + r' rejected: PATCH_TARGET_NOT_READY.\\r\\n";\n'
        r'                    append_file(g_logPath, msg, cstrlen(msg));\n'
        r'                }\n'
        r'            } else {\n'
        r'                accepted = TRUE;\n'
        r'                applied = ' + toggle_func + r'();\n'
        r'                verified = applied;\n'
        r'                ok = applied;\n'
        r'            }'
    )
    
    code = re.sub(old_block_pattern, new_block, code)

with open(c_file, "w") as f:
    f.write(code)

print("Replaced direct-patch commands in ArchitectNativeRuntime.c")
