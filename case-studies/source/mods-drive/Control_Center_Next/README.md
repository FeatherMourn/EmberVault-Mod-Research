# Enshrouded Control Center — Next

This is the new local-first HTML rebuild of Control Center. It is intentionally separate from the deprecated application in `../Control_Center`.

## Current phase

Phase 1 shell is implemented:

- Desktop-style responsive layout
- Sidebar routing for all planned modules
- Home dashboard
- Global search routed to Guides & Wiki
- Local profile selector and profile creation
- Local-storage preferences
- Shared status bar
- Searchable guide cards
- Imported offline knowledge bundle from the original Control Center
- Guide detail pages with evidence status and source links
- Safe workflow placeholders and explicit capability labels
- Content Studio project lifecycle with persistent stage tracking
- Local Mod Manager records with enable/disable, removal confirmation, and operation history
- Save Manager restore-point ledger with labels, verification status, profile association, and separate-copy restore confirmation
- Local community report history for Troubleshooter and Research Lab
- Research evidence packet export/import with duplicate protection and local review status
- Content Studio stage checklists that gate workflow advancement
- Portable workspace and active-profile mod-list export/import
- Read-only localhost bridge with game-folder health and original module inventory
- Automatic knowledge-manifest synchronization with offline fallback
- Restore-point comparison and retention-aware ledger pruning
- External Enshrouded Wiki link

Run `Run_Control_Center_Next.bat` for the recommended local experience. It starts
a local-only web server and opens the app in your browser. You can also open
`index.html` directly when Python is unavailable.

For the optional read-only connection check, start `Run_ReadOnly_Bridge.bat`
in a second window, then use **Check local bridge** from Home.

## Design rules

Every module must explain what it does, the first click, and what happens next. Game-file operations will be added behind backend services rather than directly in the browser. Destructive operations must create a restore point, require review, and remain reversible.

## Verification

From this folder, run `node --check app.js` and `python -m unittest -v test_bridge_server.py`. The knowledge bundle can be checked by confirming every `source` in `knowledge/manifest.json` exists under `knowledge/`.

## Current collaboration workflows

Research findings can be exported as `control_center.evidence_packet.v1` files and imported by another local workspace for review. Imported findings are marked `imported-for-review` and duplicate reports are ignored.

## Planned service boundaries

The deprecated Control Center contains the tested Python service layer for module discovery, fail-closed installation planning, save backup, content validation, runtime health, and live configuration. `Control_Center_Next` currently remains browser-local; it records plans and review state without writing game files. The next integration phase should add an optional localhost bridge with explicit health checks and the same backup/ownership gates before enabling live operations.

### Read-only bridge preview

Run `python bridge_server.py --game-dir "H:\SteamLibrary\steamapps\common\Enshrouded" --control-center-dir "I:\My Drive\Enshrouded Mods\Control_Center"` to expose `/api/health`, `/api/capabilities`, `/api/modules`, and `/api/profile` on localhost. Health includes the read-only count of discovered original modules; profile state separates configured modules from the catalog. This preview intentionally rejects all write requests with HTTP 405; it is a connection and capability check, not a live mod installer.

`GameService`, `ProfileService`, `ModService`, `SaveService`, `TrainerService`, `ContentService`, `ResearchService`, `TroubleshooterService`, and `WikiService` will be added behind the UI as the implementation progresses.

## Knowledge baseline

The `knowledge/guides` directory is an intentional copy of the original
Control Center documentation. `knowledge/manifest.json` records each entry's
category, source, tags, and evidence status. The new app treats this content as
an offline baseline; future synchronization can replace or extend it without
requiring a UI rebuild.
