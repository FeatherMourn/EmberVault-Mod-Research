import re

with open('runtime/native/source/CheatCorrelationHarness.c', 'r') as f:
    code = f.read()

patches = ["Shroud", "Durability", "FallDamage", "StealthMode", "Oxygen", "Cold", "Parry", "SkillReset", "AltarArea", "AltarFar", "BuildRange", "PlantGrowth", "Glider"]
for p in patches:
    code = re.sub(r'out->patch' + p + r'(Stamina)?Ready = g_cc\.buildSupported &&', 'out->patch' + p + r'\\1Ready = out->mutationBackendReady &&', code)

with open('runtime/native/source/CheatCorrelationHarness.c', 'w') as f:
    f.write(code)
