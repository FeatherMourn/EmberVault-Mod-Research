import re

with open('runtime/native/source/CheatCorrelationHarness.c', 'r') as f:
    code = f.read()

code = code.replace('out->patchGliderReady', 'out->patchGliderStaminaReady')
code = code.replace('out->patchStealthModeReady', 'out->patchStealthReady')

with open('runtime/native/source/CheatCorrelationHarness.c', 'w') as f:
    f.write(code)
