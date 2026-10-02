# Control Center 2 — KFC Custom-Content Research Lab (v0.1)

**Separate application.** This does not modify, depend on, deploy, or disable the original Control Center. Disable the original yourself before any later in-game testing. CC2 does not automatically install a mod.

**Current status:** local research tool, **not a functioning new-item mod yet**. The next unknown is whether your installed version of EML can register the complete independent item/recipe/knowledge/visual graph at the required initialization phase. The included probe only observes and logs; it does not create or patch resources.

## Windows quick start

1. Extract this ZIP into a **new** folder outside the original Control Center and outside `ENSHROUDED KFC FILES`.
2. Install Python **3.10+** with Tkinter. No third-party Python packages are required.
3. Double-click `Run_Control_Center_2.bat` (or run `python -m cc2 gui` from this folder).
4. Point the top folder selector at a **local, read-only copy** of the `ENSHROUDED KFC FILES` ZIP archives; click **Index sources**. The program only reads ZIPs and writes its own `workspace/catalog.sqlite3`.
5. In **Vanilla catalog**, search an item name or numeric ID, select a registered vanilla item, and inspect its resource relationships. Use **New-item research plan** to export a JSON plan; it deliberately does **not** generate unsafe mutation Lua.
6. Run **Diagnostics** to compare the catalog's registry, item and recipe references. Take the KFC export date/game build into account; ZIP timestamps by themselves do not prove the originating build.

The distributed SQLite index is a convenience snapshot of the subset of September 14 resource exports available for this development session, so the catalog works immediately. The archive paths inside that snapshot point to the author's temporary machine: **reindex on your PC before using raw-source inspection or trusting compatibility with your present game**. No actual KFC archives are bundled or modified.

## Commands

```
python -m cc2 --help
python -m cc2 index --kfc "D:\\ENSHROUDED KFC FILES"
python -m cc2 search "stone" --limit 10
python -m cc2 inspect YOUR_VERIFIED_ITEM_GUID
python -m cc2 diagnose
python -m cc2 plan YOUR_VERIFIED_ITEM_GUID --slug test_stone_clone --name "Test Stone Clone" --out workspace/test_stone_clone.json
```

## Separate observe-only test mod

`probe_mod/CC2_Research_Probe` contains a manual-install EML research probe. **Do not install it until you confirm the installed EML format/version and take a backup.** Run on a disposable test world, with the original Control Center disabled. It only logs whether selected `game.assets` functions are exposed and attempts to count item, registry, and recipe resources. Some interfaces may require another calling convention: a lookup error is evidence to investigate, not proof an API is unavailable. Retrieve your game build, EML version and EML logs. The probe is **not** auto-deployed by CC2.

## What's implemented and what isn't

- Implemented: read-only ZIP indexing with SHA-256 provenance; searchable item catalog; registry/recipe/knowledge/workshop references; static diagnostics; isolated Tkinter desktop application; non-deployable clone research plans; standalone observe-only EML probe.
- Unsolved: tested EML registration API and initialization timing; collision-free numeric IDs; complete new-item resource schema; localization, crafting unlock and visual linking; original binary texture/model creation; game/runtime validation.

**Safety:** Never modify the KFC ZIP archives. Never install the research probe alongside the legacy mod. CC2 v0.1 does not install anything into Enshrouded, mutate a save, or claim custom-content success. All actual changes require a later verified build-specific experiment.

See `docs/FINDINGS.md` and `docs/TEST_PLAN.md`.
