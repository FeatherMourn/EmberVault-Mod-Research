# Architect Toolkit — Engineering State (build 1076226)

**Document type: EVIDENCE.** Status vocabulary is deliberately conservative:
PROVEN, PROVEN_STATIC, PROVEN_OFFLINE, INFERRED, EXPERIMENTAL, UNSOLVED,
DISPROVEN, PLANNED, SPECULATIVE.

| System | Status | Evidence / boundary |
|---|---|---|
| Native runtime | PROVEN | Build-locked x64 runtime with identity verification; current mode is observe-only. |
| F7/F8 | PROVEN_OFFLINE | F8/F7 UI and command plumbing operate; unsupported operations remain disabled. |
| Bridge | PROVEN | Atomic JSON bridge/status publication and command acknowledgement. |
| BuildingPlaceEvent | PROVEN | Stable helper hook at RVA `0x3EBB70`; paired event capture on build 1076226. |
| Logical pair correlation | PROVEN_STATIC | Two-event correlation is established for observed client/server setups. |
| Q32.32 placement coordinates | PROVEN_OFFLINE | Recorder preserves raw fixed-point coordinates and deterministic bounds. |
| Structure Recorder | PROVEN_OFFLINE | Capture-only recording, provenance counters, and regression fixtures. |
| Structure Editor | PROVEN_OFFLINE | Plan transforms/history are offline; no runtime replay claim. |
| ArchitectDataIndex | PROVEN_OFFLINE | KFC/resource ingestion and catalog relationship validation. |
| Building-resource ingestion | PROVEN_OFFLINE | Catalog relationships are indexed; native runtime pointer path is unresolved. |
| InventoryTransferAction | EXPERIMENTAL | Read-only observer infrastructure; ownership/authority unresolved. |
| ItemStack | PROVEN_STATIC | First-dword/item-stack evidence; ownership and writes unresolved. |
| Snap static research | PROVEN_STATIC | Candidate filtering and transform maps; no new observer installed. |
| Runtime blueprint research | INFERRED | Record/cache fields and decoder family identified; common commit authority unresolved. |
| Commit transform research | PROVEN_STATIC | `0x3E2CD0` range and event argument flow mapped. |
| Placement identity authority | UNSOLVED | The upstream producer coupling identity to geometry is not proven. |
| CreateBuildingItemAction | UNSOLVED | Reflected layout known; native consumer/dispatch boundary unresolved. |
| Material authority | UNSOLVED | Material reaches commit construction, but authoritative source is not isolated. |
| Transform replay | PROVEN_OFFLINE | Structure Editor transforms are deterministic offline only. |
| Multiplayer authority | UNSOLVED | Client/server observations exist; submission/authority path is not claimed. |
| Target Resolver | UNSOLVED | Reflection candidates (cursor, select-object, focus, hit-shaped records) are catalogued; no live acquisition/publication edge or observer is proven. |

Selected-build identity, runtime blueprint authority, CreateBuildingItemAction
consumer, placement replay, and snap-rule runtime identity are
`PARKED_PENDING_NEW_EVIDENCE`; this milestone did not reopen those branches.

## Permanent negative result

In the v0.31 live test, local `BuildingPlaceEvent.trackingItemId` changed from
Wall Straight `948722226` to Foundation `950598916` for both event members and
was restored. The world still committed Wall Straight. Therefore the local
argument is writable, but helper-argument control of committed geometry is
`DISPROVEN_BUILD_1076226`. Roadmap generators must not recommend that mutation
again without direct contradictory evidence.

The machine-readable source of this state is
`bridge/architect_engineering_state.json`.
