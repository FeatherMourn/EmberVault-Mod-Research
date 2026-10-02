import re
with open('runtime/native/source/CheatCorrelationHarness.h', 'r') as f:
    code = f.read()
code = code.replace('extern ArchitectPatchRecord g_patchGliderStaminaRecord;', 'extern ArchitectPatchRecord g_patchGliderRecord;')
with open('runtime/native/source/CheatCorrelationHarness.h', 'w') as f:
    f.write(code)
