import re
with open('tests/test_direct_patch_integration.c', 'r') as f:
    code = f.read()

code = code.replace('parse_cheat_correlation_command((DWORD)strlen(cmd));', 'parse_cheat_correlation_command((DWORD)strlen(cmd1));', 1)
code = code.replace('parse_cheat_correlation_command((DWORD)strlen(cmd));', 'parse_cheat_correlation_command((DWORD)strlen(cmd2));', 1)
code = code.replace('parse_cheat_correlation_command((DWORD)strlen(cmd));', 'parse_cheat_correlation_command((DWORD)strlen(cmd3));', 1)

with open('tests/test_direct_patch_integration.c', 'w') as f:
    f.write(code)
