# CC2 observe-only probe checklist

1. Disable the original Control Center and use a disposable test world.
2. Confirm the installed loader accepts `probe_mod/CC2_Research_Probe`; retain capability `patch`, never `runtime`.
3. Manually stage the probe using the loader’s documented mod location. Do not auto-deploy, overwrite an existing folder, modify game files, or modify saves.
4. Enable console/loader logging, start the game, and load the disposable world.
5. Capture loader banner, game build/revision, EML version, CC2 lines, and errors.
6. Stop after observation; the probe must not call `create_resource` or `create_content`.

Pass: probe loads; `game.assets` exists; each of five resource types returns a result/count; `get_resource(rake_guid, "keen::ItemInfo", 0)` returns a result or explicit nil/error; creation APIs are only reported.

Fail: load error, mutation call, missing required API, signature error preventing checks, or unexplained failure to resolve the selected rake GUID.
