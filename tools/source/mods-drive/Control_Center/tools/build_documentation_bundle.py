"""Build a deterministic archive of the user-facing Control Center docs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.audit_documentation import REQUIRED, audit


def build(root: Path, output: Path) -> Path:
    root = Path(root).resolve()
    result = audit(root)
    if not result["valid"]:
        raise ValueError("Documentation audit failed: " + ", ".join(result["missing"]))
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with ZipFile(temporary, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for key, relative in sorted(REQUIRED.items()):
            path = root / relative
            info = ZipInfo(relative)
            info.date_time = (2026, 1, 1, 0, 0, 0)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    temporary.replace(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.root, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
