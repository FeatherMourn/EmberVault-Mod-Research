# Architect Toolkit native runtime v0.37.0 (OBSERVE-ONLY)

CODE-0021 adds a fail-closed PlayerObserver scaffold and atomically publishes
`bridge/player_state.json`. No local-player identity or health, stamina, or mana
observation point is proven, so all values remain `UNSOLVED`/`null` and no new
game hook is installed. F7 exposes the read-only `player.inspect` command while
all mutation controls remain disabled.

Historical observer notes below describe the prior read-only Semantic Action Observer. The existing
`BuildingPlaceEvent` hook now also publishes bounded worker-thread JSONL records
to `bridge/semantic_actions.jsonl`; semantic health is atomically published to
`bridge/semantic_action_status.json`. Every raw hook event is retained and now
includes its sequence, tick, thread, transform payload, context, hook/caller
evidence, and neutral candidate-pair correlation. Permanent mapping confidence
is reported separately from runtime hook lifecycle state, so a clean unload does
not erase a proven mapping. Inventory transfer, create-building-item,
and material-cycle hooks remain disabled and `UNSOLVED` because no safe native
execution signatures have been proven. See
`docs/research/SemanticActionObserver-v5.md`. It extends the build-locked,
observe-only `InventoryMovePointerProbe` at current RVA `0x388453`. The probe
copies only the candidate pointer's three reflected ItemStack-sized dwords and
captures the proven transfer amount and destination SlotId derivation, and adds
bounded source-stack/SlotId pre/post candidates recovered from validated caller
data flow. Inventory ownership remains explicitly unresolved.

The deployed v0.31 build preserves the working F8 UI and Lua backend. Ordinary
**Place** opens a bounded trace window; it does not arm an item substitution.

## v0.21 static action milestone

The v0.21 research pass adds no runtime hook or action observer. The reflected
`CreateBuildingItemAction` layout is recorded offline, and the bounded static
map is emitted to `bridge/create_building_item_static_map.json`. Because the
executable currently provides only generic complete-field shape matches—not a
validated action-specific consumer/data-flow boundary—the native observer stays
disabled and fail-closed. The deployed v0.20 DLL is not replaced by this
research pass. Future `create_building_item_action` records are understood by
the offline SemanticCaptureAnalyzer, but none are claimed until a safe native
site is proven.

The runtime installs only when its unique `BuildingPlaceEvent` function signature and expected event-allocation sequence both match. It validates optional context, position/orientation, volume, and caller-memory reads with `VirtualQuery` and SEH before recording them. Any failed read is omitted from the trace.

Each captured event records original item ID, caller/return address and caller RVA, thread ID, tick timestamp, pointers, material/grid/orientation/volume data, a 128-byte context snapshot, direct item-ID offsets in that snapshot, a 48-byte call-site window, eight stack frames, and at most eight one-level context-child snapshots of 64 bytes each. A strict JSON preflight validates each JSON document before atomic publication. Trace storage is capped at 16 events and the runtime log is capped at 128 KiB. Hook bytes are restored on clean unload.

The dedicated `context+0x48` child record snapshots 256 bytes, captures fields `+0x1C` and `+0x30` before and after forwarding unchanged placement arguments, and follows at most six aligned child pointers one more level. `bridge/upstream_trace.json` summarizes this lineage and field stability across ready events.

Use a test world for the historical observer workflow. Start the runtime and confirm the current identity. Move one known
count-37 stack through `37 -> split 13/24 -> move 13 -> move 24 -> merge 37`,
then perform one ordinary Construction Hammer placement. Send
`bridge/semantic_actions.jsonl`, `bridge/semantic_action_status.json`,
`bridge/building_capture.json`, `bridge/upstream_trace.json`,
`bridge/native_status.json`, and `bridge/native_runtime.log`. No inventory or
placement-selection mutation is claimed by this diagnostic.

## v0.24 semantic building catalog

The F8 shell includes a `Build Catalog` tab backed by the offline
`bridge/build_catalog.json` export. It is read-only: searching or selecting a
row only displays locally indexed identity, classification, blueprint,
recipe, material, and evidence fields. It never submits an action or changes
the game's selected build item. Snap data is exposed through
`bridge/snap_rule_catalog.json`; the verified v0.24.1 bundle supplies seven
families and 31 rules. Any fields or families not present in source remain
explicitly unavailable rather than fabricated.

## v0.29 Structure Recorder

The F8 **Structure** tab provides a capture-only recorder. It ingests committed
`building_place` events from `bridge/semantic_actions.jsonl`, collapses only
proven logical placement pairs, and saves validated
`blueprints/recorded/*.architect.json` files. Raw transforms and IDs remain
separate from derived local positions and aggregate volume bounds. Loading is
inspection-only; replay and placement are not implemented.

## v0.30 Structure Editor

The **Plan** tab and `tools/StructureEditor/plan_cli.py` provide an offline
`architect.placement_plan.v1` workflow derived from recorded structures.
Translation, rotation, pivot/origin management, enable/disable,
duplicate/delete, reorder, material planning, Layout Mirror (Experimental),
and bounded undo/redo operate only on JSON plans. No plan action submits a
bridge placement command or modifies game memory.

## v0.31 Experimental Single Placement Carrier (retired)

The v0.31 local tracking-item carrier is retained only as historical evidence.
The live wall-versus-foundation test proved that changing the helper argument
does not control committed geometry. The legacy arm command is disabled and
fails closed in v0.32; no placement argument or game memory is written.

## v0.32 Upstream Placement Identity Authority

Build ID: `architect-v032-identity-authority-20260915-a`  
Mode: `observe_only_placement_blueprint_authority`

The stable `BuildingPlaceEvent` observer and static upstream research remain
available. The first unresolved boundary is the producer coupling selected
building identity to runtime blueprint occupancy and commit volume. See
`bridge/building_identity_authority_static_map.json`.

The Plan tab exposes **Experimental Single Placement** behind an explicit TEST
WORLD acknowledgement. It accepts exactly one enabled Foundation 4m plan entry
(`950598916`) and arms a bounded two-stage state machine (10-second wait for
the first event, then a 250 ms matching raw-event window). The stable
`BuildingPlaceEvent` hook substitutes only the local tracking-item argument
before forwarding the original helper call; vanilla position, rotation,
bounds, owner, material, resolver tables, ItemInfo, and context memory remain
unchanged. The local value is restored immediately after return. Ordinary Place
remains trace-only, and this feature is **not proven** until a disposable world
shows the intended resulting geometry. See
`docs/research/SinglePlacementCarrier-v1.md`.

The initial live wall-versus-foundation test forwarded and restored the
Foundation ID successfully, but the committed world geometry remained the
wall. The local tracking-ID mutation is therefore
`DISPROVEN_BUILD_1076226` as a geometry selector and is not to be retested.
