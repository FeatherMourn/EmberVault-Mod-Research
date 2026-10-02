# CODE-0005A — observer infrastructure (offline/staging only)

This delivery is an infrastructure capability exercise, not a game-hook
authorization.  The CODE-0005 parent remains `NO_SAFE_OBSERVER_SITE` and the
deployed runtime is not rebuilt or replaced.

## Planner

`build_observer_relocation_plan.py` decodes from an explicit PE RVA or a caller
supplied byte buffer with Capstone.  It accumulates complete instructions until
the configured patch encoding minimum (12 bytes for the existing absolute
jump encoding), records the exact span and continuation, and hashes the
canonical plan.  A caller-supplied CFG edge list is required to reject an
external branch entering the middle of the span; no process scan is performed.

Only ordinary non-RIP-relative byte copies are harness-proven. RIP-relative
memory and direct CALL/JMP/Jcc are rejected until a semantics-preserving
relocator is reviewed.  Consequently the CODE-0005 candidates containing
relative calls, branches, or split fixed spans remain blocked.

## Native staging capability

`ArchitectObserverTrampoline.*` is a synthetic byte transaction with expected
byte checking, backup, exact restoration, duplicate-install rejection, and
fail-closed mismatch behavior. It has no module lookup, executable allocation,
process access, or game target.  `ArchitectObserverDiagnostics.*` is a fixed
64-event SPSC ring of scalar records. The producer performs bounded stores only;
it does no I/O, allocation, waits, formatting, locks, or game calls. Overflow
drops the newest event and increments a counter. Drain/formatting is outside
the producer. Multi-producer and reentrant site use are not claimed.

The wrapper contract is intentionally narrow: no generic game wrapper or
register/flags-preserving assembly thunk is installed. Generic RFLAGS,
nonvolatile/vector preservation and Windows unwind behavior therefore remain
unresolved. The production drain host is also unresolved.

## Requalification

The generated delta consumes the CODE-0005 map and capability map but keeps all
sites `NOT_QUALIFIED`, `installNow=false`, and
`gameHookInstallAuthorized=false`. Harness success is not game safety proof.

