import re
with open('runtime/native/source/ArchitectPatchEngine.c', 'r') as f:
    c_code = f.read()

binder = """
int architect_patch_engine_bound(void) {
    return (g_arch_VirtualProtect != 0 && g_arch_memcpy != 0 && g_arch_FlushInstructionCache != 0) ? 1 : 0;
}
"""

c_code = c_code.replace('int safe_patch_record(', binder + '\nint safe_patch_record(')
c_code = c_code.replace('int safe_patch_record(ArchitectPatchRecord* record, const char* name) {\n', 
                        'int safe_patch_record(ArchitectPatchRecord* record, const char* name) {\n    if (!architect_patch_engine_bound()) return 0;\n')

with open('runtime/native/source/ArchitectPatchEngine.c', 'w') as f:
    f.write(c_code)
