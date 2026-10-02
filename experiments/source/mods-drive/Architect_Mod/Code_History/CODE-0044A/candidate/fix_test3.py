import re
with open('tests/test_direct_patch_integration.c', 'r') as f:
    code = f.read()

code = code.replace(
    'cheat_correlation_get_state(&state);\n    ASSERT(state.patchGliderStaminaReady == TRUE, "patchReady == TRUE before dispatch");',
    'cheat_correlation_get_state(&state);\n    printf("Engine bound: %d\\n", architect_patch_engine_bound());\n    ASSERT(state.patchGliderStaminaReady == TRUE, "patchReady == TRUE before dispatch");'
)
with open('tests/test_direct_patch_integration.c', 'w') as f:
    f.write(code)
