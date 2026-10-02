import os
import subprocess

def run_test(flags):
    print(f"\n--- Testing with {flags} ---")
    vcvars = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
    cmd = f'"{vcvars}" && ml64.exe /nologo /c /Cx tests\\test_hook_transparency_asm.asm runtime\\native\\source\\ArchitectCheatCorrelationEntry.asm'
    subprocess.run(cmd, shell=True, capture_output=True)
    cmd = f'"{vcvars}" && cl.exe /nologo {flags} /W3 /Fe:tests\\test_hook_transparency.exe tests\\test_hook_transparency.c test_hook_transparency_asm.obj ArchitectCheatCorrelationEntry.obj'
    subprocess.run(cmd, shell=True, capture_output=True)
    res = subprocess.run([r"tests\test_hook_transparency.exe"], capture_output=True, text=True)
    if res.returncode == 0:
        print("PASS")
    else:
        print(f"FAIL (Return code {res.returncode})")
        print(res.stdout)

run_test("/Od")
run_test("/O2")
