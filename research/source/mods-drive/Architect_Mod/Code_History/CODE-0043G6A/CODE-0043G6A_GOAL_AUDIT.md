# CODE-0043G6A — Goal audit / pre-runtime findings

Date: 2026-09-21
Build scope: Enshrouded 1076226

## Purpose

Start G6A — first live F7 capability proof — from the existing CODE-0033 movement + stamina correlation harness.

This audit intentionally does NOT authorize deployment or mutation.

## Current authoritative baselines

Loose F7 runtime:
- 449783 bytes
- SHA-256 `9EF34615CD233BFBA2AFB885C7EA84D71343E019F4FA1647B93C004AC42585E9`

Registry:
- 60272 bytes
- SHA-256 `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`
- 55 total / 17 enabled / 38 disabled / 55 unique

Current ZIP:
- 61956660 bytes
- SHA-256 `A1AB3AEEE18987C0F4F27CC0B49A371C89F3F82BE5EC8342BD9536B86516835A`

Build fingerprint:
- revision 1076226
- executable SHA-256 `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`
- timestamp `0x6A4236C8`
- image size `0x02DA7000`

## Existing CODE-0033 intent

The packaged research document describes:
- observe-only movement probe at RVA 0x23AE34
- observe-only stamina probe at RVA 0x23423F
- exact build/signature/displaced-byte gates
- fixed 512-record memory ring
- bounded 1 MiB JSONL
- clean hook uninstall/byte restore
- eight named runtime phases
- analyzer gate before any CODE-0034-style mutation work

## Independent pre-runtime blockers

### 1. Native phase contract mismatch

PowerShell/analyzer use:
BASELINE_IDLE, WALK, SPRINT_ACTIVE, SPRINT_RECOVERY, JUMP, POST_JUMP_RECOVERY, COMBAT_IDLE, MENU.

Packaged native `cc_phase_valid` currently accepts only:
BASELINE_IDLE, ACTIVE, MENU.

Therefore the documented live procedure is not qualified as-is.

### 2. Correlation command envelope is falsely marked mutating

Current `Publish-CheatCorrelationCommand` initializes:
- readOnly = false
- mutationRequested = true

That contradicts the registry and CODE-0033 research contract for `cheatcorrelation.*`.

Because the same transport is also used by mutation cheats, the correction must be conditional to correlation actions only.

### 3. F7 only exposes Begin + Status

Current responsive `Render-DiagnosticsPage` has canonical controls for:
- cheatcorrelation.begin
- cheatcorrelation.status

It does not expose:
- cheatcorrelation.mark
- cheatcorrelation.end

G6A therefore needs a bounded phase selector + Mark + End control surface before the full test can honestly be called F7-operable.

### 4. Bundled correlation report is stale staging output

The Current ZIP contains a historical report showing movement NO_SAMPLES and stamina AMBIGUOUS with 512 samples.

It is not a fresh G6A run and must not be treated as new runtime evidence.

## Safety/deployment boundary

The local/game-drive Architect installation is intentionally absent.

G6A Gate A must:
- work in TEMP / I: source / Code_History
- produce an offline-qualified candidate
- not recreate H:
- not deploy
- not replace Current ZIP
- not claim runtime proof

User runtime execution is a separate Gate B after explicit redeployment.

## Goal disposition

Proceed with CODE-0043G6A as:
1. CODE-0033 contract repair/qualification,
2. F7 research control completion,
3. exact runtime-test candidate packaging,
4. user runtime capture gate,
5. analyzer-driven mutation decision only after evidence.

This does not change the current evidence status of movement, stamina, local-player ownership, or gameplay mutation.
