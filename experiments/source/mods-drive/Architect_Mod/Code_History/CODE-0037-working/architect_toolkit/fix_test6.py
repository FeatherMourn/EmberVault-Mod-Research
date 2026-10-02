import re
with open('tests/test_direct_patch_integration.c', 'r') as f:
    code = f.read()

# Fix assertions
code = code.replace(
    'ASSERT(memcmp(dummyTarget, "\\xF3\\x41\\x0F\\x10\\x84\\x24\\xA4\\x04\\x00\\x00", 10) == 0, "target == exact patch bytes");',
    'ASSERT(memcmp(dummyTarget, "\\x0F\\x57\\xC0\\x90\\x90\\x90\\x90\\x90\\x90\\x90", 10) == 0, "target == exact patch bytes");'
)

code = code.replace(
    'ASSERT(memcmp(dummyTarget, "\\x0F\\x57\\xC0\\x90\\x90\\x90\\x90\\x90\\x90\\x90", 10) == 0, "original bytes restored exactly");',
    'ASSERT(memcmp(dummyTarget, "\\xF3\\x41\\x0F\\x10\\x84\\x24\\xA4\\x04\\x00\\x00", 10) == 0, "original bytes restored exactly");'
)

with open('tests/test_direct_patch_integration.c', 'w') as f:
    f.write(code)
