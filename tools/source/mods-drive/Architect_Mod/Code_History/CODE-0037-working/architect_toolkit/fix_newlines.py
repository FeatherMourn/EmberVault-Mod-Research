import re

with open('runtime/native/source/ArchitectNativeRuntime.c', 'r') as f:
    anr_code = f.read()

# Fix the newlines inside string literals
anr_code = re.sub(r'rejected: (.*?)\.\n";', r'rejected: \1.\\r\\n";', anr_code)

with open('runtime/native/source/ArchitectNativeRuntime.c', 'w') as f:
    f.write(anr_code)
