import re
with open('runtime/native/source/ArchitectNativeRuntime.c', 'r') as f:
    code = f.read()

adapter = """
static void* architect_patch_memcpy_adapter(void* dest, const void* src, size_t count) {
    if (count > 0xFFFFFFFFULL) return 0;
    mem_copy((BYTE*)dest, (const BYTE*)src, (DWORD)count);
    return dest;
}
"""

if "architect_patch_memcpy_adapter" not in code:
    code = code.replace("static BOOL ascii_equal", adapter + "static BOOL ascii_equal")

with open('runtime/native/source/ArchitectNativeRuntime.c', 'w') as f:
    f.write(code)
