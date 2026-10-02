# Enshrouded content-loader project summary

## Objective

Build and verify a practical way to add custom Enshrouded content, understand EML and `dinput8.dll`, improve the loader, and provide reusable tooling for future mod development.

## What was researched and built

### KFC and resource discovery

- Created safe extracted and working KFC copies under `H:\Enshrouded_KFC_Extracted_20260926` and `H:\Enshrouded_KFC_WorkingCopy_20260926`.
- Identified the runtime resource types needed for furniture content: `keen::ItemInfo`, `keen::ItemRegistryResource`, `keen::RecipeRegistryResource`, `keen::ItemKnowledgeResource`, `keen::FbUiBundle`, and `keen::HashKey32`.
- Built inspection/repacking helpers and documented the staged KFC route.
- Confirmed static archive edits are overwritten by EML's startup patch pass, so runtime registration is the reliable route.

### EML upgrade

Source tree: `H:\enshroudedresearch\external\kfc-parser-source`.

Modified EML Lua assets support to:

- expose `game.assets.register_resource(value, type, guid, part)`;
- retain newly-created resources in type indexes;
- return newly-created resources through `get_resources_by_type` and `get_all_resources`.

Build verification passed with `cargo check -p mod-loader-lua`, release Lua-loader build, and release `dinput8-proxy` build.

### `dinput8.dll`

- Rebuilt the proxy from the EML source tree.
- Added runtime DLL loading using `libloading` and retained library handles for the loader lifetime.
- Installed the rebuilt proxy with a reversible backup at `H:\Enshrouded_LiveBackup_20260926_runtime_dll_upgrade`.
- Verified the game launches and remains responsive with the rebuilt proxy.
- Fixed a shutdown-only Rust TLS panic by removing runtime cleanup from
  `DLL_PROCESS_DETACH`; Windows now reclaims process-owned loader state during
  exit instead of calling mutex/library teardown while TLS is being destroyed.
  The patched proxy was installed on 2026-09-26 with a reversible backup at
  `H:\Enshrouded_LiveBackup_20260926_runtime_shutdown_fix\20260926-200943`.

### Custom content proof

The bed experiment uses:

- donor item `2940001508`;
- new item `3987654321`;
- donor recipe `3531872774`;
- new recipe `3987654322`.

The live log proved:

- indexed ItemInfo count increased from 3520 to 3521;
- the clone was discoverable by its new ID;
- item and recipe registries increased;
- item knowledge link was added;
- typed `HashKey32` creation succeeded;
- UI link used the new recipe ID.

The final UI solution clones the containing `FbUiBundle` recipe set. `set.entries` is a fixed-size typed array; appending to it produced an out-of-bounds error. Cloning the set and appending it to `group.sets` succeeded:

- donor set entries: 9;
- donor entry index: 8;
- groups before: 8;
- groups after: 9;
- new entry value: `3987654322`.

The Carpenter → Beds menu was visually verified in-game. An additional bed slot appeared at the end of the category and displayed as “Palm Wood Bed.”

## Reusable artifacts

- `research/runtime/kfc_content_registry.lua` — reusable runtime registration helper.
- `research/runtime/kfc_content_mod_template.lua` — starter mod template.
- `research/runtime/KFC_CONTENT_REGISTRY_HELPER_20260926.md` — helper documentation.
- `research/UI_CATALOG_CLONING_20260926.md` — typed UI catalog findings.
- `research/EML_RESOURCE_REGISTRATION_UPGRADE_20260926.md` — EML source/API upgrade notes.
- `research/KFC_EXTERNAL_CONTENT_ROUTE_1076226.md` — KFC staging and runtime patch findings.
- `research/tools/repack_custom_content.ps1` — guarded repacking wrapper.
- `research/tools/install_kfc_helper.ps1` — installs the reusable helper into a validated EML mod directory.

## Safety and rollback

Live backups were created before DLL and KFC-related changes. The unstable query-graph and fixed-array experiments were reverted. The active game configuration uses the stable cloned-set implementation.

## Remaining limitations

- Custom localization payload creation is now implemented as a research-gated project/runtime route; the isolated build `1076226` probe registered both a new `LocaTag` and matching locale collection entry. Visual UI consumption still requires a separate in-game confirmation.
- The current template assumes the helper is available to EML's Lua module search path; packaging it directly beside a mod may require adapting the loader's module path or inlining the helper.
- The solution is proven for runtime registration and one furniture recipe. Broader content classes still need donor-specific schema validation.
