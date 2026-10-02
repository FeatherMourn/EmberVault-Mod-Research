import re

with open(r"runtime\native\source\CheatCorrelationHarness.c", "r") as f:
    src = f.read()

# Replace any remaining old Target assignments
src = re.sub(r"g_patchOxygenTarget(\s*=\s*g_imageBase\s*\+\s*0x[0-9A-Fa-f]+;)", r"g_patchOxygenRecord.target\1", src)
src = re.sub(r"g_patchColdTarget(\s*=\s*g_imageBase\s*\+\s*0x[0-9A-Fa-f]+;)", r"g_patchColdRecord.target\1", src)
src = re.sub(r"g_patchParryTarget(\s*=\s*g_imageBase\s*\+\s*0x[0-9A-Fa-f]+;)", r"g_patchParryRecord.target\1", src)
src = re.sub(r"g_patchSkillResetTarget(\s*=\s*g_imageBase\s*\+\s*0x[0-9A-Fa-f]+;)", r"g_patchSkillResetRecord.target\1", src)

src = re.sub(r"g_patchAltarAreaTarget(\s*=\s*g_imageBase\s*\+\s*0x[0-9A-Fa-f]+;)", r"g_patchAltarAreaRecord.target\1", src)
src = re.sub(r"g_patchAltarFarTarget(\s*=\s*g_imageBase\s*\+\s*0x[0-9A-Fa-f]+;)", r"g_patchAltarFarRecord.target\1", src)
src = re.sub(r"g_patchBuildRangeTarget(\s*=\s*g_imageBase\s*\+\s*0x[0-9A-Fa-f]+;)", r"g_patchBuildRangeRecord.target\1", src)
src = re.sub(r"g_patchPlantGrowthTarget(\s*=\s*g_imageBase\s*\+\s*0x[0-9A-Fa-f]+;)", r"g_patchPlantGrowthRecord.target\1", src)
src = re.sub(r"g_patchGliderTarget(\s*=\s*g_imageBase\s*\+\s*0x[0-9A-Fa-f]+;)", r"g_patchGliderRecord.target\1", src)

with open(r"runtime\native\source\CheatCorrelationHarness.c", "w") as f:
    f.write(src)
print("Offsets fixed.")
