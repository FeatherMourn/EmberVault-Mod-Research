# Semantic Action Observer v0.23.0 — dispatcher-family milestone

This milestone follows the proven InventoryTransferAction consumer instead of
brute-forcing ClientPlayerInput heap objects. The result is static-only and
preserves the stable inventory, placement, and F7/F8 runtime behavior.

`0x371810..0x37229F` remains a proven InventoryTransferAction consumer. Its
entry loads `RSI=[RDX+0x10]`, consumes the action at `RSI+0x08`, copies the
version to `[RDX+0x38]+0x20`, and dispatches type-specific inventory handlers.
This supports an inferred envelope/wrapper shape but does not establish its
producer, allocation, lifetime, or genericity.

The reflected sibling layouts are exact: CreateBuildingItemAction is 0x0C
with item ID at +0x08, and BuildingStockCycleAction is 0x14 with material IDs
at +0x04/+0x08/+0x0C/+0x10. No native consumer for either sibling is proven.
The reflected ServerConsumedPlayerInput cluster (+0x20/+0x30/+0x40) has no
single data-flow-proven base in the connected code. ClientPlayerInput remains
static-layout proven but live-owner unresolved.

Accordingly, no new action observer or detour is installed. The generated
`bridge/semantic_action_dispatcher_static_map.json` records the bounded
instruction evidence, rejected candidates, and first unresolved pointer
transition (`0x37182C`).

