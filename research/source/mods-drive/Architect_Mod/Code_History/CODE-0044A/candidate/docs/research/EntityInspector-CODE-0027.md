# CODE-0027 — F7 Entity Inspector / Target Resolver

## Conclusion

`NO_SAFE_TARGET_PATH_CONVERGENCE`

CODE-0027 adds reusable, read-only Entity Inspector state, command routing, bounded capture markers, and F7 registry entries. It installs **no target hook**, performs **no pointer walk**, makes **no physics call**, and exposes **no mutation command**. The exact build-1076226 fingerprint is still required before the module accepts commands.

## Static candidate table

| Priority | Candidate | Reflection evidence | Function RVA / signature | Result |
|---:|---|---|---|---|
| 1 | `keen::ecs::ClientCursor` (index 2842, size 4328) | `hoveredVoxelMaterialId` +138; `previousSelectedEntityId` +192; primary/secondary transforms | Not established | Best vanilla highlight/build cursor lead; static layout only |
| 1 | `keen::ecs::ClientCursorInput` (2766, 160) | Cursor input owns selection-oriented state | Not established | Producer/consumer and live instance unresolved |
| 1 | `keen::ecs::CursorSelectObjectAction` (2670, 24) | `selectedObjectId` +8 | Not established | Concrete identity-shaped action field; submission/consumption unresolved |
| 3 | `keen::ecs::TargetEntity` (710, 4) | `targetId` +0 | Not established | Semantics and owner unresolved |
| 3 | `keen::ecs::TargetPosition` (711, 12) | `targetPosition` +0 | Not established | No proven relationship to aimed entity |
| 4 | `keen::ecs::DebugHitResult` (3418, 44) | Hit-shaped reflected type | Not established | Generic hit metadata is insufficient |
| 4 | `keen::ecs::InteractionQuery` (3697, 20) | Query-shaped reflected type | Not established | No proven result path |

The deterministic source is `bridge/entity_inspector_static_map.json`, produced by `python tools/EntityInspector/analyze_entity_targeting.py`. The analyzer validates executable SHA-256 `AF2F...0781`, PE timestamp `0x6A4236C8`, image size `0x2DA7000`, and each reflected index/size/field offset before emitting the map.

## Selected vanilla path

The selected research family is `ClientCursor / CursorSelectObjectAction`, because vanilla reflection explicitly associates it with hover and object selection. This is not yet a selected runtime function. No relocation-aware evidence currently connects the descriptors to a unique producer, consumer, live ECS component instance, or stable target-publication boundary. Therefore RVA, signature, calling convention, arguments, return layout, caller graph, and overwrite span remain `UNSOLVED`.

## Hook safety

Canonical build validation is available. Every remaining hook condition fails closed: no exact target-site signature, unique match, understood function boundary, understood arguments/result, or relocatable overwrite span exists. No hook is installed and no uninstall work is needed beyond normal module shutdown. Existing Building, Inventory, Player, PlayerDiscovery, SemanticAction, and GameSettings behavior is unchanged.

## Target result and identity findings

`bridge/entity_inspector_state.json` contains only justified fields. Target status is `UNSOLVED`; identity, resource, pointer, type, name, position, and rotation are null; authority is `UNKNOWN`; components are empty. Null values are intentional and are never rendered as fake zeroes.

- Stable entity/resource identity: `UNSOLVED`.
- Transform: `UNSOLVED`; reflected cursor transforms are not proven target transforms.
- Component enumeration: `UNSOLVED`; no bounded validated ECS registry query is mapped.
- Authority/network identity: `UNSOLVED`; no client/server/owner inference is made.
- Classification: `UNKNOWN`; no guessed class rules exist.
- Player synergy: no validated target-to-player ECS relationship yet.
- Building synergy: preserved cursor/build reflection evidence, without changing placement hooks.

## F7 and bridge integration

The registry-driven Inspector / Diagnostics category adds `entity.inspect`, `entity.inspect.clear`, `entity.capture.begin`, `entity.capture.mark`, and `entity.capture.end`. Clear affects only Architect diagnostic state. The PowerShell dispatcher allowlists these commands, marks them read-only, rejects mutation/unknown commands, and publishes `bridge/entity_inspector_command.json`.

Runtime state is published atomically to `bridge/entity_inspector_state.json`. Optional research events use `bridge/entity_inspector_capture.jsonl`, bounded to 64 records and 262,144 bytes. Markers are allowlisted target-class labels and carry no target claim when the resolver is unresolved.

## Runtime test

After deploying the rebuilt DLL, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\EntityInspector\Invoke-EntityInspectorRuntimeTest.ps1
```

The operator sequence covers no target, building, harvestable, container, crafting station, friendly NPC, enemy, dropped item, player, travel/return, then clean capture end. With zero probe installed, the expected result is bounded markers plus null target observations; any non-null target would be a failure of the current evidence contract.

Return these files after runtime testing:

- `bridge/entity_inspector_state.json`
- `bridge/entity_inspector_capture.jsonl`
- `bridge/native_status.json`
- `bridge/native_runtime.log`

## Remaining boundary and next feature

The first unresolved boundary is the current-build producer/consumer of `CursorSelectObjectAction.selectedObjectId` or writer of `ClientCursor.previousSelectedEntityId`, followed by a validated ECS entity lookup and lifetime contract. The recommended next feature is a narrowly scoped offline xref/data-flow recovery of those exact two fields. Mutation, custom raycasting, transform reads, component enumeration, and authority claims remain blocked.
