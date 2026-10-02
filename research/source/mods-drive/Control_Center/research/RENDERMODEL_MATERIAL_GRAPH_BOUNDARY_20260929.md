# RenderModel Material Graph Boundary — 2026-09-29

The staged bed `keen::RenderModel` exposes four material GUID references in
its `materials[]` array:

- `873f25d2-5adf-456a-82c7-0d8b7ff04f9a`
- `5b22bab9-1d14-49d6-919c-3fc97917b60b`
- `5da22bb4-0b90-40fd-8680-365d2c7e9169`
- `6d9e2209-260c-4bab-9020-c3260a076cb2`

The staged subset does not contain corresponding `RenderMaterialResource`
payloads, and its `modelMaterialDataType` is `Invalid` with an empty
`modelMaterialData` array. Therefore the current fixture is sufficient to
identify material slots but not sufficient to construct a typed replacement
material graph.

The separate direct `ItemInfo.material` assignment probe aborted EML with a
non-unwinding panic. A graph-level replacement must first acquire a complete,
typed material resource and its texture dependencies; inventing a GUID here
would not be a valid experiment.

Classification: research-only, blocked on typed material-resource acquisition;
no stable-profile or live-installation changes were made.
