import re
with open('tests/test_direct_patch_integration.c', 'r') as f:
    code = f.read()

code = code.replace(
    'const char* cmd = "{\\"action\\":\\"cheat.world.glider_stamina\\",\\"commandId\\":\\"cmd_123\\"}";',
    'const char* cmd1 = "{\\"action\\":\\"cheat.world.glider_stamina\\",\\"commandId\\":\\"cmd_123\\"}";\n    const char* cmd2 = "{\\"action\\":\\"cheat.world.glider_stamina\\",\\"commandId\\":\\"cmd_124\\"}";\n    const char* cmd3 = "{\\"action\\":\\"cheat.world.glider_stamina\\",\\"commandId\\":\\"cmd_125\\"}";'
)
code = code.replace('strcpy(g_cheatCorrelationCommand, cmd);', 'strcpy(g_cheatCorrelationCommand, cmd1);', 1)
code = code.replace('strcpy(g_cheatCorrelationCommand, cmd);', 'strcpy(g_cheatCorrelationCommand, cmd2);', 1)
code = code.replace('strcpy(g_cheatCorrelationCommand, cmd);', 'strcpy(g_cheatCorrelationCommand, cmd3);', 1)

with open('tests/test_direct_patch_integration.c', 'w') as f:
    f.write(code)
