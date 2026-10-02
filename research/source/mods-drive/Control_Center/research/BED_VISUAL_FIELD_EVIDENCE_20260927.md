# Bed visual-field evidence — 2026-09-27

## Probe

- Donor GUID: `01474f79-6b5a-4bcd-999d-7e9339fda91c`
- Probe: `visual_field_probe_bed_20260927`
- Resource type: `keen::ItemInfo`
- Session log: `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-27.eml.log`
- Backup: `H:\Enshrouded_ControlCenter_Backups\20260927-visual-field-probe-bed-smoke`

## Observed fields

| Field | Present | Observed value |
|---|---:|---|
| `iconImage` | yes | zero GUID |
| `iconModel` | yes | `4c7f1c3a-b448-4460-ad5e-a79b3859d2c1` |
| `iconScene` | yes | `bb6e4131-f978-4707-bd0c-f573d59b1d37` |
| `visualModel` | no | nil |
| `visualEntity` | no | nil |
| `placedEntity` | no | nil |
| `material` | no | nil |
| `texture` | no | nil |
| `objectId` | yes | donor GUID |

## Interpretation

The furniture donor does not expose the generic `visualModel`, `material`, or
`texture` fields tested by the planner. Its visible representation is more
likely reached through `iconModel`, `iconScene`, and the object/resource graph
behind `objectId`. This narrows the next research probe to those typed resource
families and their donor relationships.

The probe was read-only. It does not prove that replacing `iconModel` or
`iconScene` will change placed furniture appearance, and it does not prove
custom asset import.

## Capability status

`experimental`: donor field discovery is verified for this session;
visual-resource substitution remains research-only.

The first multi-family graph probe started in EML but emitted no family
markers after the loader announced the module. This is classified as
`inconclusive`, not as proof that the resource families are absent. The probe
generator now wraps each `get_resources_by_type` call independently and logs a
`TYPE_ERROR` so unsupported or build-specific type names cannot suppress the
remaining scans.

A fresh regenerated run still reached the loader's `Running mod` event but
emitted no probe records. This is recorded as a second `inconclusive` result:
the multi-family probe needs to be reduced to a minimal single-family probe or
validated with an EML-compatible Lua syntax/runtime harness before further live
testing.

## Static KFC relationship

KFC inspection found the model GUID in a `TemplateResource` under a
`keen::ecs::ModelResource` component:

- Component field: `model`
- Referenced model GUID: `4c7f1c3a-b448-4460-ad5e-a79b3859d2c1`

The targeted relationship extractor resolved the exact edge:

```text
TemplateResource/9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5_39768775_0.json
  components[23].$value.model
    -> guid:4c7f1c3a-b448-4460-ad5e-a79b3859d2c1
```

This is the first concrete donor-to-placed-model edge. A future visual
replacement may need to clone or patch that `TemplateResource` graph while
preserving its gameplay components.

The read-only template inventory reports **34 components**. Relevant groups
include `ModelComponent`, `ModelRenderHint`, `ModelResource`,
`ColliderResourceComponent`, `Comfort`, `ComfortProvider`, `Health`, and
interaction components. This establishes a donor baseline that future
candidate verification must preserve.

A single-resource runtime probe for the extracted `TemplateResource` GUID
`9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5` was recognized by the loader but emitted
no result marker. It is therefore currently `inconclusive`: the extracted
template identifier may not be the runtime resource identity, or this resource
family may not be exposed through `get_resources_by_type` on this build.
