import re

with open(r"runtime\native\source\CheatCorrelationHarness.h", "r") as f:
    hdr = f.read()

hdr_add = """
typedef struct ArchitectPatchRecord {
    BYTE* target;
    const BYTE* validatedOriginalBytes;
    const BYTE* patchBytes;
    DWORD length;
    BYTE savedOriginalBytes[32];
    BOOL installedByArchitect;
    BOOL writeReadback;
    BOOL revertAvailability;
} ArchitectPatchRecord;

// safe patch record functions
BOOL safe_patch_record(ArchitectPatchRecord* record, const char* name);
BOOL safe_revert_record(ArchitectPatchRecord* record, const char* name);
"""

if "ArchitectPatchRecord" not in hdr:
    hdr = hdr.replace("BOOL safe_patch_bytes", hdr_add + "\nBOOL safe_patch_bytes")
    with open(r"runtime\native\source\CheatCorrelationHarness.h", "w") as f:
        f.write(hdr)

with open(r"runtime\native\source\CheatCorrelationHarness.c", "r") as f:
    src = f.read()

# Remove old target/original definitions
src = re.sub(r"static BYTE\* g_patch[a-zA-Z0-9_]+Target = 0;\s*static BYTE g_patch[a-zA-Z0-9_]+Original(\[[0-9]+\])?(\s*=\s*\{?[^;]+\}?| = 0x[0-9a-fA-F]+);\n", "", src)

# Add new ArchitectPatchRecord definitions
records = """
ArchitectPatchRecord g_patchShroudRecord = {0, (const BYTE*)"\\x40\\x55\\x41\\x54\\x41\\x55", (const BYTE*)"\\xC3\\x55\\x41\\x54\\x41\\x55", 6, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchDurabilityRecord = {0, (const BYTE*)"\\x40\\x55\\x41\\x55\\x48\\x8D", (const BYTE*)"\\xC3\\x55\\x41\\x55\\x48\\x8D", 6, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchFallDamageRecord = {0, (const BYTE*)"\\x40\\x53\\x48\\x83\\xEC\\x60", (const BYTE*)"\\xC3\\x53\\x48\\x83\\xEC\\x60", 6, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchStealthModeRecord = {0, (const BYTE*)"\\x48\\x89\\x4C\\x24\\x08\\x55", (const BYTE*)"\\xC3\\x89\\x4C\\x24\\x08\\x55", 6, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchOxygenRecord = {0, (const BYTE*)"\\x40\\x55\\x41\\x55\\x41\\x56", (const BYTE*)"\\xC3\\x55\\x41\\x55\\x41\\x56", 6, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchColdRecord = {0, (const BYTE*)"\\x40\\x55\\x56\\x48\\x8D\\x6C", (const BYTE*)"\\xC3\\x55\\x56\\x48\\x8D\\x6C", 6, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchParryRecord = {0, (const BYTE*)"\\x74\\x78", (const BYTE*)"\\x90\\x90", 2, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchSkillResetRecord = {0, (const BYTE*)"\\x48\\x89\\x6C", (const BYTE*)"\\x31\\xC0\\xC3", 3, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchAltarAreaRecord = {0, (const BYTE*)"\\x41\\x83\\x0F\\x02", (const BYTE*)"\\x41\\x83\\x0F\\x00", 4, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchAltarFarRecord = {0, (const BYTE*)"\\x0F\\x44\\xD1\\x88\\x56\\x69", (const BYTE*)"\\xB2\\x04\\x90\\x88\\x56\\x69", 6, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchBuildRangeRecord = {0, (const BYTE*)"\\x41\\xBC\\x03\\x00\\x00\\x00", (const BYTE*)"\\x41\\xBC\\x20\\x00\\x00\\x00", 6, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchPlantGrowthRecord = {0, (const BYTE*)"\\xF3\\x44\\x0F\\x10\\x44\\x01\\x14", (const BYTE*)"\\x45\\x0F\\x57\\xC0\\x90\\x90\\x90", 7, {0}, FALSE, FALSE, FALSE};
ArchitectPatchRecord g_patchGliderRecord = {0, (const BYTE*)"\\xF3\\x41\\x0F\\x10\\x84\\x24\\xA4\\x04\\x00\\x00", (const BYTE*)"\\x0F\\x57\\xC0\\x90\\x90\\x90\\x90\\x90\\x90\\x90", 10, {0}, FALSE, FALSE, FALSE};

BOOL safe_patch_record(ArchitectPatchRecord* record, const char* name) {
    if (!record || !record->target) return FALSE;
    if (bytes_equal(record->target, record->patchBytes, record->length)) {
        record->installedByArchitect = TRUE;
        record->writeReadback = TRUE;
        record->revertAvailability = TRUE;
        return TRUE;
    }
    if (!bytes_equal(record->target, record->validatedOriginalBytes, record->length)) {
        return FALSE;
    }
    memcpy(record->savedOriginalBytes, record->target, record->length);
    DWORD oldProtect;
    if (VirtualProtect(record->target, record->length, PAGE_EXECUTE_READWRITE, &oldProtect)) {
        memcpy(record->target, record->patchBytes, record->length);
        VirtualProtect(record->target, record->length, oldProtect, &oldProtect);
        record->installedByArchitect = TRUE;
        record->writeReadback = bytes_equal(record->target, record->patchBytes, record->length);
        record->revertAvailability = TRUE;
        return record->writeReadback;
    }
    return FALSE;
}

BOOL safe_revert_record(ArchitectPatchRecord* record, const char* name) {
    if (!record || !record->target || !record->installedByArchitect) return FALSE;
    DWORD oldProtect;
    if (VirtualProtect(record->target, record->length, PAGE_EXECUTE_READWRITE, &oldProtect)) {
        memcpy(record->target, record->savedOriginalBytes, record->length);
        VirtualProtect(record->target, record->length, oldProtect, &oldProtect);
        record->installedByArchitect = FALSE;
        record->revertAvailability = FALSE;
        return TRUE;
    }
    return FALSE;
}
"""
src = src.replace("// External ASM entry points", records + "\n// External ASM entry points")

