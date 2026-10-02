# Latest Semantic Capture Report

## Session summary

- Current session: `v020-91AF71C-24480`
- Runtime: `0.20.0` / `architect-v020-semantic-observer-20260914-a`
- Build supported: `True`; fingerprint validated: `True`
- Mixed sessions: `False`; clean shutdown: `False`
- Declared events/drops: `None` / `None`

## Session `v020-91AF71C-24480`

Events: 14. Preview/cancel-only candidate: `False`.

### Building operations

- Logical `1`: 2 record(s), payload equal `True`, delta `16` ms, threads `[3640, 25548]`. No side classification assigned.

### Inventory operations

- Event `2` `empty_destination_initialization`: destination `0` + `24` -> `24`, caller `0x38636A`, thread `25548`. merge_count_arithmetic=INSUFFICIENT_EVIDENCE, empty_initialization_arithmetic=SUPPORTED_BY_CAPTURE, destination_stack_address_equation=SUPPORTED_BY_CAPTURE, source_stack_address_equation=SUPPORTED_BY_CAPTURE.
- Event `4` `empty_destination_initialization`: destination `0` + `13` -> `13`, caller `0x38613F`, thread `25548`. merge_count_arithmetic=INSUFFICIENT_EVIDENCE, empty_initialization_arithmetic=SUPPORTED_BY_CAPTURE, destination_stack_address_equation=SUPPORTED_BY_CAPTURE, source_stack_address_equation=SUPPORTED_BY_CAPTURE.
- Event `6` `empty_destination_initialization`: destination `0` + `24` -> `24`, caller `0x38613F`, thread `25548`. merge_count_arithmetic=INSUFFICIENT_EVIDENCE, empty_initialization_arithmetic=SUPPORTED_BY_CAPTURE, destination_stack_address_equation=SUPPORTED_BY_CAPTURE, source_stack_address_equation=SUPPORTED_BY_CAPTURE.
- Event `8` `existing_item_merge`: destination `24` + `13` -> `37`, caller `0x3860AC`, thread `25548`. merge_count_arithmetic=SUPPORTED_BY_CAPTURE, empty_initialization_arithmetic=INSUFFICIENT_EVIDENCE, destination_stack_address_equation=SUPPORTED_BY_CAPTURE, source_stack_address_equation=SUPPORTED_BY_CAPTURE.

### InventoryTransferAction observations

- Operation `1`: type `3`, actionAmountRaw `24`, effectiveTransferAmount `24`, item `Build_TerrainMaterial_T1_Stone`. split_action_amount_equals_effective=SUPPORTED_BY_CAPTURE, source_slot_matches=SUPPORTED_BY_CAPTURE, target_slot_matches=SUPPORTED_BY_CAPTURE.
- Operation `2`: type `2`, actionAmountRaw `0`, effectiveTransferAmount `13`, item `Build_TerrainMaterial_T1_Stone`. operation_type_dependent_amount=SUPPORTED_BY_CAPTURE, source_slot_matches=SUPPORTED_BY_CAPTURE, target_slot_matches=SUPPORTED_BY_CAPTURE.
- Operation `3`: type `2`, actionAmountRaw `0`, effectiveTransferAmount `24`, item `Build_TerrainMaterial_T1_Stone`. operation_type_dependent_amount=SUPPORTED_BY_CAPTURE, source_slot_matches=SUPPORTED_BY_CAPTURE, target_slot_matches=SUPPORTED_BY_CAPTURE.
- Operation `4`: type `2`, actionAmountRaw `0`, effectiveTransferAmount `13`, item `Build_TerrainMaterial_T1_Stone`. operation_type_dependent_amount=SUPPORTED_BY_CAPTURE, source_slot_matches=SUPPORTED_BY_CAPTURE, target_slot_matches=SUPPORTED_BY_CAPTURE.

### CreateBuildingItemAction observations

No create-building-item action records; native consumer observer remains disabled until static proof.

## Caller distribution

- `0x3860AC`: 1
- `0x38613F`: 2
- `0x38636A`: 1

## Warnings

No parser/session warnings.

## Unresolved mappings

- CreateBuildingItemAction native consumer and dispatch boundary
- CreateBuildingItemAction lifecycle (selection/preview/cancel/commit)
- CreateBuildingItemAction.itemId ↔ BuildingPlaceEvent.trackingItemId causality
- client/server side identity
- inventory ownership
- final source post-state when only intermediate snapshots exist
- concrete R14 type unless independently established

## Recommended next evidence

- CreateBuildingItemAction observer is disabled; first resolve its native consumer statically before a live selection/preview/cancel/commit test.
