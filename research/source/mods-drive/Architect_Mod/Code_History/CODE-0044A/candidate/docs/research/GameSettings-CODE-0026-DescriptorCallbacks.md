# CODE-0026 — Descriptor-owned callback recovery

## Conclusion

`NO_DESCRIPTOR_CONVERGENCE`

The exact non-DS generated registration objects for reflection indices 2703
and 3410 were recovered with relocation-aware PE analysis. Neither object owns
a relocation into `.text`; therefore neither exposes a descriptor-owned code
pointer to follow. No hook was added and GameSettings mutation remains blocked.

The analyzed executable is revision 1076226, SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`,
PE timestamp `0x6A4236C8`, image size `0x02DA7000`.

No Ghidra, IDA, Binary Ninja, or Rizin installation was present. The equivalent
analysis used the PE base-relocation directory, section-aware target
classification, exact generated-object layout validation, and bounded string
decoding. It did not repeat CODE-0025's broad graph traversal.

## Index 2703 — AdminChangeGameSettingsAction

- Object: `[0x198F520, 0x198F5D0)`
- Object size: `0xB0`
- Payload size encoded at object `+0x40`: `0x98`
- Internal hash at `+0x54`: `0x9919D92D`
- Qualified-name slot `+0x20` resolves to
  `keen::ecs::AdminChangeGameSettingsAction`
- Direct code relocations: **0**

| Slot | Relocation | Target RVA | Classification |
|---:|---|---:|---|
| `+0x00` | `IMAGE_REL_BASED_DIR64` | `0x13FE310` | type name metadata |
| `+0x10` | `IMAGE_REL_BASED_DIR64` | `0x1C3C468` | impact-name metadata |
| `+0x20` | `IMAGE_REL_BASED_DIR64` | `0x1C3C4C8` | qualified-name metadata |
| `+0x30` | `IMAGE_REL_BASED_DIR64` | `0x18AF5E8` | type metadata, exact role unresolved |
| `+0x58` | `IMAGE_REL_BASED_DIR64` | `0x198ED70` | field/type metadata |
| `+0x70` | `IMAGE_REL_BASED_DIR64` | `0x198EFC8` | field/type metadata |

Three code relocations immediately before the object, at RVAs `0x198F500`,
`0x198F508`, and `0x198F510`, target `0x11A8EF0`, `0x11A9640`, and
`0x11A9960`. Object-boundary recovery excludes these slots: they belong to the
preceding generated descriptor. Their first functions initialize/copy much
smaller unrelated objects, which independently contradicts ownership by the
`0x98` action descriptor. They are not callback candidates for index 2703.

## Index 3410 — GameSettingsChangedEvent

- Object: `[0x18CBCA0, 0x18CBD50)`
- Object size: `0xB0`
- Payload size encoded at object `+0x40`: `0x98`
- Internal hash at `+0x54`: `0x81B10CBB`
- Qualified-name slot `+0x20` resolves to
  `keen::ecs::GameSettingsChangedEvent`
- Direct code relocations: **0**

| Slot | Relocation | Target RVA | Classification |
|---:|---|---:|---|
| `+0x00` | `IMAGE_REL_BASED_DIR64` | `0x1C07708` | type name metadata |
| `+0x10` | `IMAGE_REL_BASED_DIR64` | `0x1C077B8` | impact-name metadata |
| `+0x20` | `IMAGE_REL_BASED_DIR64` | `0x1C07860` | qualified-name metadata |
| `+0x30` | `IMAGE_REL_BASED_DIR64` | `0x18AF5E8` | type metadata, exact role unresolved |
| `+0x38` | `IMAGE_REL_BASED_DIR64` | `0x16A13F0` | type/base metadata, exact role unresolved |
| `+0x58` | `IMAGE_REL_BASED_DIR64` | `0x18CAE20` | field/type metadata |
| `+0x70` | `IMAGE_REL_BASED_DIR64` | `0x18CBA28` | field/type metadata |

The recovered object has no constructor, destructor, serializer, deserializer,
producer, dispatcher, handler, subscriber, vtable, or other code slot directly
owned by it. Data pointers must not be reclassified as callbacks merely because
downstream metadata may eventually participate in generic reflection code.

## Callback candidate table

There are no descriptor-owned callback candidates. Consequently there is no
candidate RVA, function signature, pseudocode, argument interpretation,
caller/callee graph, side classification, or relocatable overwrite span to
report. The empty `callbackCandidates` arrays in the JSON are an evidence
result, not missing analysis.

## Safety and remaining blocker

No candidate meets the runtime-hook rule. A dispatch boundary and independent
readback/event/owner boundary both remain unresolved. Authority cannot be
inferred from registration membership. GameSettings mutation remains blocked.

The next discriminating static step must follow the field/type metadata objects
at the exact owned slots while retaining object ownership, then identify where
the generic registry consumes those objects. That is a new metadata-consumer
task; recursively following every pointer would repeat the rejected broad
CODE-0025 traversal.
