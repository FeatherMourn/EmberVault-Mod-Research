# F8 backend protocol (offline definition)

The versioned operation vocabulary is defined in
`tools/ArchitectVoxel/f8_protocol.py`. Existing support is intentionally kept
separate from proposed operations:

| Operation | Status |
| --- | --- |
| `preview` | supported by existing backend path |
| `place` | supported by existing backend path |
| `cancel` | supported by existing backend path |
| `select_carrier_shape` | unsupported in the current runtime |
| `generate_shape` | unsupported in the current runtime |
| `rotate` | unsupported in the current runtime |
| `mirror` | unsupported in the current runtime |
| `material_change` | unsupported in the current runtime |
| `apply_to_architect_carrier` | experimental and disabled; no carrier swapping is claimed |
| `single_placement_carrier_arm` | EXPERIMENTAL; one Foundation 4m semantic argument substitution only |
| `single_placement_carrier_cancel` | EXPERIMENTAL; clears the one-shot arm |

Commands carry `protocolVersion` and an operation-specific payload. Unsupported
operations fail validation locally; this document does not add handlers,
bridge writes, or claims of runtime support.

Future procedural controls are defined offline as `shape`, `radius`, `width`,
`height`, `hollow`, `thickness`, `axis`, `rotate`, `mirror`, `material`, and
`preview`, with carrier application explicitly experimental/unsupported until
a separate safety review.

The v0.24 Build Catalog is a UI-only read path. Its neutral
`ArchitectBuildSelection` contains ItemId/GUID/classification/material,
blueprint identity, and snap identity with `backendStatus =
"read_only_catalog"`; selecting a row emits no bridge command and does not
change the game's active build item.

Structure Recorder actions (`start_recording`, `stop_recording`,
`cancel_recording`, `save_recording`, `load_recording`) are UI-local capture
operations. They read the existing semantic placement stream and write only
versioned `.architect.json` inspection files; no action produces a placement or
replay command.

The v0.30 Plan tab is likewise UI-local. `plan_cli.py` creates and edits
`architect.placement_plan.v1` JSON only; translation, rotation, mirror,
material planning, and undo/redo are offline operations. Runtime protocol
operations remain explicitly unsupported.

The v0.31 carrier commands are intentionally narrow. An arm payload carries
`backendItemId=950598916`, one `planPlacementId`, and
`materialMutationEnabled=false`. It uses the next legitimate vanilla
placement's transform and never replays plan coordinates. Native status is
published at `bridge/single_placement_carrier_status.json`; a written argument
is capture evidence, not proof of world authority.
