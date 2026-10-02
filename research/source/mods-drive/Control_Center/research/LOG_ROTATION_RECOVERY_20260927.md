# EML log rotation recovery record — 2026-09-27

## Action

The two oversized historical logs were moved out of the live game log
directory while Enshrouded was not running:

| Original | Recovery location | Size |
|---|---|---:|
| `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-27.eml.log` | `H:\Enshrouded_ControlCenter_Backups\20260927-log-rotation\2026-09-27.eml.log` | 1,902,753,529 bytes |
| `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-26.eml.log` | `H:\Enshrouded_ControlCenter_Backups\20260927-log-rotation\2026-09-26.eml.log` | 1,298,298,247 bytes |

## Verification

A later regenerated log exceeded the smoke-test threshold and was archived
with the reusable rotation tool on 2026-09-27:

| Original | Recovery location | Size |
|---|---|---:|
| `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-27.eml.log` | `H:\Enshrouded_ControlCenter_Backups\20260927T212243Z-log-rotation\2026-09-27.eml.log` | 368,679,003 bytes |

The operation was performed while Enshrouded was not running. The rotation
manifest is stored beside the archived log.

The live-loader preflight was rerun after the move and reported:

```text
status: ready
latest_eml_log: null
warnings: []
```

The operation changed no mod directories or save files. To restore a log for
historical analysis, move the corresponding file back to the live `logs`
directory while the game is closed.
