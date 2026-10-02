# CODE-0006 — snap winner / preview writeback static map

The four known `0x3E79C0` callers remain split across two post-filter
families. `0x3EB810` receives caller-owned storage and count, walks every
0x50-byte accepted element, applies a per-element predicate, and invokes
`0x99ECF0`, `0x8CD2C0`, and `0x3E5480`. At `0x3EB84E`, R8 receives the
accepted-element pointer; at `0x3EB872`, R9 receives the element-derived
`[RDI+0x48]`; and at `0x3EB893`, that value is copied to `[RSP+0x90]` before
the helper call. It advances through the complete list; no best-index, score
comparison, min/max replacement, or retained winner was found in the bounded
function.

`0x99F970` consumes one caller-derived record through RDI and reads fields at
`+0x14`, `+0x1C`, `+0x20`, `+0x28`, `+0x2C`, `+0x34`, `+0x38`, and `+0x40`.
Its arithmetic/minimum operations are internal to that one input record; no
accepted-list traversal or candidate-to-candidate choice is proven.

Both families therefore classify as
`NO_WINNER_SELECTION_IN_BOUNDED_PATH`. Outputs are stack-local or
callee-dependent, so persistent owner/writeback is
`UNSOLVED_NOT_PERSISTENCE_PROOF`. The downstream helper `0x3E5480` calls
`0x3ED1A0` and writes through its returned pointer at `0x3E5583..0x3E55E6`,
but destination owner, lifetime, and preview meaning are unresolved. No
instruction-backed edge to preview state, blueprint authority,
CreateBuildingItemAction, or the `0x3E2CD0` commit inputs was established.

The artifact is offline-only with `installNow=false` and
`gameHookInstallAuthorized=false` and current-source designation is also
unauthorized. No runtime hook or deployment change was made.
