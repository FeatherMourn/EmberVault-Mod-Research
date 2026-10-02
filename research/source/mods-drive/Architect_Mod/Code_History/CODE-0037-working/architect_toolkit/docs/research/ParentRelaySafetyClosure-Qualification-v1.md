# CODE-0005E relay safety closure

This is an offline/staging-only qualification. The parent-call relay remains
uninstalled and the deployed runtime is unchanged.

The relay publication model uses eight fixed power-of-two slots with monotonic
64-bit generations, per-slot publication state, and a nonblocking busy/drop
policy. It stores only scalar buffer/frame/argument values. A downstream matcher
accepts exactly one coherent, unconsumed candidate and requires the established
RBP/RSP equations, `0x280F8B` stack marker, same stack-allocation identity,
guarded buffer reads, and an unchanged generation after reads. Zero or multiple
matches are rejected; stale and cross-stack candidates cannot be accepted by
the synthetic model.

The matcher reports `downstreamSnapshot38` and `downstreamSnapshot78` only as
downstream snapshots. Their post-consumer value stability remains unproven.

The helper entry's first flag-defining comparison occurs after the copied entry
prologue, so LOCKed publication operations are conditionally safe for this
site-specific contract. This is not a universal flags guarantee. Unwind and
exception behavior for the dynamic relay island remains unresolved, as does
production worker/drain integration. The final result is
`PARTIAL_STATIC_OR_HARNESS`; `installNow=false` and
`gameHookInstallAuthorized=false`.
