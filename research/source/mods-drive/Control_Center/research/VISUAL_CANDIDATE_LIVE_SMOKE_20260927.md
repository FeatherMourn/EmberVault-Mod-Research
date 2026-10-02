# Visual candidate live smoke attempt — 2026-09-27

The `visual_candidate_159b_1076226` read-only probe was staged under the
reversible isolated smoke profile while the game was closed. The game process
started and was responsive during the first observation window, then exited.

Result:

- No new or updated EML log was observed.
- The existing log remained at its pre-run timestamp and size.
- No dependency or probe output was captured.
- No visual substitution claim can be made.
- The isolated profile was restored and the staged probe was moved to a
  recoverable research staging archive.
- The normal live mod set was restored; no gameplay files were changed.

Classification: `inconclusive` / `runtime-unverified`.

The next live investigation should focus on why launching the executable
directly did not produce a fresh EML log, using the normal Steam launch path or
an already-supported launcher invocation. It must preserve the same isolation
and rollback gates.
