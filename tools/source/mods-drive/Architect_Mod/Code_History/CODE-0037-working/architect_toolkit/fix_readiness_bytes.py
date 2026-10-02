import os
import re

c_file = r"runtime\native\source\CheatCorrelationHarness.c"
with open(c_file, "r") as f:
    text = f.read()

new_readiness = r"""
        out->patchShroudReady = g_cc.buildSupported && g_patchShroudTarget && (bytes_equal(g_patchShroudTarget, (const BYTE*)"\x40\x55\x41\x54\x41\x55", 6) || (g_patchNoShroud && bytes_equal(g_patchShroudTarget, (const BYTE*)"\xC3\x55\x41\x54\x41\x55", 6)));
        out->patchDurabilityReady = g_cc.buildSupported && g_patchDurabilityTarget && (bytes_equal(g_patchDurabilityTarget, (const BYTE*)"\x40\x55\x41\x55\x48\x8D", 6) || (g_patchNoDurability && bytes_equal(g_patchDurabilityTarget, (const BYTE*)"\xC3\x55\x41\x55\x48\x8D", 6)));
        out->patchFallDamageReady = g_cc.buildSupported && g_patchFallTarget && (bytes_equal(g_patchFallTarget, (const BYTE*)"\x40\x53\x48\x83\xEC\x60", 6) || (g_patchNoFallDamage && bytes_equal(g_patchFallTarget, (const BYTE*)"\xC3\x53\x48\x83\xEC\x60", 6)));
        out->patchStealthReady = g_cc.buildSupported && g_patchStealthTarget && (bytes_equal(g_patchStealthTarget, (const BYTE*)"\x48\x89\x4C\x24\x08\x55", 6) || (g_patchStealthMode && bytes_equal(g_patchStealthTarget, (const BYTE*)"\xC3\x89\x4C\x24\x08\x55", 6)));
        out->patchOxygenReady = g_cc.buildSupported && g_patchOxygenTarget && (bytes_equal(g_patchOxygenTarget, (const BYTE*)"\x40\x55\x41\x55\x41\x56", 6) || (g_patchNoOxygen && bytes_equal(g_patchOxygenTarget, (const BYTE*)"\xC3\x55\x41\x55\x41\x56", 6)));
        out->patchColdReady = g_cc.buildSupported && g_patchColdTarget && (bytes_equal(g_patchColdTarget, (const BYTE*)"\x40\x55\x56\x48\x8D\x6C", 6) || (g_patchNoCold && bytes_equal(g_patchColdTarget, (const BYTE*)"\xC3\x55\x56\x48\x8D\x6C", 6)));
        out->patchParryReady = g_cc.buildSupported && g_patchParryTarget && (bytes_equal(g_patchParryTarget, (const BYTE*)"\x74\x78", 2) || (g_patchEasyParry && bytes_equal(g_patchParryTarget, (const BYTE*)"\x90\x90", 2)));
        out->patchSkillResetReady = g_cc.buildSupported && g_patchSkillResetTarget && (bytes_equal(g_patchSkillResetTarget, (const BYTE*)"\x48\x89\x6C", 3) || (g_patchSkillReset && bytes_equal(g_patchSkillResetTarget, (const BYTE*)"\x31\xC0\xC3", 3)));
        out->patchAltarAreaReady = g_cc.buildSupported && g_patchAltarAreaTarget && (bytes_equal(g_patchAltarAreaTarget, (const BYTE*)"\x41\x83\x0F\x02", 4) || (g_patchAltarArea && bytes_equal(g_patchAltarAreaTarget, (const BYTE*)"\x41\x83\x0F\x00", 4)));
        out->patchAltarFarReady = g_cc.buildSupported && g_patchAltarFarTarget && (bytes_equal(g_patchAltarFarTarget, (const BYTE*)"\x0F\x44\xD1\x88\x56\x69", 6) || (g_patchAltarFar && bytes_equal(g_patchAltarFarTarget, (const BYTE*)"\xB2\x04\x90\x88\x56\x69", 6)));
        out->patchBuildRangeReady = g_cc.buildSupported && g_patchBuildRangeTarget && (bytes_equal(g_patchBuildRangeTarget, (const BYTE*)"\x41\xBC\x03\x00\x00\x00", 6) || (g_patchBuildRange && bytes_equal(g_patchBuildRangeTarget, (const BYTE*)"\x41\xBC\x20\x00\x00\x00", 6)));
        out->patchPlantGrowthReady = g_cc.buildSupported && g_patchPlantGrowthTarget && (bytes_equal(g_patchPlantGrowthTarget, (const BYTE*)"\xF3\x44\x0F\x10\x44\x01\x14", 7) || (g_patchPlantGrowth && bytes_equal(g_patchPlantGrowthTarget, (const BYTE*)"\x45\x0F\x57\xC0\x90\x90\x90", 7)));
        out->patchGliderStaminaReady = g_cc.buildSupported && g_patchGliderTarget && (bytes_equal(g_patchGliderTarget, (const BYTE*)"\xF3\x41\x0F\x10\x84\x24\xA4\x04\x00\x00", 10) || (g_patchGliderStamina && bytes_equal(g_patchGliderTarget, (const BYTE*)"\x0F\x57\xC0\x90\x90\x90\x90\x90\x90\x90", 10)));
"""

text = re.sub(r"out->patchShroudReady = g_cc\.buildSupported && g_patchShroudTarget.*?;.*out->patchGliderStaminaReady = [^\n]+;", lambda m: new_readiness.strip(), text, flags=re.DOTALL)

with open(c_file, "w") as f:
    f.write(text)
