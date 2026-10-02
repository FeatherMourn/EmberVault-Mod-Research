# Steam launch path evidence — 2026-09-27

The installed Steam metadata identifies Enshrouded as:

- App ID: `1203620`
- Library: `H:\SteamLibrary`
- Install directory: `H:\SteamLibrary\steamapps\common\Enshrouded`
- Steam executable: `C:\Program Files (x86)\Steam\steam.exe`

The prior isolated smoke attempt launched `enshrouded.exe` directly. The
process was briefly responsive but no EML log update occurred, so that run is
inconclusive. The next controlled attempt should invoke Steam with
`steam://rungameid/1203620` after applying the same reversible research
profile. This preserves the normal Steam initialization path while retaining
the existing backup, isolation, and restoration gates.
