import re
with open('tests/test_direct_patch_integration.c', 'r') as f:
    code = f.read()

code = code.replace(
    'parse_cheat_correlation_command((DWORD)strlen(cmd));\n    \n    cheat_correlation_get_state(&state);',
    'parse_cheat_correlation_command((DWORD)strlen(cmd));\n    printf("Failure reason: %s\\n", g_lastCommandFailureReason);\n    cheat_correlation_get_state(&state);'
)
with open('tests/test_direct_patch_integration.c', 'w') as f:
    f.write(code)
