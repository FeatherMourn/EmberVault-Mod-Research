from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist" / "mods"


def package_all() -> list[Path]:
    DIST.mkdir(parents=True, exist_ok=True)
    outputs = []
    for manifest_path in sorted(ROOT.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        package_id = manifest["id"]
        package_dir = manifest_path.parent
        output = DIST / f"{package_id}-{manifest['version']}.zip"
        with ZipFile(output, "w", ZIP_DEFLATED) as archive:
            for path in package_dir.rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts:
                    archive.write(path, Path(package_id) / path.relative_to(package_dir))
        outputs.append(output)
    return outputs


if __name__ == "__main__":
    for artifact in package_all():
        print(artifact)
