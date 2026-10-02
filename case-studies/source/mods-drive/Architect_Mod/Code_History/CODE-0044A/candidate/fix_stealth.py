import re

with open('runtime/native/source/CheatCorrelationHarness.c', 'r') as f:
    code = f.read()

code = code.replace('out->patchStealthReady = g_cc.buildSupported &&', 'out->patchStealthReady = out->mutationBackendReady &&')

with open('runtime/native/source/CheatCorrelationHarness.c', 'w') as f:
    f.write(code)
