from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent


def package_probe(probe_name: str = "emberworks_worldwright_probe") -> Path:
    source = ROOT / "runtime_mods" / probe_name
    output_dir = ROOT / "dist" / "runtime_probes"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{probe_name}-0.1.0.zip"
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in source.rglob("*"):
            if path.is_file():
                archive.write(path, Path(source.name) / path.relative_to(source))
        built_dll = ROOT / "native_bridge_probe" / "target" / "x86_64-pc-windows-msvc" / "release" / "emberworks_native_bridge_probe.dll"
        if built_dll.exists():
            archive.write(built_dll, Path(source.name) / built_dll.name)
    return output


if __name__ == "__main__":
    for source in sorted((ROOT / "runtime_mods").iterdir()):
        if source.is_dir() and (source / "mod.json").exists():
            print(package_probe(source.name))
