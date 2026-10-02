import re
with open('runtime/native/source/ArchitectNativeRuntime.c', 'r') as f:
    code = f.read()

# Fix broken newlines
code = re.sub(r'rejected: (.*?)\.\n\n";', r'rejected: \1.\\r\\n";', code)
with open('runtime/native/source/ArchitectNativeRuntime.c', 'w') as f:
    f.write(code)
