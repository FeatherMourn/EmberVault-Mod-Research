import os
import subprocess
import sys

vcvars = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
compile_cmd = f'"{vcvars}" && cl.exe /nologo /O2 /W3 /Fe:tests\\test_direct_patch_integration.exe tests\\test_direct_patch_integration.c'

res = subprocess.run(compile_cmd, shell=True)
if res.returncode != 0:
    print("Compile failed")
    sys.exit(1)

res2 = subprocess.run("tests\\test_direct_patch_integration.exe", shell=True)
if res2.returncode != 0:
    print("Test failed")
    sys.exit(1)

sys.exit(0)
