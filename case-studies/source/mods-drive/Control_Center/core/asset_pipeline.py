"""Format-aware asset inspection and deterministic icon-atlas planning."""
from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AssetMetadata:
    path: Path
    kind: str
    size: int
    sha256: str
    width: int | None
    height: int | None
    format: str
    engine_status: str


class AssetPipeline:
    """Inspect and plan assets without converting opaque engine payloads blindly."""

    def inspect(self, path: Path, kind: str) -> AssetMetadata:
        path = Path(path).resolve(); kind = str(kind).lower()
        if not path.is_file() or path.is_symlink():
            raise ValueError("Asset must be a regular file.")
        raw = path.read_bytes()
        width = height = None
        format_name = path.suffix.lower().lstrip(".") or "unknown"
        if kind in {"icons", "textures"} and path.suffix.lower() == ".png":
            width, height = self._png_size(raw)
            format_name = "png"
        if kind == "models" and path.suffix.lower() in {".gltf", ".glb", ".obj"}:
            suffix = path.suffix.lower()
            if suffix == ".gltf":
                json.loads(raw.decode("utf-8-sig"))
                format_name = "gltf"
            elif suffix == ".glb":
                if len(raw) < 12 or raw[:4] != b"glTF" or struct.unpack_from("<I", raw, 4)[0] != 2:
                    raise ValueError("Invalid GLB header or unsupported GLB version.")
                declared_length = struct.unpack_from("<I", raw, 8)[0]
                if declared_length != len(raw):
                    raise ValueError("GLB declared length does not match file length.")
                format_name = "glb"
            else:
                if not any(line.lstrip().startswith(("v ", "f ")) for line in raw.decode("utf-8", errors="replace").splitlines()):
                    raise ValueError("OBJ must contain at least one vertex or face record.")
                format_name = "obj"
        status = "packaged-unverified-engine-import" if kind in {"models", "audio", "textures"} else "packaged"
        return AssetMetadata(path, kind, len(raw), hashlib.sha256(raw).hexdigest(), width, height, format_name, status)

    def plan_icon_atlas(self, assets: list[AssetMetadata], cell_size: int = 128, columns: int = 8) -> dict[str, Any]:
        if cell_size <= 0 or columns <= 0:
            raise ValueError("cell_size and columns must be positive.")
        if any(asset.kind != "icons" for asset in assets):
            raise ValueError("Icon atlas accepts icons only.")
        placements = []
        for index, asset in enumerate(sorted(assets, key=lambda item: str(item.path).lower())):
            row, column = divmod(index, columns)
            placements.append({"asset": str(asset.path), "x": column * cell_size, "y": row * cell_size,
                               "width": cell_size, "height": cell_size})
        return {"schema": "control_center.icon_atlas_plan.v1", "cell_size": cell_size,
                "columns": columns, "rows": (len(placements) + columns - 1) // columns,
                "engine_status": "research-only", "placements": placements}

    @staticmethod
    def _png_size(raw: bytes) -> tuple[int, int]:
        if len(raw) < 24 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
            raise ValueError("Invalid PNG header.")
        width, height = struct.unpack(">II", raw[16:24])
        if width <= 0 or height <= 0:
            raise ValueError("PNG dimensions must be positive.")
        return width, height