# Replace target initializations
src = src.replace("g_patchShroudTarget = g_imageBase + 0x27EA00;", "g_patchShroudRecord.target = g_imageBase + 0x27EA00;")
src = src.replace("g_patchDurabilityTarget = g_imageBase + 0x1F6DB0;", "g_patchDurabilityRecord.target = g_imageBase + 0x1F6DB0;")
src = src.replace("g_patchFallTarget = g_imageBase + 0x231F10;", "g_patchFallDamageRecord.target = g_imageBase + 0x231F10;")
src = src.replace("g_patchStealthTarget = g_imageBase + 0x302540;", "g_patchStealthModeRecord.target = g_imageBase + 0x302540;")
src = src.replace("g_patchOxygenTarget = g_imageBase + 0x27E6A0;", "g_patchOxygenRecord.target = g_imageBase + 0x27E6A0;")
src = src.replace("g_patchColdTarget = g_imageBase + 0x2344B2;", "g_patchColdRecord.target = g_imageBase + 0x2344B2;")
src = src.replace("g_patchParryTarget = g_imageBase + 0x269E71;", "g_patchParryRecord.target = g_imageBase + 0x269E71;")
src = src.replace("g_patchSkillResetTarget = g_imageBase + 0x1A472E;", "g_patchSkillResetRecord.target = g_imageBase + 0x1A472E;")
src = src.replace("g_patchAltarAreaTarget = g_imageBase + 0xCDAE13;", "g_patchAltarAreaRecord.target = g_imageBase + 0xCDAE13;")
src = src.replace("g_patchAltarFarTarget = g_imageBase + 0xCDAC55;", "g_patchAltarFarRecord.target = g_imageBase + 0xCDAC55;")
src = src.replace("g_patchBuildRangeTarget = g_imageBase + 0x61ED8F;", "g_patchBuildRangeRecord.target = g_imageBase + 0x61ED8F;")
src = src.replace("g_patchPlantGrowthTarget = g_imageBase + 0x5D783B;", "g_patchPlantGrowthRecord.target = g_imageBase + 0x5D783B;")
src = src.replace("g_patchGliderTarget = g_imageBase + 0x23315C;", "g_patchGliderRecord.target = g_imageBase + 0x23315C;")

