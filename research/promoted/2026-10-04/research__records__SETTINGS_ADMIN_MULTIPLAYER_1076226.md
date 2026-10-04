# Settings, administration, and multiplayer boundaries — revision 1076226

- Topic: game settings / admin / backend / multiplayer
- Status: confirmed static model; runtime mutation and readback unresolved
- Confidence: high for reflected layouts and backend safety decisions; low for unsupported runtime adapters
- Build: revision `1076226`
- Executable SHA-256: `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`

## Supported conclusions

The build contains a reflected aggregate `GameSettings` model, a purpose-named `AdminChangeGameSettingsAction`, a server-consumed action slot, a `GameSettingsChangedEvent`, and a presets resource. Their layouts and several versioned fields are statically supported. The dispatch boundary, authoritative readback producer/subscriber, live owner, and safe mutation adapter were not recovered.

The backend architecture therefore fails closed: no guessed native-memory target, object resolver, or hook is registered. Multiplayer families are represented as intended `VANILLA_ACTION` mechanisms rather than being falsely presented as supported native controls. GameSettings remains `NONE`/unavailable until a concrete safe boundary is proven.

## Runtime capability boundary

The research records restricted Lua/EML capabilities such as resource lookup/creation, protected `require`, controlled host I/O, and logging. It does not establish LuaJIT/FFI, arbitrary filesystem access, native DLL exports, callback registration, or general memory access. Absence of observed use is recorded as unresolved, not proof of impossibility.

## Evidence

- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/GameSettings-CODE-0023-Static.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/GameSettings-CODE-0024-Dispatch-Readback.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/GameSettings-CODE-0025-DataFlow.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/GameSettings-CODE-0026-DescriptorCallbacks.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/Backend-CODE-0030-NativeMemoryFoundation.md`
- `../source/mods-drive/Architect_Mod/Code_History/CODE-0037-working/architect_toolkit/docs/research/Backend-CODE-0031-LiveBackendFoundation.md`

## Modding implications

Resource-backed and vanilla-action approaches should be investigated before native mutation. A feature may be designed and represented in the backend without being advertised as available. Any future settings or multiplayer feature must specify authority, persistence, readback, revert behavior, failure mode, and exact-build evidence.

## Open questions

- Where is the authoritative settings action submission boundary?
- Which event or state path provides trustworthy readback?
- Which multiplayer operations are genuinely reachable through vanilla actions?
- Which capabilities remain stable across builds and dedicated-server environments?
