import re
with open('build_scripts/run_all_tests.ps1', 'r') as f:
    code = f.read()

code = re.sub(r'Run-Suite "Direct Patch Integration" "cmd.exe /c .*?" ""\n', 'Run-Suite "Direct Patch Integration" "python tests\\\\build_and_run_integration.py" ""\n', code)

with open('build_scripts/run_all_tests.ps1', 'w') as f:
    f.write(code)
