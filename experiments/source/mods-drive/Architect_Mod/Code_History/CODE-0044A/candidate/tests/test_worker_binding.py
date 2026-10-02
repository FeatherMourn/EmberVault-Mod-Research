import re
import sys

with open('runtime/native/source/ArchitectNativeRuntime.c', 'r') as f:
    c = f.read()

# 4. verify worker() calls architect_bind_patch_engine_runtime() before cheat_correlation_initialize()
worker_match = re.search(r'static DWORD __stdcall worker\(LPVOID ignored\) \{.*?architect_bind_patch_engine_runtime\(\);\s*cheat_correlation_initialize\(', c, re.DOTALL)
if not worker_match:
    print("FAIL: worker() does not call architect_bind_patch_engine_runtime() right before cheat_correlation_initialize()")
    sys.exit(1)
print("[PASS] worker() structural binding order verified")

sys.exit(0)
