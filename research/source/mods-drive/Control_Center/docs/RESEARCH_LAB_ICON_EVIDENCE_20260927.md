# Research Lab custom-icon evidence workflow

The Control Center Research Lab now exposes **Catalog Custom Icon Evidence**.
It accepts an EML `.eml.log` file and writes
`research/icon_import_catalog.json`.

The catalog is valid only when the selected fixture contains all three runtime
markers:

1. `IMPORTED_ICON|ok=true|result=<UiTextureResource GUID>`
2. `REGISTERED|itemId=<id>|recipeId=<id>`
3. `UI_LINKS|1|matching_sets=<count>`

This proves the PNG-to-texture conversion, typed texture resource registration,
item/recipe registration, and catalog linkage. It does **not** claim that the
icon was visibly rendered in-game. Rendering remains a separate verification
step requiring a fresh screenshot or other direct visual evidence.

The workflow is intentionally research-gated and does not modify game files.
The evidence verifier is `research/tools/verify_icon_import_log.py`; the service
entry point is `core.research_lab.ResearchProbeService.catalog_icon_import_result`.
