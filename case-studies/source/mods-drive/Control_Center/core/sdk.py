"""Stable developer SDK surface for EML/KFC content modules."""

from __future__ import annotations

import shutil
from pathlib import Path


class SdkError(RuntimeError):
    pass


class DeveloperSdk:
    """Expose versioned helper packaging without requiring internal paths."""

    SDK_VERSION = "1.0"
    CAPABILITIES = (
        "assets.register_resource",
        "kfc.clone_resource",
        "kfc.append_registry",
        "kfc.clone_recipe_set",
        "kfc.localization_registry",
    )

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.helper_source = self.base_dir / "research" / "runtime" / "kfc_content_registry.lua"
        self.localization_helper_source = self.base_dir / "research" / "runtime" / "kfc_localization_registry.lua"

    def manifest(self) -> dict:
        return {"schema": "control_center.sdk.v1", "version": self.SDK_VERSION, "capabilities": list(self.CAPABILITIES)}

    def package_helper(self, module_root: Path) -> Path:
        module_root = Path(module_root)
        if not self.helper_source.is_file():
            raise SdkError(f"Bundled KFC helper is missing: {self.helper_source}")
        destination = module_root / "src" / "kfc_content_registry.lua"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.helper_source, destination)
        localization_destination = module_root / "src" / "kfc_localization_registry.lua"
        if not self.localization_helper_source.is_file():
            raise SdkError(f"Bundled localization helper is missing: {self.localization_helper_source}")
        shutil.copy2(self.localization_helper_source, localization_destination)
        return destination
