import re
with open('build_scripts/run_all_tests.ps1', 'r') as f:
    code = f.read()

if 'Direct Patch Integration' not in code:
    code = code.replace(
        'Run-Suite "Command Routing Independence" "python tests\\test_command_routing.py" ""\n',
        'Run-Suite "Command Routing Independence" "python tests\\test_command_routing.py" ""\nRun-Suite "Direct Patch Integration" "cmd.exe /c \\""C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat" && cl.exe /nologo /O2 /W3 /Fe:tests\\test_direct_patch_integration.exe tests\\test_direct_patch_integration.c && tests\\test_direct_patch_integration.exe\\" " ""\n'
    )
with open('build_scripts/run_all_tests.ps1', 'w') as f:
    f.write(code)
