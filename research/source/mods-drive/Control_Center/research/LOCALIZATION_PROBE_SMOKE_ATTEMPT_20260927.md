# Localization Probe Smoke Attempt — 2026-09-27

## Purpose

Exercise the corrected localization probe in an isolated game profile after fixing the stale global-`hasher` dependency in the older staged helper.

## Procedure

- Confirmed Enshrouded was closed before changes.
- Applied `research/isolated_smoke_profile_20260927.json`.
- Quarantined all seven existing live modules through the reversible Control Center workflow.
- Installed the corrected `research/probes/localization_runtime_1076226` as the temporary `control_center_localization_probe` module.
- Started Enshrouded and confirmed the process was responsive.
- Waited for a fresh EML log session and searched for localization, panic, fatal, and error markers.
- No fresh or updated EML log appeared during the observation window, so no runtime result was assigned.
- Stopped the test process, moved the temporary probe to the Control Center quarantine area, and restored all seven original modules.

## Result

**Inconclusive — no loader evidence was produced.**

This attempt does not prove or disprove localization registration or UI consumption. It must not be promoted to a runtime-success or runtime-failure result. The absence of a fresh log suggests the launch did not reach the expected EML logging path, but that is an observation requiring a separate launch-path investigation.

## Recovery verification

Post-test live verification reported:

- loader status: `ready`;
- live module count: 7;
- research-only module count: 5;
- temporary probe present in live mods: `false`.

The temporary probe remains recoverable at:

`profiles/quarantine/localization_probe_inconclusive_20260927`

## Follow-up launch-path check

A second attempt used the installed Control Center/Steam launch route:

`steam://rungameid/1203620`

The result was the same: a responsive `enshrouded.exe` process appeared, but
the existing `.eml.log` timestamp and size did not change. This reproduces the
observation across both direct executable and Steam URI launches. The issue is
therefore currently classified as a fresh-log/session-observability blocker,
not as a localization registration result.

The second temporary probe was moved to:

`profiles/quarantine/localization_probe_steam_inconclusive_20260927`

All original modules were restored again and live verification returned
`ready` with seven modules and no temporary probe installed. UI label
consumption remains unverified.
