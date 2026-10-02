import subprocess
import sys
from pathlib import Path

SCRATCH = Path(r"C:\Users\JoelT\.gemini\antigravity\brain\d23b16db-84cd-4213-bad4-65a0e40e0fab\scratch")
SRC = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\mods\architect_toolkit\runtime\native\source")
VCVARS = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

def main():
    commands = [
        f'call "{VCVARS}" >nul',
        f'cd /d "{SCRATCH}"',
        f'ml64 /nologo /c "{SRC}\\ArchitectCheatCorrelationEntry.asm"',
        'ml64 /nologo /c test_hook_transparency_asm.asm',
        'cl /nologo /O2 /W4 test_hook_transparency.c test_hook_transparency_asm.obj ArchitectCheatCorrelationEntry.obj /link kernel32.lib',
        'test_hook_transparency.exe'
    ]
    full_cmd = " && ".join(commands)
    print("Building and executing transparency test harness...")
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    print("Process return code:", res.returncode)
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
