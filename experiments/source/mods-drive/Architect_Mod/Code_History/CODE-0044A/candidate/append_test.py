with open('tests/test_command_routing.py', 'a') as f:
    f.write("\n\nworker_match = re.search(r'static DWORD __stdcall worker\\\\(LPVOID ignored\\\\) \\\\{.*?architect_bind_patch_engine_runtime\\\\(\\\\);\\\\s*cheat_correlation_initialize\\\\(', c, re.DOTALL)\n")
    f.write("if not worker_match:\n    print('FAIL: worker() does not call architect_bind_patch_engine_runtime() right before cheat_correlation_initialize()')\n    sys.exit(1)\n")
    f.write("print('[PASS] worker() structural binding order verified')\n")
