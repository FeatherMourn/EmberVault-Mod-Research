import re

# 1. Update ArchitectPatchEngine.h
with open('runtime/native/source/ArchitectPatchEngine.h', 'r') as f:
    h_code = f.read()

if 'int architect_patch_engine_bound(void);' not in h_code:
    h_code = h_code.replace('BOOL safe_revert_record(', 'int architect_patch_engine_bound(void);\nBOOL safe_revert_record(')
    with open('runtime/native/source/ArchitectPatchEngine.h', 'w') as f:
        f.write(h_code)

# 2. Update ArchitectPatchEngine.c
with open('runtime/native/source/ArchitectPatchEngine.c', 'r') as f:
    c_code = f.read()

if 'int architect_patch_engine_bound' not in c_code:
    binder = """int architect_patch_engine_bound(void) {
    return (g_arch_VirtualProtect != 0 && g_arch_memcpy != 0 && g_arch_FlushInstructionCache != 0) ? 1 : 0;
}
"""
    c_code = c_code.replace('BOOL safe_patch_record(', binder + '\nBOOL safe_patch_record(')
    c_code = c_code.replace('BOOL safe_patch_record(ArchitectPatchRecord* record, const char* name) {\n', 
                            'BOOL safe_patch_record(ArchitectPatchRecord* record, const char* name) {\n    if (!architect_patch_engine_bound()) return FALSE;\n')
    with open('runtime/native/source/ArchitectPatchEngine.c', 'w') as f:
        f.write(c_code)

# 3. Update CheatCorrelationHarness.c
with open('runtime/native/source/CheatCorrelationHarness.c', 'r') as f:
    cc_code = f.read()

cc_code = cc_code.replace('out->mutationBackendReady = g_cc.buildSupported;', 'out->mutationBackendReady = g_cc.buildSupported && architect_patch_engine_bound();')

patches = ["Shroud", "Durability", "FallDamage", "StealthMode", "Oxygen", "Cold", "Parry", "SkillReset", "AltarArea", "AltarFar", "BuildRange", "PlantGrowth", "Glider"]
for p in patches:
    regex = r'out->patch' + p + r'(Stamina)?Ready = g_cc\.buildSupported && g_patch' + p + r'Record\.target && \(arch_bytes_equal\([^\|]+\|\| \(arch_bytes_equal\([^\)]+\) && .*? && !g_patch' + p + r'Record\.recoveryRequired\)\);'
    match = re.search(regex, cc_code)
    if match:
        original = match.group(0)
        new_val = original.replace('&& (arch_bytes_equal', f'&& !g_patch{p}Record.recoveryRequired && (arch_bytes_equal')
        new_val = new_val.replace(f' && !g_patch{p}Record.recoveryRequired));', '));')
        cc_code = cc_code.replace(original, new_val)
with open('runtime/native/source/CheatCorrelationHarness.c', 'w') as f:
    f.write(cc_code)

# 4. Update ArchitectNativeRuntime.c
with open('runtime/native/source/ArchitectNativeRuntime.c', 'r') as f:
    anr_code = f.read()

if 'char g_lastCommandFailureReason[128]' not in anr_code:
    anr_code = anr_code.replace('char g_lastProcessedCommandId[64];', 'char g_lastProcessedCommandId[64];\nchar g_lastCommandFailureReason[128] = {0};')

if 'architect_patch_memcpy_adapter' not in anr_code:
    adapter = """
static void* architect_patch_memcpy_adapter(void* dest, const void* src, size_t count) {
    if (count > 0xFFFFFFFFULL) return 0;
    mem_copy((BYTE*)dest, (const BYTE*)src, (DWORD)count);
    return dest;
}
"""
    anr_code = anr_code.replace('static void mem_copy(BYTE* dest, const BYTE* src, DWORD len) {', adapter + '\nstatic void mem_copy(BYTE* dest, const BYTE* src, DWORD len) {')

