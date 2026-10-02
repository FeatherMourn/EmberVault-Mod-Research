# Control Center — EML discovery repair — 2026-09-24

## Scope
The user-provided 4,774,209-byte `Control_Center.zip` was inspected without executing untrusted game hooks. Original SHA-256: `58f6726185ff20544b2c3db4ac67f8bd32dec0a20f84d2d61cc42b2e48cd319a`.

## Findings
- Uploaded archive contains desktop Control Center Python source, modules, profiles and a generated `runtime/master_loader.lua`, but **no loadable EML `mod.json` + `src/mod.lua` package at its root**.
- `core/installer.py` generates `mod.json` without EML's required `capabilities` array. This blocks recognition on EML versions enforcing the documented manifest schema.
- The alternate GUI's **Recompile & Deploy** and **Launch** paths only called `manager.compile_master_lua()`, writing the local preview, not installing the EML mod.
- EML proxy detection missed `dbghelp.dll` (recommended proxy in referenced EML guide).
- All 28 Control Center modules were enabled in the uploaded active profile. Recognition and Lua syntax alone do not validate the game-resource fields or claims in any module.

## Repair and test outputs
Use **only the `_VERIFIED` packages** in this folder. Earlier unsuffixed uploads are superseded, and the unsuffixed probe is an empty ZIP; they remain retained for history.

- `EMH_EML_Loader_Probe_VERIFIED.zip` (508 bytes): zero-mutation `emh_loader_probe` EML package. Expected console line: `[EMH probe] EML loaded the diagnostic mod.`
- `Control_Center_EML_Fixed_Source_VERIFIED.zip` (4,427,490 bytes): source with corrected manifest, proxy detection, and actual installation for alternate GUI; existing default Control Center `Review & Apply` also installs through same service. Source patch includes cross-platform mocked process-state test only in a test file.
- `EMH_EML_Profile_Experimental_VERIFIED.zip` (10,708 bytes): actual EML mod generated from all 28 originally enabled modules, now with `capabilities: ["patch"]`. **EXPERIMENTAL and NOT in-game verified**. Use test world and save backup.

Offline verification: ZIP CRC and file-tree validation PASS; 18/18 Python unit tests PASS; Python compileall PASS; Lua loadfile syntax of both generated EML Lua files PASS. No EML runtime/game launch or current-build compatibility test was available. `runtime` in EML documentation was still WIP; the package uses startup `patch` only, and desktop GUI does not become an in-game overlay.

## Deployment test
1. Stop Enshrouded. Unzip the verified loader probe into `<game-dir>/mods/` so `mods/emh_loader_probe/mod.json` and `mods/emh_loader_probe/src/mod.lua` exist.
2. Verify EML is installed and working; enable `"enable_console": true` in `<game-dir>/eml.json` (the file appears after a successful first EML launch). Launch and confirm the `[EMH probe]` line in the EML console/log. If the proxy itself does not start, inspect the proxy choice, game path, and EML logs before considering the gameplay modules.
3. Only after the probe succeeds, use the fixed desktop source's `Run_Control_Center.bat`, select game directory and `Review & Apply`, or manually unzip the experimental profile package into the game `mods/` directory. For first runtime trial, disable unverified modules and test with a backed-up test world, then confirm the `[Enshrouded Mod Hub] EML patch entry point loaded` console line.

Official documentation used: https://brabb3l.github.io/kfc-parser/eml/develop/setup.html ; https://brabb3l.github.io/kfc-parser/eml/usage.html .

The original user archive was separately staged unchanged under `Enshrouded Mods/Incoming/2026-09-24/INC-0066/`; no canonical Current source was changed. No new primary mod was designated.
