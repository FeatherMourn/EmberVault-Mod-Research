import re
with open('runtime/native/source/ArchitectPatchEngine.h', 'r') as f:
    h_code = f.read()

h_code = h_code.replace('int safe_revert_record(', 'int architect_patch_engine_bound(void);\nint safe_revert_record(')

with open('runtime/native/source/ArchitectPatchEngine.h', 'w') as f:
    f.write(h_code)
