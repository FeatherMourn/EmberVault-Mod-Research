import subprocess
import hashlib
from pathlib import Path

import json

ROOT = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\mods\architect_toolkit")
SRC = ROOT / "runtime" / "native" / "source"
NATIVE = ROOT / "runtime" / "native"
VCVARS = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

def sync_build_identity():
    identity_file = ROOT / "runtime" / "build_identity.json"
    if identity_file.exists():
        data = json.loads(identity_file.read_text(encoding="utf-8"))
        header_file = SRC / "ArchitectBuildIdentity.h"
        header_text = f"""#ifndef ARCHITECT_BUILD_IDENTITY_H
#define ARCHITECT_BUILD_IDENTITY_H

/* Authoritative Build Identity Definition - Synced with runtime/build_identity.json */
#define ARCHITECT_RUNTIME_VERSION "{data['version']}"
#define ARCHITECT_RUNTIME_BUILD_ID "{data['buildId']}"
#define ARCHITECT_RUNTIME_MODE "{data['mode']}"

#endif /* ARCHITECT_BUILD_IDENTITY_H */
"""
        header_file.write_text(header_text, encoding="utf-8")
        print(f"Synchronized ArchitectBuildIdentity.h: version={data['version']} buildId={data['buildId']} mode={data['mode']}")

def build():
    sync_build_identity()
    commands = [
        f'call "{VCVARS}" >nul',
        f'cd /d "{SRC}"',
        'ml64 /nologo /c ArchitectBuildingPlaceEntry.asm',
        'ml64 /nologo /c ArchitectInventoryMoveProbeEntry.asm',
        'ml64 /nologo /c ArchitectInventoryMovePostProbeEntry.asm',
        'ml64 /nologo /c ArchitectInventoryTransferProbeEntry.asm',
        'ml64 /nologo /c ArchitectCheatCorrelationEntry.asm',
        'ml64 /nologo /c ArchitectSiteAProbeEntry.asm',
        'cl /nologo /c /O2 /GS- /Zl /W4 /TC /Fo"ArchitectNativeRuntime.obj" ArchitectNativeRuntime.c',
        'link /nologo /dll /machine:x64 /nodefaultlib /entry:DllMain /out:"..\\ArchitectNativeRuntime.dll" '
        'ArchitectNativeRuntime.obj ArchitectBuildingPlaceEntry.obj ArchitectInventoryMoveProbeEntry.obj '
        'ArchitectInventoryMovePostProbeEntry.obj ArchitectInventoryTransferProbeEntry.obj '
        'ArchitectCheatCorrelationEntry.obj ArchitectSiteAProbeEntry.obj kernel32.lib vcruntime.lib'
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

