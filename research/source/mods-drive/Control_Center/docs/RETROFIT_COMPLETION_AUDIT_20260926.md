# Control Center Retrofit Completion Audit

This audit distinguishes local implementation evidence from game-facing runtime
evidence. A passing unit test proves a local service contract; it does not prove
that Keen's client consumes a newly registered resource.

## Evidence summary

### Canonical project path

The retrofit target named in the original objective (`Control\\_Center`) is not
present on disk. The authoritative working project is
`I:\\My Drive\\Enshrouded Mods\\Control_Center`; all current source, tests,
research artifacts, and audit evidence are maintained there. No duplicate
project was created, avoiding divergent installations.

- Local implementation: all 50 matrix rows have a tested service or UI path.
- Automated verification: the full suite currently passes 162 tests, and
  `core`, `gui`, and `tools` compile successfully.
- Offline archive verification: the patched KFC was unpacked read-only and the
  new `ItemInfo`, item registry entry, recipe output, knowledge link, and UI
  recipe link all passed `research/tools/verify_kfc_fixture.py`. This proves
  serialized registration, not client rendering.
- Strongest controlled runtime fixture: the bed clone on game build `1076226`.
  Logs prove resource registration, registry growth, knowledge linkage, typed
  hash creation, and safe cloned UI-set insertion. An additional bed slot was
  visually confirmed in-game, and the inserted slot now renders a bed image.
  A unique recipe GUID was required to prevent catalog deduplication.
- Reversible operation: generated content, release packages, profiles, and
  installer-owned files use manifests, hashes, staging, backups, and rollback.
- Release packaging: the PyInstaller one-file application was built
  successfully at `dist/EnshroudedModHub.exe`, and the Inno Setup installer
  was compiled successfully at
  `packaging/Output/EnshroudedModHub-Setup.exe`. The spec and installer
  source paths were corrected for the canonical `Control_Center` layout.
- Current preflight: the combined localized-bed probe is ready for build
  `1076226`; the game directory, logs directory, probe files, and declared
  build matched, and no Enshrouded process was active.
- Live health snapshot: build `1076226` was detected; the staging bed project
  validated; 4 installed content mods were inventoried; the module graph had
  no issues; and the bounded diagnostic scan completed successfully. Aggregate
  diagnostics reported 0 total errors, while runtime status remained degraded
  because the latest log contains one historical startup error.
- Live replacement safety: the installed localized-bed probe has an ownership
  manifest with SHA-256 file records and a populated rollback backup containing
  all three replaced files.
- Live integrity report: the health snapshot reports the localized-bed probe as
  `integrity: verified` from those ownership hashes; unrelated legacy mods
  remain `not_available` rather than receiving an unsupported integrity claim.

## Evidence boundaries that remain explicit

| Area | Current conclusion | Required evidence to promote it |
|---|---|---|
| Custom localization | Runtime registration verified; UI consumption remains research-only. | A fresh controlled session showing the custom label in the relevant catalog and a saved screenshot/log reference. |
| Model/audio engine import | File/package validation verified; engine import remains unverified. | A controlled donor-specific resource test proving the client consumes the imported asset. |
| Broader content classes | Schemas and validation gates exist; only the bed fixture is end-to-end verified. | One controlled fixture per content family, with logs and visual or game-facing confirmation where applicable. |
| Live game validation | Preflight refuses to run while Enshrouded is active. | Close the current session, run one isolated probe, preserve the resulting log, and catalog evidence. |

## Safe next validation sequence

1. Close Enshrouded normally; do not terminate it from the Control Center.
2. Run the Content Center controlled-probe preflight against the target build.
3. Use a disposable profile/world and a backed-up probe package.
4. Launch once, collect the newest `.eml.log`, and inspect structured markers.
5. Capture the relevant in-game UI state if the feature is visible.
6. Catalog the log hash and visual evidence before changing feature state.

Until those runtime gates are satisfied, the Control Center deliberately keeps
the affected features marked research-only or runtime-verified/UI-research-only.

Latest controlled launch result: localization tag/collection registration,
item cloning, recipe registration, and UI-set linking all succeeded. With the
unique recipe GUID fix, the bed fixture is cataloged as
`end_to_end_visual_verified`: the inserted Carpenter/Beds slot renders a bed
image in-game. Custom localization payloads, non-donor icons/models, and
broader content classes remain follow-up work.

## Latest stability verification

The combined localized-bed probe was redeployed after removing unsafe `nil`
assignments to typed recipe fields. The subsequent controlled launch completed
all registration markers, including `REGISTERED`, `COUNTS`, `ITEM_KNOWLEDGE_LINKS`,
and `UI_LINKS`. Enshrouded then exited normally; the newest log contained no
panic, fatal error, `AccessError`, loader-environment error, or mod-loader
failure. This verifies the current probe's startup and shutdown stability.

## Visual evidence update

The latest supplied in-game screenshot confirms that the cloned catalog set
creates an additional Carpenter/Beds slot and that the slot renders a bed
image. The decisive correction was giving the cloned recipe a unique
`recipeGuid`; reusing the donor GUID allowed registration to succeed but left
the client catalog entry visually blank. The fixture is therefore promoted to
`end_to_end_visual_verified` for the current bed path. Its displayed label and
requirements still come from the donor profile, so custom localization and
independent visual-asset registration remain follow-up milestones.
