# Item Observer Stack Scanner Performance Fix v7.1

## Performance bug

The v7 broad scan performed a second `ReadProcessMemory`, hex encoding, and two
SHA-256 calculations for every match. It also traversed each buffer once per
requested value. Common integers can occur tens of thousands of times, so work
scaled with both candidate count and target count and appeared frozen without
progress output. PowerShell also enumerated returned `byte[]` buffers through
the pipeline; returning each buffer as one object removed that hidden per-byte
marshalling cost.

## Root cause / old pipeline

The discovery and object-characterization stages were coupled: bulk region read
→ per-value scan → per-hit process read → context serialization and hashing.
Those expensive operations supplied no evidence needed by the initial
baseline/split/move/merge address comparison.

## New pipeline

1. Fast, evidence-complete exact-value captures.
2. Offline transition comparison and ranking.
3. Targeted `±0x40` context capture for only the surviving addresses.

## Fast scan

`StackMemoryReader.cs` walks each bulk buffer once for all requested values,
using a target hash set and manual bounds-safe little-endian assembly instead of
`BitConverter` in the hot loop. The default chunk size is 8 MiB. Reads include a
three-byte overlap; only starts in the logical chunk are reported, preventing
boundary omissions and duplicate hits. `uint32`/`int32` use four-byte alignment;
opt-in `uint16` uses two-byte alignment.

Broad records contain only address, value, representation, width, and region
metadata. They contain no context bytes, hashes, or pointer analysis.

The default candidate limit is unlimited. A nonzero `-MaxMatchesPerValue` is an
explicit resource control; exceeding it produces `CANDIDATE_LIMIT_EXCEEDED`,
never a falsely complete result.

## Differential comparison

`compare_stack_captures.py` reads legacy schema 1 and lightweight schema 2.
Transition evidence, address continuity, move stability, merge return, region,
and relative region offset drive first-pass ranking. Legacy context remains
optional. The output provides `topCandidates` and `targetedContextAddresses`.

## Targeted context capture

After comparison, pass a small set of ranked addresses to:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackCandidateContextCapture.ps1 -Addresses 0x12345678,0x23456789 -Phase split -ExpectedValues 13,24
```

Only this stage reads `±0x40` context, converts it to hex, calculates raw and
amount-normalized hashes, and classifies pointer-like fields and region data.

## Progress and metrics

Progress is rate-limited to approximately once per second and reports label,
regions complete/total, scanned/total MiB, count per target, and elapsed time.
Capture JSON records enumeration, scan and total milliseconds, bytes, regions,
chunks, read failures, failed bytes, throughput, and per-target counts.

Individual raced or unreadable chunks are counted and skipped. Final capture
and manifest files are written through same-directory temporary files and moved
into place. Ctrl+C before finalization therefore cannot register a partial scan
as completed; an unregistered `.tmp` may remain and is safe to remove later.

## Safety

Both tools open the process with query/read access only. They do not write
memory, inject, hook, patch, guard pages, set breakpoints, or mutate inventory,
players, saves, or multiplayer state.

## Test flow

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackAmountDifferentialCapture.ps1 -Label baseline -Values 37
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackAmountDifferentialCapture.ps1 -Label split -Values 13,24
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackAmountDifferentialCapture.ps1 -Label move -Values 13,24
powershell -NoProfile -ExecutionPolicy Bypass -File tools\ItemObserver\Invoke-StackAmountDifferentialCapture.ps1 -Label merge -Values 37
python tools\ItemObserver\compare_stack_captures.py
```

Repeat with different quantities in a second baseline-created session before
calling any address or field proven.
