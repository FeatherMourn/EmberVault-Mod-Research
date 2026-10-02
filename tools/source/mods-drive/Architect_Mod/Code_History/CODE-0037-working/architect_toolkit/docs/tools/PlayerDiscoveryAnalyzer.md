# Player Discovery Analyzer

`tools/PlayerDiscovery/analyze_player_discovery.py` performs read-only, offline
correlation of `bridge/player_discovery.jsonl`. It never accesses the game
process and never treats behavioral similarity as proof.

Run it from the repository root:

```powershell
python tools/PlayerDiscovery/analyze_player_discovery.py
```

The default deterministic machine-readable output is
`bridge/player_discovery_report.json`. Use `--text-output <path>` for a compact
human-readable companion. An alternate capture may be supplied as the first
argument.

Events are consolidated first by `entityId`, then by `ownerPointer`, then by
`componentPointer`, and finally by `probeId`. Numeric samples may use
`raw.float`, `raw.u32`, `raw.u16`, `raw.value`, or top-level `value`. The
analyzer compares phase medians, preserves client/server sides and pointer
observations, and reports malformed lines instead of silently accepting them.

The analyzer emits only experimental, disproven-by-behavior, or insufficient-
evidence candidate states. It cannot establish local-player ownership,
component ownership, authority, or a safe mutation path.

Marker-only captures are valid. They preserve the observed phase list and
produce `UNSOLVED_INSUFFICIENT_EVIDENCE` with zero candidates; phase markers
are never promoted into synthetic candidates.
