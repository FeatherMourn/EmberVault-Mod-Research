from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    manifests = sorted(ROOT.glob("*/manifest.json"))
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                           cwd=ROOT, capture_output=True, text=True)
    compile_run = subprocess.run([sys.executable, "-m", "compileall", "-q", "."],
                                 cwd=ROOT, capture_output=True, text=True)
    native_run = subprocess.run(
        ["cargo", "build", "--manifest-path", "native_bridge_probe/Cargo.toml",
         "--target", "x86_64-pc-windows-msvc", "--release"],
        cwd=ROOT, capture_output=True, text=True,
    )
    wheel = ROOT / "dist" / "emberworks_mods-0.1.0-py3-none-any.whl"
    wheel_install = None
    wheel_import = None
    if wheel.exists():
        with tempfile.TemporaryDirectory(prefix="emberworks-wheel-verify-") as target:
            wheel_install = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--target", target,
                 "--no-deps", "--disable-pip-version-check", str(wheel)],
                cwd=ROOT, capture_output=True, text=True,
            )
            env = dict(__import__("os").environ)
            env["PYTHONPATH"] = target
            wheel_import = subprocess.run(
                [sys.executable, "-c", "import construction_sdk, blueprint_library, worldwright, zooping, builders_wand, chiselcraft, framed_architecture, restoration, kinetic_works"],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
    packages = {}
    for path in manifests:
        data = json.loads(path.read_text(encoding="utf-8"))
        packages[data["id"]] = {
            "version": data["version"],
            "runtime_status": data.get("runtime_status", "unknown"),
            "capabilities": data.get("capabilities", []),
        }
    report = {
        "tests_passed": tests.returncode == 0,
        "tests_exit_code": tests.returncode,
        "compile_passed": compile_run.returncode == 0,
        "compile_exit_code": compile_run.returncode,
        "native_bridge_build_passed": native_run.returncode == 0,
        "native_bridge_build_exit_code": native_run.returncode,
        "wheel_import_passed": bool(wheel_install and wheel_import and wheel_install.returncode == 0 and wheel_import.returncode == 0),
        "manifest_count": len(manifests),
        "packages": packages,
        "control_center_modified": False,
        "runtime_verified": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if tests.returncode:
        print(tests.stdout, file=sys.stderr)
        print(tests.stderr, file=sys.stderr)
    if compile_run.returncode:
        print(compile_run.stdout, file=sys.stderr)
        print(compile_run.stderr, file=sys.stderr)
    return 0 if (tests.returncode == 0 and compile_run.returncode == 0 and
                  native_run.returncode == 0 and report["wheel_import_passed"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
