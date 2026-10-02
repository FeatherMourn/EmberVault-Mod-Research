"""Run an isolated install/upgrade/uninstall smoke test for a Windows installer."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run_installer(installer: Path, root: Path) -> int:
    return subprocess.run([
        str(installer), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/NOICONS",
        f"/DIR={root}",
    ], check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installer", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-portable", type=Path, help="require the installed executable to match this exact build")
    args = parser.parse_args()
    installer = args.installer.resolve()
    result = {
        "schema": "control_center.installer_smoke.v1",
        "installer": str(installer),
        "valid": False,
        "isolated": True,
    }
    if not installer.is_file():
        result["error"] = "installer does not exist"
    else:
        with tempfile.TemporaryDirectory(prefix="control-center-installer-") as raw:
            root = Path(raw) / "install"
            root.mkdir()
            first = run_installer(installer, root)
            installed_exe = root / "EnshroudedModHub.exe"
            installed_hash = hashlib.sha256(installed_exe.read_bytes()).hexdigest() if installed_exe.is_file() else None
            expected_hash = hashlib.sha256(args.expected_portable.read_bytes()).hexdigest() if args.expected_portable else None
            payload_matches = installed_hash == expected_hash if args.expected_portable else installed_hash is not None
            files_after_install = sorted(
                str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()
            )
            user_file = root / "profiles" / "user-profile.json"
            user_file.parent.mkdir(parents=True, exist_ok=True)
            user_file.write_text('{"preserve": true}\n', encoding="utf-8")
            upgrade = run_installer(installer, root)
            preserved_after_upgrade = user_file.is_file() and user_file.read_text(encoding="utf-8") == '{"preserve": true}\n'
            uninstallers = sorted(root.glob("unins*.exe"))
            uninstall = None
            if uninstallers:
                uninstall = subprocess.run([
                    str(uninstallers[0]), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"
                ], check=False).returncode
            result.update({
                "install_exit": first,
                "installed_executable_sha256": installed_hash,
                "expected_executable_sha256": expected_hash,
                "payload_matches": payload_matches,
                "upgrade_exit": upgrade,
                "files_after_install": files_after_install,
                "preserved_after_upgrade": preserved_after_upgrade,
                "uninstall_exit": uninstall,
                "user_file_after_uninstall": user_file.is_file(),
                "remaining_files": sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()),
            })
            remaining = [path for path in root.rglob("*") if path.is_file()]
            allowed_after_uninstall = {user_file.resolve(), uninstallers[0].resolve()} if uninstallers else {user_file.resolve()}
            result["valid"] = (
                first == 0 and payload_matches and upgrade == 0 and preserved_after_upgrade and
                uninstall == 0 and user_file.is_file() and
                all(path.resolve() in allowed_after_uninstall for path in remaining)
            )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if args.output:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, output)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
