import re

with open('runtime/native/source/ArchitectNativeRuntime.c', 'r') as f:
    code = f.read()

# Remove all definitions of architect_patch_memcpy_adapter
code = re.sub(r'static void\* architect_patch_memcpy_adapter\(void\* dest, const void\* src, size_t count\) \{\n    if \(count > 0xFFFFFFFFULL\) return 0;\n    mem_copy\(\(BYTE\*\)dest, \(const BYTE\*\)src, \(DWORD\)count\);\n    return dest;\n\}\n', '', code)

# Insert it exactly after mem_copy implementation ends
adapter = """
static void* architect_patch_memcpy_adapter(void* dest, const void* src, size_t count) {
    if (count > 0xFFFFFFFFULL) return 0;
    mem_copy((BYTE*)dest, (const BYTE*)src, (DWORD)count);
    return dest;
}
"""

code = code.replace("for (i = 0; i < n; i++) dst[i] = src[i];\n}", "for (i = 0; i < n; i++) dst[i] = src[i];\n}\n" + adapter)

with open('runtime/native/source/ArchitectNativeRuntime.c', 'w') as f:
    f.write(code)