if 'g_arch_VirtualProtect =' not in anr_code:
    binder = """
        g_arch_VirtualProtect = (int (*)(void*, size_t, unsigned long, unsigned long*))VirtualProtect;
        g_arch_memcpy = architect_patch_memcpy_adapter;
        g_arch_FlushInstructionCache = (int (*)(void*, const void*, size_t))FlushInstructionCache;
"""
    anr_code = anr_code.replace('cheat_correlation_initialize(buildSupported);', binder + '\n        cheat_correlation_initialize(buildSupported);')

if 'lastCommandFailureReason' not in anr_code:
    anr_code = anr_code.replace(
        'p = append_ascii(g_cheatCorrelationJson, p, sizeof(g_cheatCorrelationJson), "\\",\\r\\n  \\"lastFailure\\": \\"");',
        'p = append_ascii(g_cheatCorrelationJson, p, sizeof(g_cheatCorrelationJson), "\\",\\r\\n  \\"lastCommandFailureReason\\": \\"");\n      p = append_json_string(g_cheatCorrelationJson, p, sizeof(g_cheatCorrelationJson), g_lastCommandFailureReason[0] ? g_lastCommandFailureReason : "NONE");\n      p = append_ascii(g_cheatCorrelationJson, p, sizeof(g_cheatCorrelationJson), "\\",\\r\\n  \\"lastFailure\\": \\"");'
    )

direct_patches = [
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
for action, ready_flag, record_var, toggle_func in direct_patches:
    old_block_regex = r'\} else if \(ascii_equal\(action, "' + action + r'"\)\) \{.*?\} else \{\s*accepted = TRUE;\s*applied = ' + toggle_func + r'\(\);\s*verified = applied;\s*ok = applied;\s*\}'
    new_block = (
        '} else if (ascii_equal(action, "' + action + '")) {\n'
        '            if (!curState.buildSupported) {\n'
        '                const char* msg = "' + action + ' rejected: BUILD_UNSUPPORTED.\\r\\n";\n'
        '                append_file(g_logPath, msg, cstrlen(msg));\n'
        '                ccopy(g_lastCommandFailureReason, sizeof(g_lastCommandFailureReason), "BUILD_UNSUPPORTED", 17);\n'
        '            } else if (!curState.mutationBackendReady) {\n'
        '                const char* msg = "' + action + ' rejected: MUTATION_BACKEND_UNAVAILABLE.\\r\\n";\n'
        '                append_file(g_logPath, msg, cstrlen(msg));\n'
        '                ccopy(g_lastCommandFailureReason, sizeof(g_lastCommandFailureReason), "MUTATION_BACKEND_UNAVAILABLE", 28);\n'
        '            } else if (!curState.' + ready_flag + ') {\n'
        '                if (' + record_var + '.recoveryRequired) {\n'
        '                    const char* msg = "' + action + ' rejected: PATCH_RECOVERY_REQUIRED.\\r\\n";\n'
        '                    append_file(g_logPath, msg, cstrlen(msg));\n'
        '                    ccopy(g_lastCommandFailureReason, sizeof(g_lastCommandFailureReason), "PATCH_RECOVERY_REQUIRED", 23);\n'
        '                } else {\n'
        '                    const char* msg = "' + action + ' rejected: PATCH_TARGET_NOT_READY.\\r\\n";\n'
        '                    append_file(g_logPath, msg, cstrlen(msg));\n'
        '                    ccopy(g_lastCommandFailureReason, sizeof(g_lastCommandFailureReason), "PATCH_TARGET_NOT_READY", 22);\n'
        '                }\n'
        '            } else {\n'
        '                g_lastCommandFailureReason[0] = 0;\n'
        '                accepted = TRUE;\n'
        '                applied = ' + toggle_func + '();\n'
        '                verified = applied;\n'
        '                ok = applied;\n'
        '            }'
    )
    anr_code = re.sub(old_block_regex, new_block, anr_code, flags=re.DOTALL)
with open('runtime/native/source/ArchitectNativeRuntime.c', 'w') as f:
    f.write(anr_code)

print("Updates completed successfully.")
