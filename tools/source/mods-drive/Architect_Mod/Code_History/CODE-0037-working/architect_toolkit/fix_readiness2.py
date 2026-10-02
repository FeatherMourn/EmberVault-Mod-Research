import re

with open('runtime/native/source/CheatCorrelationHarness.c', 'r') as f:
    code = f.read()

code = re.sub(r'out->patch([A-Za-z]+)\\1Ready', r'out->patch\1Ready', code)

with open('runtime/native/source/CheatCorrelationHarness.c', 'w') as f:
    f.write(code)
