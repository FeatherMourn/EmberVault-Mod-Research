import os
import subprocess

def main():
    print("Compiling patch engine test...")
    vcvars = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
    
    cmd = f'"{vcvars}" && cl.exe /nologo /O2 /W3 /Fe:tests\\test_patch_engine.exe tests\\test_patch_engine.c runtime\\native\\source\\ArchitectPatchEngine.c'
    
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print("Compile failed:", res.stdout, res.stderr)
        exit(1)
        
    print("Running test...")
    res2 = subprocess.run([r"tests\test_patch_engine.exe"], capture_output=True, text=True)
    print(res2.stdout)
    if res2.stderr:
        print(res2.stderr)
    exit(res2.returncode)

if __name__ == "__main__":
    main()

