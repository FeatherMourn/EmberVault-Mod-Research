# Run the platform inventory probe

This runbook requires the user to perform the live EML launch. The research
agent must not execute these commands automatically.

## Safety gate

Before running, confirm:

- The game is closed while the mod folder is staged.
- The probe is copied as a separate mod; existing `flight_mod` is untouched.
- The probe manifest requests export only and no patch capability.
- The export destination is the configured `export` directory.
- No save or game archive is being edited.

## Staging commands

The reviewed mod package is in:

`research/probes/embervault_platform_inventory/`

It contains `mod.json` and `src/mod.lua`. Copy the entire package directory
into the game `mods` directory; do not rename the inner folder.

```powershell
$Game = "H:\SteamLibrary\steamapps\common\Enshrouded"
$ProbeSource = "I:\My Drive\Enshrouded Mods\EmberVault-Suites\EmberVault-Mod-Research\research\probes\embervault_platform_inventory"
$ProbeRoot = Join-Path $Game "mods\embervault_platform_inventory"

Copy-Item $ProbeSource $ProbeRoot -Recurse -Force
```

After launching Enshrouded normally through Steam and closing it, inspect:

```powershell
$Export = Join-Path $Game "export\embervault\platform-inventory-v1.tsv"
Test-Path $Export
Get-FileHash $Export -Algorithm SHA256
```

Do not use `--patch`, `emm.exe repack`, `emm.exe restore`, or any save-related
command for this probe. Stop if EML reports an error, the game does not close
normally, or the output is missing. Preserve the output and hash for manual
review before importing it into Mod Research.
