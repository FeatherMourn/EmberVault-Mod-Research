import subprocess
import hashlib
from pathlib import Path

ROOT = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\mods\architect_toolkit")
SRC = ROOT / "runtime" / "native" / "source"
NATIVE = ROOT / "runtime" / "native"
VCVARS = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

def build():
    commands = [
        f'call "{VCVARS}" >nul',
        f'cd /d "{SRC}"',
        'ml64 /nologo /c ArchitectBuildingPlaceEntry.asm',
        'ml64 /nologo /c ArchitectInventoryMoveProbeEntry.asm',
        'ml64 /nologo /c ArchitectInventoryMovePostProbeEntry.asm',
        'ml64 /nologo /c ArchitectInventoryTransferProbeEntry.asm',
        'ml64 /nologo /c ArchitectCheatCorrelationEntry.asm',
        'cl /nologo /c /O2 /GS- /Zl /W4 /TC /Fo"ArchitectNativeRuntime.obj" ArchitectNativeRuntime.c',
        'link /nologo /dll /machine:x64 /nodefaultlib /entry:DllMain /out:"..\\ArchitectNativeRuntime.dll" '
        'ArchitectNativeRuntime.obj ArchitectBuildingPlaceEntry.obj ArchitectInventoryMoveProbeEntry.obj '
        'ArchitectInventoryMovePostProbeEntry.obj ArchitectInventoryTransferProbeEntry.obj '
        'ArchitectCheatCorrelationEntry.obj kernel32.lib vcruntime.lib'
    ]
    full_cmd = " && ".join(commands)
    print("Running build...")
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    print("Return code:", res.returncode)
    if res.stdout:
        print("STDOUT:", res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    
    dll_path = NATIVE / "ArchitectNativeRuntime.dll"
    if dll_path.exists():
        h = hashlib.sha256(dll_path.read_bytes()).hexdigest()
        print(f"Built DLL SHA-256: {h}")
        sha_file = NATIVE / "SHA256.txt"
        sha_file.write_text(f"{h}  ArchitectNativeRuntime.dll\n", encoding="utf-8")
        print("Updated SHA256.txt")

if __name__ == "__main__":
    build()

