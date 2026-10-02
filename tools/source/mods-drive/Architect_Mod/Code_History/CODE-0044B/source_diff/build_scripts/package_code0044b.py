"""Create the two CODE-0044B archives after offline qualification.

Run from the reconstructed CODE-0044A-based working tree. Does not mutate Current.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(r"I:\My Drive\Enshrouded Mods\Architect_Mod\Code_History\CODE-0044B")
CANDIDATE = OUT / "architect_toolkit_CODE-0044B_candidate_20260921.zip"
INTEGRATED = OUT / "architect_toolkit_CODE-0044B_BUILD_FEATURE_PACK1_TEST_20260921.zip"
SOURCE_DIRS = ("blueprints", "build_scripts", "data", "docs", "runtime", "src", "tests", "tools")
INSTALL_DIRS = ("blueprints", "runtime", "src")
EXCLUDED_PARTS = {"__pycache__", "bridge", "staging", "incoming"}
EXCLUDED_SUFFIXES = {".obj", ".exp", ".lib", ".exe", ".pyc", ".pdb", ".tmp", ".log", ".zip"}
EXCLUDED_NAMES = {"ui_errors.log", "last_crash.txt", "ui_bounds.json"}


def selected(directories: tuple[str, ...]) -> list[Path]:
    files = [ROOT / "mod.json"]
    for directory in directories:
        base = ROOT / directory
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if any(part.lower() in EXCLUDED_PARTS for part in relative.parts):
                continue
            if path.suffix.lower() in EXCLUDED_SUFFIXES or path.name.lower() in EXCLUDED_NAMES:
                continue
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def add_files(archive: zipfile.ZipFile, files: list[Path], prefix: str = "") -> None:
    for path in files:
        archive.write(path, prefix + path.relative_to(ROOT).as_posix())


def checked_archive(path: Path) -> tuple[int, int]:
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"CRC failure in {path}: {bad}")
        names = set(archive.namelist())
        if not any(name.endswith("runtime/ArchitectRuntime.ps1") for name in names):
            raise RuntimeError("Runtime source is absent from package")
        if not any(name.endswith("runtime/ArchitectBuildDesign.psm1") for name in names):
            raise RuntimeError("Procedural geometry engine is absent from package")
        if not any(name.endswith("runtime/cheat_table_1013216_catalog.json") for name in names):
            raise RuntimeError("CT catalog is absent from package")
        return len(names), path.stat().st_size


def main() -> None:
    if not OUT.is_dir() or CANDIDATE.exists() or INTEGRATED.exists():
        raise RuntimeError("Output directory missing or final archive already exists; refusing overwrite")
    candidate_files = selected(SOURCE_DIRS)
    install_files = selected(INSTALL_DIRS)
    if not all(path.is_file() for path in candidate_files + install_files):
        raise RuntimeError("A required package input is missing")
    readme = (
        "CODE-0044B integrated BUILD feature pack; offline qualified only.\r\n"
        "Install mods/architect_toolkit as a single folder in a disposable/test game setup.\r\n"
        "Do not infer live carrier switching, world placement, game ghost, or native mutation.\r\n"
        "Generated designs are local data. Exact catalog matches only stage the next restart.\r\n"
        "Do not promote Architect_Mod/Current without a later integration decision.\r\n"
    )
    with tempfile.TemporaryDirectory(prefix="code0044b-package-", dir=OUT) as temp:
        tempdir = Path(temp)
        candidate_tmp = tempdir / CANDIDATE.name
        integrated_tmp = tempdir / INTEGRATED.name
        with zipfile.ZipFile(candidate_tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
            add_files(archive, candidate_files)
        with zipfile.ZipFile(integrated_tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
            archive.writestr("README_CODE0044B_RUNTIME_TEST.txt", readme)
            add_files(archive, install_files, "mods/architect_toolkit/")
        candidate_count, candidate_bytes = checked_archive(candidate_tmp)
        integrated_count, integrated_bytes = checked_archive(integrated_tmp)
        os.rename(candidate_tmp, CANDIDATE)
        os.rename(integrated_tmp, INTEGRATED)
    for name, path, count, size in (
        ("candidate", CANDIDATE, candidate_count, candidate_bytes),
        ("integrated", INTEGRATED, integrated_count, integrated_bytes),
    ):
        print(f"{name} files={count} bytes={size} sha256={digest(path)} path={path}")


if __name__ == "__main__":
    main()
