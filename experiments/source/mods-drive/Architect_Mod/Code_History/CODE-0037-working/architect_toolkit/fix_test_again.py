import re

with open('tests/test_command_routing.py', 'r') as f:
    code = f.read()

code = code.replace(
    r"r'static DWORD __stdcall worker\\\\(LPVOID ignored\\\\) \\\\{.*?architect_bind_patch_engine_runtime\\\\(\\\\);\\\\s*cheat_correlation_initialize\\\\('",
    r"r'static DWORD __stdcall worker\(LPVOID ignored\) \{.*?architect_bind_patch_engine_runtime\(\);\s*cheat_correlation_initialize\('"
)

with open('tests/test_command_routing.py', 'w') as f:
    f.write(code)
