import re

with open('runtime/native/source/ArchitectNativeRuntime.c', 'r') as f:
    code = f.read()

# Remove old adapter if any
code = re.sub(r'static void\* architect_patch_memcpy_adapter.*?return dest;\n}\n', '', code, flags=re.DOTALL)

adapter_and_binder = """
static void* architect_patch_memcpy_adapter(void* dest, const void* src, size_t count) {
    if (count > 0xFFFFFFFFULL) return 0;
    mem_copy((BYTE*)dest, (const BYTE*)src, (DWORD)count);
    return dest;
}

BOOL architect_bind_patch_engine_runtime(void) {
    g_arch_VirtualProtect = (int (*)(void*, size_t, unsigned long, unsigned long*))VirtualProtect;
    g_arch_memcpy = architect_patch_memcpy_adapter;
    g_arch_FlushInstructionCache = (int (*)(void*, const void*, size_t))FlushInstructionCache;
    return architect_patch_engine_bound() ? TRUE : FALSE;
}
"""

# Insert right after mem_copy
code = code.replace("for (i = 0; i < n; i++) dst[i] = src[i];\n}", "for (i = 0; i < n; i++) dst[i] = src[i];\n}\n" + adapter_and_binder)

# Inject into worker() before cheat_correlation_initialize
if 'architect_bind_patch_engine_runtime();' not in code:
    code = code.replace('cheat_correlation_initialize(', 'architect_bind_patch_engine_runtime();\n    cheat_correlation_initialize(')

with open('runtime/native/source/ArchitectNativeRuntime.c', 'w') as f:
    f.write(code)
