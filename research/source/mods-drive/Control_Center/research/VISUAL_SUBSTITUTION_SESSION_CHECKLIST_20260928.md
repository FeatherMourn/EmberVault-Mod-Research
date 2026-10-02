# Visual-substitution controlled-session checklist

Probe: `registered_visual_substitution_probe_20260928`  
Build: `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`  
State: research-only

Current fresh-session baseline: `probe_sessions/visual_substitution_baseline_20260928_r2.json`.

## Before launch

- Confirm the game is stopped.
- Confirm the stable profile contains no research-only or unclassified modules.
- Record a fresh log baseline with `tools/prepare_probe_session.py`.
- Apply an isolated smoke profile containing only the probe and required stable
  loader support.
- Verify the probe manifest IDs and replacement model GUID match the staged
  package.

Run a dry-run first and save its report:

```text
python tools/install_research_probe.py \
  research/staging/registered_visual_substitution_probe_20260928 \
  H:\\SteamLibrary\\steamapps\\common\\Enshrouded \
  --storage <research-state> \
  --expected-build "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z" \
  --output research/probe_sessions/visual_substitution_install_dry_run_20260928.json
```

Only after the isolated profile is ready should an operator repeat the command
with explicit `--install`, `--allow-research`, and `--output` arguments. The
approval flag is intentionally required because this probe is research-only.

## In-game hypothesis

The new item should appear as a distinct recipe/UI entry and retain the donor
bed mechanics while using the replacement visual reference. Inspect both the
catalog icon/preview and a placed object. A successful Lua assignment or
registration log alone is not visual proof.

Before capturing catalog evidence, load a save that has an accessible player
building area and enter the building-tool context with the Summoning Staff or
other configured building tool. The current user profile maps `UiBuildingMenu`
to `Tab`, but that key does not open the catalog from a non-building interior.
Treat a world-entry screenshot from such a location as world evidence only,
not as catalog or visual-substitution proof.

## Evidence to capture

- Fresh EML log with the probe markers.
- Screenshot of the new catalog entry.
- Screenshot of the placed object.
- Whether donor and replacement mechanics remain unchanged.
- Any crash, panic, missing-resource, or fallback message.

## After the session

- Stop the game before cleanup.
- Verify the fresh log boundary and classify the session evidence.
- Remove the probe from the isolated profile.
- Restore the stable profile and run live-loader preflight.
- Record the result as `verified`, `experimental`, `research-only`, or
  `unsupported`; do not promote from log registration alone.
