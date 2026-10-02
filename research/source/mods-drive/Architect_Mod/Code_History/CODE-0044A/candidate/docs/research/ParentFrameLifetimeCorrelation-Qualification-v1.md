# CODE-0005D — parent-frame lifetime and correlation qualification

The bounded interval from `0x2807C8` through `0x280F86` contains no decoded
writes to RSP or RBP. This supports a static equality result for the effective
parent stack pointer and the established RBP relation, but it does not prove
the dynamic allocation size or that the buffer fields are in-bounds.

The retained equations are:

```text
parent RSP       = RBP - 0x100
relay entry RSP  = RBP - 0x108
buffer           = RBP - 0x30 = relay entry RSP + 0xD8
buffer + 0x38    = relay entry RSP + 0x110
buffer + 0x78    = relay entry RSP + 0x150
```

They remain hypotheses until a reviewed runtime stack-range check can validate
them. The interval has no direct writes whose addresses are syntactically
`[RBP+0x08]` or `[RBP+0x48]`, but those values are passed through aliases and
calls (including uses around `0x280945` and `0x280B23`). Callee side effects
are not bounded, so both fields are classified
`ALIAS/CALLEE_SIDE_EFFECT_UNRESOLVED`; absence of a static write is not
immutability proof.

The proposed stable-hook gate requires coherent relay generation, consume-once
semantics, RDX/RBP arithmetic agreement, the `0x280F8B` stack marker, same-stack
allocation validation, and guarded field reads. Race, reentrancy, unwind, and
production drain integration remain unresolved. The result is
`PARTIAL_STATIC`; `installNow=false` and `gameHookInstallAuthorized=false`.
