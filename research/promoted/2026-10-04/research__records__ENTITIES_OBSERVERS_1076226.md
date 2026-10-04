# Entities, observers, and inventory action flow — revision 1076226

- Topic: ECS reflection, cursor/entity discovery, observers, inventory
- Status: strongly supported static findings; safe runtime target not established
- Confidence: high for reflected layouts and decoded field flow; low-to-medium for semantic ownership and hookability
- Build: revision `1076226`
- Executable SHA-256: `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`

## Supported conclusions

The read-only reflection cache establishes relevant `ClientPlayerInput` action layouts, including `CreateBuildingItemAction` and `InventoryTransferAction`. The static inventory-transfer analysis identifies a native consumer region at `0x371810` connected to an action-shaped payload and traces the reflected fields through validation and transfer calls.

For cursor/entity targeting, reflection identifies `ClientCursor`, `ClientCursorInput`, `CursorSelectObjectAction`, `TargetEntity`, and related fields. The descriptor registry relationship is supported for the recorded build, but the research did not recover a typed ECS system, query, action subscription, event subscription, live component instance, or stable target-publication boundary. The result is not a safe target path.

Observer trampoline work is infrastructure-only: it validates planning and fail-closed transaction behavior in staging, not a game hook or authorization to attach to a live process.

## Safety boundary

Reflected offsets and static descriptor addresses are evidence about a specific build, not portable runtime pointers. No native mutation, process access, or live memory write should be inferred from these records. Any future runtime experiment needs an explicit build fingerprint, disposable-world plan, bounded capture, and fail-closed mismatch behavior.

## Evidence

- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/ClientPlayerInput-StaticMap-v1.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/InventoryTransfer-StaticMap-v1.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/EntityInspector-CODE-0027.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/EntityInspector-CODE-0028-CursorDataFlow.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/EntityInspector-CODE-0029-ECSSystemRecovery.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/ObserverTrampolineDiagnosticInfrastructure-v1.md`

## Modding implications

Offline reflection and static mapping are useful for naming candidate fields, designing probes, and validating data-flow hypotheses. They do not yet provide a safe general-purpose entity observer or target resolver. Inventory action analysis is more mature than cursor-target recovery, but remains build-specific.

## Open questions

- Can a later build or controlled runtime capture connect cursor descriptors to an owned ECS system?
- Which owner/root establishes the semantic identity of container slots and generations?
- Can inventory-transfer field flow be reproduced through a supported mod boundary rather than native intervention?
