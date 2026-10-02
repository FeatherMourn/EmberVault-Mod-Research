import re
with open('runtime/native/source/ArchitectNativeRuntime.c', 'r') as f:
    code = f.read()

code = code.replace('static char g_lastProcessedCommandId[64] = "";', 'static char g_lastProcessedCommandId[64] = "";\nstatic char g_lastCommandFailureReason[128] = "";')
with open('runtime/native/source/ArchitectNativeRuntime.c', 'w') as f:
    f.write(code)
