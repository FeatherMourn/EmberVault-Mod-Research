# Building and placement pipeline — revision 1076226

- Topic: building / placement / snapping
- Status: strongly supported static map; runtime authority remains partly unresolved
- Confidence: medium-high for listed instruction/data flow, medium for semantic names
- Build: revision `1076226`
- Executable SHA-256: `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`

## Supported conclusion

The researched placement path enters `0x3E2CD0` from `0x280F86` with an input transform/context structure and an owner/context argument. The routine resolves records through `0xCA90E0` and `0xCB4B50`, performs vector/scalar arithmetic and coordinate integerization, then dispatches a `BuildingPlaceEvent` through `0x3EBB70`. The static maps identify instruction-backed field flow for position, orientation, volume bounds, material, tracking identity, and owner.

The `CreateBuildingItemAction` layout is statically established for this build as a 0x0C structure containing version data, selected index, and item ID. Its relationship to the transient native dispatch consumer and the final placement resolver is not established.

## Important negative result

Changing the local fifth argument at the `BuildingPlaceEvent` helper did not change committed world geometry in the recorded v0.31 experiment. That local argument is therefore disproven as the world-geometry authority for this build and should not be treated as a reliable modding control point.

## Evidence

- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/BuildingSnap-StaticMap-v1.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/BuildingCommitTransform-StaticMap-v1.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/BuildingIdentityAuthority-StaticMap-v1.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/CreateBuildingItem-StaticMap-v1.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/BuildingKfcIngestion-1076226.md`

## Modding implications

Static mapping can identify candidate inputs and downstream consumers, but it does not establish a safe supported hook. Native/runtime changes must remain build-specific, fail closed, and be validated in a disposable world. Data ingestion is a safer route for cataloging building identities and snap/configuration relationships than assuming event arguments control final geometry.

## Open questions

- What transient consumer connects `CreateBuildingItemAction` to the placement resolver?
- Which runtime record is authoritative for selected blueprint identity?
- Which preview/snap winner writeback becomes the committed placement input?
- Can the pipeline be observed reproducibly across later builds?
