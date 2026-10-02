# CODE-0033 — Movement + Stamina Live Correlation Sprint

## Implementation status

`DUAL_CORRELATION_HARNESS_READY`

Architect Native Runtime v0.39.0 contains two dormant, command-gated, observe-only probes for revision 1076226. Neither is installed until `cheatcorrelation.begin`. Each probe independently requires the canonical build fingerprint, PE timestamp `0x6A4236C8`, image size `0x02DA7000`, one exact signature match at its expected RVA, and exact displaced bytes.

The movement probe starts at RVA `0x23AE34` and replays a 16-byte whole-instruction span. It records the known integration context, original accumulator/operand, `xmm3` input bits, thread, caller, and phase. It does not write velocity.

The stamina probe starts at RVA `0x23423F` and replays its 22-byte whole-instruction span. It records the naturally computed base, selector, addressed cell, current `int32` value, thread, caller, and phase. It does not read unknown adjacent fields and does not write the attribute.

Both hot hooks publish only into a fixed 512-record in-memory ring. The worker thread writes bounded JSONL, capped at 1 MiB. Ending the capture restores the exact original instruction bytes and flushes the instruction cache. If one probe fails validation, the other remains usable.

## Commands and phases

- `cheatcorrelation.begin`
- `cheatcorrelation.mark` with `BASELINE_IDLE`, `WALK`, `SPRINT_ACTIVE`, `SPRINT_RECOVERY`, `JUMP`, `POST_JUMP_RECOVERY`, `COMBAT_IDLE`, or `MENU`
- `cheatcorrelation.status`
- `cheatcorrelation.end`

The F7 Research page publishes these commands with `readOnly: true` and `mutationRequested: false`.

## One-session procedure

1. Restart Architect and Enshrouded; verify `cheat_correlation_status.json` reports build supported.
2. In F7 Research, begin movement/stamina capture.
3. Mark `BASELINE_IDLE`; stand still five seconds.
4. Mark `WALK`; walk normally five seconds.
5. Mark `SPRINT_ACTIVE`; sprint until stamina visibly drains.
6. Mark `SPRINT_RECOVERY`; stop until stamina substantially recovers.
7. Mark `JUMP`; jump several times.
8. Mark `POST_JUMP_RECOVERY`; return to idle.
9. End capture. Open and close F8 once, then exit normally.
10. Run `python tools/CheatCorrelation/analyze_capture.py`.

Return `bridge/cheat_correlation_status.json`, `bridge/cheat_correlation_capture.jsonl`, `bridge/cheat_correlation_report.json`, `bridge/native_status.json`, and `bridge/native_runtime.log`.

## CODE-0034 gate

CODE-0034 is justified only when the analyzer reports `CONVERGED` for at least one family. Movement requires one dominant context across idle and multiple active phases without multi-entity contamination. Stamina requires one stable context/selector whose value decreases during `SPRINT_ACTIVE` and increases during `SPRINT_RECOVERY`. A converged stamina scalar is preferred over an instruction patch.
