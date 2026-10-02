# Build Selection Static Map v1

**RESEARCH / OFFLINE STATIC ONLY.** The reflected `CreateBuildingItemAction`
layout and `ClientPlayerInputData+0x1B0` placement are proven, but no connected
native consumer establishes that this action feeds the live build-selection
state. The context child IDs and R12 chain are recorded as neutral evidence.

No pre-placement callback or safe selection-change observer is installed. The
first unresolved boundary is input/UI selection state to the native
blueprint/cache record.

The v0.31 helper-argument mutation remains permanently disallowed: it was
writable and pair-safe, but committed geometry stayed Wall Straight 4m.
