import os
import subprocess
import sys

def main():
    print("Compiling Site A probe lifecycle test...")
    vcvars = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
    
    cmd = (
        f'"{vcvars}" && '
        'cl.exe /nologo /O2 /W3 /Fe:tests\\test_siteA_probe_lifecycle.exe '
        'tests\\test_siteA_probe_lifecycle.c kernel32.lib'
    )
    
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print("Compile failed:\nSTDOUT:\n", res.stdout, "\nSTDERR:\n", res.stderr)
        sys.exit(1)
        
    print("Running Site A probe lifecycle test...")
    res2 = subprocess.run([r"tests\test_siteA_probe_lifecycle.exe"], capture_output=True, text=True)
    print(res2.stdout)
    if res2.stderr:
        print(res2.stderr)
    sys.exit(res2.returncode)

if __name__ == "__main__":
    main()
