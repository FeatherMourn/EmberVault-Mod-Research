# Live Environment Snapshot — 2026-09-27

Captured read-only before the next controlled smoke test.

## Observed state

- Enshrouded process: stopped.
- `dinput8.dll`: present.
- Game `mods/` directory: present.
- Mod directories: 8; names passed the loader naming check.
- Latest EML log: `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-27.eml.log`.
- The latest read-only preflight is recorded in
  `research/LIVE_LOADER_ISOLATION_PREFLIGHT_20260927.json`.
- Three installed folders are currently unclassified because they lack an
  explicit `feature_state`: `content_donor_probe_1076226`,
  `emberworks_worldwright_probe`, and `flight_mod`.

## Interpretation

The loader installation is structurally ready, but fresh-session observability
is not currently demonstrated. Five installed modules are explicitly marked
research-only, so a production smoke test should use an isolated profile or
quarantine those modules first. The strict isolation preflight is currently
not ready because all three unclassified folders must be excluded or explicitly
classified. No live files were changed for this snapshot.

The isolated-profile dry run also passed: all seven live modules are accounted
for as exclusions, with no missing exclusions or unaccounted modules. It used
the same 1,279,938-byte log baseline and changed no live state.

## Next safe gate

Establish a fresh-session log boundary with an isolated, reversible profile,
then run only the smallest donor-preserving probe. Do not promote localization
or visual substitution based on this snapshot.
