# Semantic Action Dispatcher Static Map v1

## Scope

Offline-only analysis of Enshrouded revision `1076226`, executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
The scanner reads the on-disk PE and previously validated static maps. It does
not attach to a process, scan process memory, invoke game code, install a
detour, or write any runtime state.

## Proven anchor and wrapper hypothesis

The build-locked InventoryTransferAction consumer is
`0x371810..0x37229F`. At its entry:

```text
0x37182C  mov rsi,[rdx+0x10]
0x371830  mov r12,rcx
0x37184D  mov rcx,[rdx+0x38]
0x371842  mov eax,[rsi+0x08]
0x371869  mov [rcx+0x20],eax
```

The payload at `RSI+0x08` matches all fields of the reflected 0x20-byte
`InventoryTransferAction`, and its downstream slots/amount reach the proven
inventory primitive. This remains `PROVEN_BUILD_1076226`.

The surrounding object is only an **INFERRED dispatch/envelope shape**:
`dispatchContext (RDX) + 0x10 -> RSI`, then `RSI + 0x08 -> payload`. The eight
bytes before the payload, wrapper type/length metadata, allocation site,
enqueue site, and producer copy are not established by the current static
evidence. No function call or copy has been promoted as the wrapper producer.

## Dispatch graph

The consumer branches by the action type byte and calls:

```text
0x37200D -> 0x386180 (type == 3)
0x372020 -> 0x385D80 (accepted non-3 path)
0x3860A7 / 0x38613A / 0x386365 -> 0x3883C0
```

These are downstream inventory paths. Their presence does not identify a
generic action dispatcher or imply that create-building and stock-cycle
actions share the same wrapper.

## Consumed-version cluster

Reflection places the server-only consumed versions at `+0x20`
(`consumedInventoryTransferAction`), `+0x30`
(`consumedCreateBuildingItemAction`), and `+0x40`
(`consumedBuildingStockCycleAction`). The inventory consumer proves one
`+0x20` copy at `0x371869`, but the bounded connected-code analysis found no
single data-flow-proven base that accesses all three offsets. Other equal
displacements occur in stack locals or helper functions and are not promoted
to `ServerConsumedPlayerInput`.

## Sibling action result

`CreateBuildingItemAction` (0x0C; version/index/item ID at +0/+4/+8) and
`BuildingStockCycleAction` (0x14; version/material IDs at +0/+4/+8/+C/+10)
remain **UNSOLVED** as native consumers. No sibling is identified solely from
payload size or generic three-field accesses. There is no safe observer in
this milestone. `UiCreateBuildingItemEvent` remains unconnected.

The reflected `ClientPlayerInput` offsets are known (`+0x000`, `+0x0A4`,
`+0x1B0`), but the connected code does not establish a multi-field base at
those offsets. Live owner identity remains **UNSOLVED**.

## Rejected and unresolved transitions

* Generic `[base+0]/[base+4]/[base+8]` routines are **DISPROVEN** as action
  identity evidence without a dispatch/data-flow edge.
* A lone `+0x20` version write is **INFERRED_ONLY**, not proof of the reflected
  server owner.
* The first unresolved transition is still `dispatchContext+0x10 -> RSI` at
  `0x37182C`.
* Wrapper allocation/lifetime, producer/copy path, genericity, create/stock
  sibling dispatch, and UI-to-input linkage remain unresolved.

Because no CreateBuildingItemAction consumer is strongly established, the
optional runtime observer is disabled and fail-closed. The deployed DLL and
all proven runtime behavior remain unchanged.

