import re

with open('runtime/native/source/ArchitectNativeRuntime.c', 'r') as f:
    code = f.read()

replacement = (
    'p = append_ascii(g_cheatCorrelationJson, p, sizeof(g_cheatCorrelationJson), ",\\r\\n  \\"lastCommandFailureReason\\": ");\n'
    '    p = append_json_string(g_cheatCorrelationJson, p, sizeof(g_cheatCorrelationJson), g_lastCommandFailureReason);\n'
    '    p = append_ascii(g_cheatCorrelationJson, p, sizeof(g_cheatCorrelationJson), ",\\r\\n  \\"lastCommandVerified\\": ");'
)

code = code.replace('p = append_ascii(g_cheatCorrelationJson, p, sizeof(g_cheatCorrelationJson), ",\\r\\n  \\"lastCommandVerified\\": ");', replacement)

with open('runtime/native/source/ArchitectNativeRuntime.c', 'w') as f:
    f.write(code)
