# Enshrouded Creative Studio — standalone offline design workspace

**Status:** `OFFLINE_TESTED` storage and package; **NOT RUNTIME_TESTED** (no game integration). Version 0.1.0, 2026-09-24.

This tool separates the original Control Center's 12 custom-content studios from its Lua/EML compiler. It retains the original category-specific visual creation wizards and card displays, adds a generic JSON editor, and writes drafts to its *own* local workspace. No generated Lua or mods are deployed; no original game files or legacy registries are modified.

## Install at the requested location

Extract the **contents** of this ZIP directly into:

`I:\My Drive\Enshrouded Mods\Control\_Center\`

The ZIP's top level contains `Run_Creative_Studio.bat`, `studio/`, `tests/`, and this README. Your Google Drive sync client should then sync the extracted files. This response does not claim that the ZIP was already copied to your Windows `I:` drive or uploaded into the empty Drive folder.

1. Install Python 3.10 or newer on Windows and verify `py -3 --version`.
2. Open a terminal in `_Center` and install the one dependency: `py -3 -m pip install -r requirements.txt`.
3. Double-click `Run_Creative_Studio.bat`, or launch with `py -3 -m studio.app`.
4. Use **Import Legacy Drafts** to select your old `Enshrouded Mods\Control_Center\custom_content` directory. The tool only reads from the old folder and copies/merges compatible JSON, skipping existing IDs. Asset import is optional.
5. Continue designing in any of the 12 studios. Edit records as JSON, archive a record with recoverable trash, and export a portable *draft* ZIP from the sidebar.

## Workspace layout

```text
_Center/
  Run_Creative_Studio.bat
  requirements.txt
  README.md
  studio/
    app.py             # independent visual UI and 12 existing creation wizards
    store.py           # isolated draft JSON storage, import/export/history
    materials.py       # legacy recipe dropdowns (IDs NOT validated)
  tests/
    test_store.py
  workspaces/default/  # created on first launch; never points to old Control_Center
    registries/        # one JSON list for each of 12 studios
    history/           # backups before edits; import metadata, with hashes
    trash/             # archived drafts; non-destructive deletion
    assets/            # optional copies of models, textures, audio
    exports/           # explicitly marked offline review bundles
```

The current original `Enshrouded Mods/Control_Center` folder remains unchanged. This package does not replace `Architect_Mod/Current` or modify `ENSHROUDED KFC FILES`.

## 12 design workspaces

Furniture & props; art & paintings; hair & beards; potions & alchemy; spells & magic; building blocks; color palettes & dyes; gliders & hooks; weapons & armor; pets & companions; farming & botany; campfire music & MIDI.

The existing visual wizards' **data-entry fields** are retained from `Control_Center/gui/app.py` (snapshot retrieved 2026-09-24). The inherited material presets and IDs come from `Control_Center/core/content_importer.py`; their existence in source does **not** validate them against the current Enshrouded build.

## Safety and limitations

- **No Lua generation, live EML integration, mod deployment or automatic runtime changes.** Creation saves draft JSON only. Export bundles include a manifest, file hashes and an explicit `NOT_GAME_TESTED` marker.
- The old Control Center made broad claims about live custom content. This tool does not treat those claims as runtime proof. Rendering, model import, recipes, game IDs and compatibility still require build-specific validation before any deployment adapter can be enabled.
- Old registry import checks all candidate JSON files before updating registries. It does not overwrite drafts with matching IDs. It backs up each existing registry before edits. Deletions also copy removed records to `trash`.
- Imports involving duplicate IDs across studios are okay; duplicate IDs *within the same studio* are rejected. Invalid existing JSON blocks startup/reload instead of being silently replaced.
- **The creation wizards retain the old form validation.** Some invalid numeric inputs may raise a UI callback error instead of a polished prompt; use **Edit draft JSON** for repair. Run the offline tests before integrating future versions.
- Google Drive syncing of an actively open writable workspace from **multiple computers** can cause conflicts. Run one editor at a time, and keep Drive file-version history enabled. The app itself has no cloud locking.
- No in-game testing, Windows GUI smoke test, or current game-build validation was performed in this package's offline checks.

## Integration contract for later Lua/EML work

Treat Studio export as an immutable proposal. A separate, versioned **Export Adapter** may eventually import `creative-studio-draft-v1` after checking manifest hashes, feature support, the exact Enshrouded build, validated resource IDs, and a dry-run diff. The adapter must never mutate `Architect_Mod/Current`, install hooks, or deploy to a game unless separately authorized and independently validated. Until then, the existing Lua modules continue independently.

## Development / offline verification

`py -3 -m unittest discover -s tests -v`

The tests exercise all 12 categories, append-only backups, recovery trash, non-destructive legacy import, corrupt-input failure, export integrity, and the absence of Lua compilation paths from the standalone tool.

## Source and preservation

Created from the user-owned existing `Control_Center` project observed in connected Drive on 2026-09-24:
- `gui/app.py` — 12 existing studio wizards and card renderers adapted into `studio/app.py`.
- `core/content_importer.py` — registry naming, item method compatibility, and material dropdown data only. Its unvalidated Lua generation methods were intentionally **not** included.
- `core/manager.py` — inspected for coupling; **not included**.

The original source is not moved, replaced or deleted. Archive this exact package under an appropriate new CODE ID in `Architect_Mod/Code_History` if it becomes an implementation deliverable; do not designate it as current Architect runtime source without explicit approval.
