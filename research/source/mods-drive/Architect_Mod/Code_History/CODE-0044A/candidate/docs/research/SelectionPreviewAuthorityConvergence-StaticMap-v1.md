# CODE-0011 — Selection/preview authority convergence sweep

Status: `E_PARTIAL_STATIC_FRONTIERS_PARKED`, offline/static-only. Build locked
to Enshrouded revision `1076226`, executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
No process, debugger, hook, injection, deployment, or memory write was used.

## Front results

### Front A — VoxelModel/ghost producer

The available ItemInfo/VoxelBlueprint/VoxelModel relationships are resource
evidence only. No building-specific executable VoxelModel resolver, ghost
producer, or preview writer was anchored within two meaningful call/data-flow
hops. Generic renderer/model hits are rejected and this front is parked.

### Front B — snap owner

`0x3E79C0` is instruction-backed. It reads the source collection at
`[RSI+0x110]`, resolves candidate `+0x08` through `0xCA90E0` using cache
`[RSI+0xF0]`, and appends bounded `0x50`-byte accepted records. The accepted
collection is caller/local-owned and persistence is unresolved. RSI similarity
to other functions is not treated as object identity.

### Front C — commit inputs

At `0x280F86`, `R8D` is loaded from `[RBX]` before calling `0x3E2CD0`; the
placement function receives `RCX`/`RDX` and retains them as RSI/R15. These are
proven downstream inputs, but no persistent source owner or connection to the
snap/preview fronts is established.

### Front D — resource identity

Exported ItemInfo, VoxelBlueprint, and VoxelModel relationships provide a
resource-only bridge. They do not prove native runtime authority or a shared
placement owner.

## Convergence graph

The machine-readable graph records anchored functions, owner/field nodes, and
evidence-bearing edges. It classifies the sweep as `NO_CONVERGENCE`: no single
instruction-backed object/field is reached from two target fronts. The apparent
RSI overlap between snap and placement paths is explicitly rejected as
coincidence without runtime object identity.

CODE-0009's `0x3ED1A0` slot family and CODE-0010's CreateBuildingItemAction
consumer branch remain parked. Generic VoxelModel/render searches are also
parked under the two-hop rule. No surviving candidate owner is promoted and
`observerDecision.install` remains false.

See `bridge/selection_preview_authority_convergence_static_map.json` for the
front-by-front evidence, target-property matrix, parked branches, and exact
source-map references.