# Replace toggles
def fix_toggle(src, func_name, record_name, bool_name, patch_name):
    # Regex find the toggle function block
    pattern = rf"(BOOL {func_name}\(void\) {{.*?return FALSE;\n    }}\n}})"
    replacement = f"""BOOL {func_name}(void) {{
    if (!{record_name}.target) return FALSE;
    if (!{bool_name}) {{
        if (safe_patch_record(&{record_name}, "{patch_name}")) {{
            {bool_name} = TRUE;
            return TRUE;
        }}
        return FALSE;
    }} else {{
        if (safe_revert_record(&{record_name}, "{patch_name}")) {{
            {bool_name} = FALSE;
            return TRUE;
        }}
        return FALSE;
    }}
}}"""
    return re.sub(pattern, replacement, src, flags=re.DOTALL)

src = fix_toggle(src, "cheat_toggle_shroud", "g_patchShroudRecord", "g_patchNoShroud", "shroud")
src = fix_toggle(src, "cheat_toggle_durability", "g_patchDurabilityRecord", "g_patchNoDurability", "durability")
src = fix_toggle(src, "cheat_toggle_falldamage", "g_patchFallDamageRecord", "g_patchNoFallDamage", "falldamage")
src = fix_toggle(src, "cheat_toggle_stealth", "g_patchStealthModeRecord", "g_patchStealthMode", "stealth")
src = fix_toggle(src, "cheat_toggle_oxygen", "g_patchOxygenRecord", "g_patchNoOxygen", "oxygen")
src = fix_toggle(src, "cheat_toggle_cold", "g_patchColdRecord", "g_patchNoCold", "cold")
src = fix_toggle(src, "cheat_toggle_parry", "g_patchParryRecord", "g_patchEasyParry", "parry")
src = fix_toggle(src, "cheat_toggle_skill_reset", "g_patchSkillResetRecord", "g_patchSkillReset", "skillreset")
src = fix_toggle(src, "cheat_toggle_altar_area", "g_patchAltarAreaRecord", "g_patchAltarArea", "altar_area")
src = fix_toggle(src, "cheat_toggle_altar_far", "g_patchAltarFarRecord", "g_patchAltarFar", "altar_far")
src = fix_toggle(src, "cheat_toggle_build_range", "g_patchBuildRangeRecord", "g_patchBuildRange", "build_range")
src = fix_toggle(src, "cheat_toggle_plant_growth", "g_patchPlantGrowthRecord", "g_patchPlantGrowth", "plant_growth")
src = fix_toggle(src, "cheat_toggle_glider_stamina", "g_patchGliderRecord", "g_patchGliderStamina", "glider_stamina")

# Replace get_state
def fix_readiness(src, field, record):
    pattern = rf"out->{field} = g_cc\.buildSupported && g_patch[a-zA-Z0-9_]+Target && \([^;]+;"
    replacement = f"out->{field} = g_cc.buildSupported && {record}.target && (bytes_equal({record}.target, {record}.validatedOriginalBytes, {record}.length) || ({record}.installedByArchitect && bytes_equal({record}.target, {record}.patchBytes, {record}.length)));"
    return re.sub(pattern, replacement, src)

src = fix_readiness(src, "patchShroudReady", "g_patchShroudRecord")
src = fix_readiness(src, "patchDurabilityReady", "g_patchDurabilityRecord")
src = fix_readiness(src, "patchFallDamageReady", "g_patchFallDamageRecord")
src = fix_readiness(src, "patchStealthReady", "g_patchStealthModeRecord")
src = fix_readiness(src, "patchOxygenReady", "g_patchOxygenRecord")
src = fix_readiness(src, "patchColdReady", "g_patchColdRecord")
src = fix_readiness(src, "patchParryReady", "g_patchParryRecord")
src = fix_readiness(src, "patchSkillResetReady", "g_patchSkillResetRecord")
src = fix_readiness(src, "patchAltarAreaReady", "g_patchAltarAreaRecord")
src = fix_readiness(src, "patchAltarFarReady", "g_patchAltarFarRecord")
src = fix_readiness(src, "patchBuildRangeReady", "g_patchBuildRangeRecord")
src = fix_readiness(src, "patchPlantGrowthReady", "g_patchPlantGrowthRecord")
src = fix_readiness(src, "patchGliderStaminaReady", "g_patchGliderRecord")

with open(r"runtime\native\source\CheatCorrelationHarness.c", "w") as f:
    f.write(src)
print("C Refactoring complete.")

