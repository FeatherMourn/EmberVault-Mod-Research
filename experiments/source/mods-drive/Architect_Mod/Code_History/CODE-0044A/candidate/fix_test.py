import re

with open('tests/test_command_routing.py', 'r') as f:
    lines = f.readlines()

# find where "worker_match" starts and remove it
new_lines = []
for line in lines:
    if "worker_match" in line:
        break
    new_lines.append(line)

with open('tests/test_command_routing.py', 'w') as f:
    f.writelines(new_lines)
    f.write("\n")
    f.write("worker_match = re.search(r'static DWORD __stdcall worker\\\\(LPVOID ignored\\\\) \\\\{.*?architect_bind_patch_engine_runtime\\\\(\\\\);\\\\s*cheat_correlation_initialize\\\\(', c, re.DOTALL)\n")
    f.write("if not worker_match:\n    print('FAIL: worker() does not call architect_bind_patch_engine_runtime() right before cheat_correlation_initialize()')\n    import sys\n    sys.exit(1)\n")
    f.write("print('[PASS] worker() structural binding order verified')\n")
