# Static executable inventory

This inventory is independent of the reference tables and is not a feature implementation.

| Item | Observed value |
|---|---|
| Format | PE32+ / x64 |
| Image base | `0x140000000` |
| Entry RVA | `0x2D6D310` |
| Image size | `0x2DA7000` |
| `.text` RVA / raw size | `0x1000` / `0x12A5200` |
| `.rdata` RVA / raw size | `0x12A7000` / `0xC36E00` |
| Imports | 17 DLLs |
| SHA-256 | `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781` |

Printable-string counts are only triage signals, not target identification: `health` 135, `stamina` 93, `mana` 56, `glider` 72, `oxygen` 38, `craft` 297, `inventory` 327, `voxel` 809, and `teleport` 92. No hook is inferred from these counts.

Status: infrastructure static analysis complete; all gameplay features remain `Not implemented`.

## Runtime module observation (read-only)

At the time of observation, PID `7652` had the main module loaded at `0x7FF6B19D0000` with size `0x2DA7000`, matching the recorded image size. Additional game-local modules observed included `DINPUT8.dll`, `shroudtopia.dll`, and Steam/graphics components. Custom modules observed under the game installation included:

- `H:\SteamLibrary\steamapps\common\Enshrouded\mods\flight_mod\flight_mod.dll`
- `H:\SteamLibrary\steamapps\common\Enshrouded\mods\ChatCommands.dll`
- `H:\SteamLibrary\steamapps\common\Enshrouded\mods\whitelist_mod.dll`

This was module enumeration only; no process memory was read or written. Future AOB validation must scope scans explicitly to `enshrouded.exe` or to a named custom module and must treat the loaded custom modules as a separate compatibility risk. The presence of `flight_mod.dll` is not evidence that the table's flight feature is implemented or safe.

## Limited live integrity check (read-only)

The running process was opened with read-only access. The first 32 bytes at the live entry point (`base + 0x2D6D310`) matched the corresponding on-disk bytes exactly:

`E8 00 00 00 00 50 53 51 52 56 57 55 41 50 41 51 41 52 41 53 41 54 41 55 41 56 41 57 48 8B 4C 24`

This is only a narrow integrity check. It does not prove that other executable regions are unmodified and does not promote any feature beyond `Not implemented`.

## Independent string cross-reference triage

`analyze_feature_xrefs.py` scanned the executable's `.text` section with Capstone and searched `.rdata` for feature vocabulary. It found 857 term-bearing printable strings but zero direct RIP-relative references to the starts of those strings. This negative result is insufficient for target identification; no AOB or gameplay hook was derived from it. The analyzer's result is therefore recorded as `STATIC_CANDIDATES_ONLY`.
