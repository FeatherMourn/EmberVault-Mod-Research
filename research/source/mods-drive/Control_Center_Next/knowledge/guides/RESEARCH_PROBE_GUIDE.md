# Research-probe guide

Prepare a fresh isolated profile, verify the pinned build, install only one
research probe, capture the exact log and screenshots, and stop on any panic.
Remove the probe while the game is stopped, restore the stable profile, and
record a structured verdict with limitations. Never promote a probe to stable
from registration success alone.

Before starting a research session, close Enshrouded completely. The session
launcher checks for an existing `Enshrouded.exe` process and refuses to start
another session if the game is already running. This prevents overlapping
Steam launches and protects the current profile from being tested twice.
If the launcher reports that Enshrouded is already running, close the game and
run the same session command again; no probe is installed or changed by that
refusal.

After the game is stopped, remove an owned probe transactionally with:

`python tools/install_research_probe.py <probe> <game-dir> --storage <storage> --remove`

The command uses the ownership record and removes only files that still match
the installed probe. It will not remove arbitrary or modified files.

To install one validated research-only probe for a controlled session, use the
plain-language `--install` alias together with explicit research approval:

`python tools/install_research_probe.py <probe> <game-dir> --storage <storage> --install --allow-research --expected-build 1076226`

The installer remains dry-run by default. It refuses a research-only probe
without `--allow-research`, refuses a build mismatch, and should only be run
while Enshrouded is closed. Use `--remove` after the session, then restore the
stable profile before normal gameplay.
# Research probe safety

## Known-stalling resource families

The installer rejects probes that directly query these resource families because
the current EML build has a recorded fresh-session stall while resolving them:

- `keen::AnimationGraphResource2_0`
- `keen::ds::AnimationGraphResource2_0`
- `keen::VoxelWorldResource`
- `keen::VoxelWorldChunkResource`
- `keen::WaterWorldResource`

This is a safety boundary, not a claim that the engine can never support these
systems. Use already-proven donor families, such as
`keen::actor::ActorSequenceResource`, for normal research work.

Only a deliberately bounded boundary experiment may override the gate, using
`--allow-unsafe-boundary` with a fresh isolated profile, a fresh-session log
baseline, and an immediate stop-and-restore plan. Do not use that override for
stable modules or ordinary content development.

## Chair/stool clone verification path

The reproducible chair/stool probe is:

`research/probes/chair_stool_clone_1076226`

The current runtime report proves registration only. The beginner wizard does
not yet select this probe automatically; until that UI entry is added, use the
advanced research workflow with this probe and follow the same evidence path:

1. Open Control Center and select **Research Lab**.
2. Use the advanced research workflow for
   `chair_stool_clone_1076226`; do not add it to the stable profile.
3. Validate the probe and prepare the safe test.
4. Launch the game through Control Center.
5. Open the Carpenter/build menu and capture the chair/stool tile with the
   new item selected.
6. Place the item in the world, show its interaction prompt, and capture that
   screen separately.
7. Save, close the game, relaunch the same profile, and confirm the item still
   exists before capturing the persistence result.
8. Close the game, remove the probe, restore the stable profile, and keep all
   screenshots with the structured runtime report.

Registration, catalog visibility, placement/interaction, and save persistence
are separate results. A successful loader message alone does not promote the
chair/stool clone to stable.

