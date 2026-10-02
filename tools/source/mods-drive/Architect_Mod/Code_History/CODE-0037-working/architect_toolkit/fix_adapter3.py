import re
with open('runtime/native/source/ArchitectNativeRuntime.c', 'r') as f:
    code = f.read()

# I will replace static void* architect_patch_memcpy_adapter... with empty
code = re.sub(r'static void\* architect_patch_memcpy_adapter.*?return dest;\n}\n', '', code, flags=re.DOTALL)

adapter = """
static void* architect_patch_memcpy_adapter(void* dest, const void* src, size_t count) {
    if (count > 0xFFFFFFFFULL) return 0;
    mem_copy((BYTE*)dest, (const BYTE*)src, (DWORD)count);
    return dest;
}
"""
code = code.replace('static BOOL str_starts_with(', adapter + 'static BOOL str_starts_with(')

with open('runtime/native/source/ArchitectNativeRuntime.c', 'w') as f:
    f.write(code)
