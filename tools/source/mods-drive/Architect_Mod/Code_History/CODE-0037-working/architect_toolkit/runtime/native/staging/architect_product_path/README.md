# CODE-0012 staging boundary

This directory is reserved for a future product-path package. CODE-0012 does
not build or deploy a native DLL and does not contain an EML runtime loader.
The authoritative offline planner is
`tools/ArchitectProductPath/product_path_staging.py`; its manifest is written
to `bridge/blueprint_ghost_identity_perturbation_manifest.json`. The generated
preview package is `runtime/staging/ArchitectProductPathPreview.lua`; it
defaults off, is not loaded by the current mod, and exposes an explicit
`activate()` entry point using only source-anchored clone/append operations.

No file here may replace `runtime/native/ArchitectNativeRuntime.dll` or alter
`Architect_Mod/Current` without a separately authorized milestone.
