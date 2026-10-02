# EML texture mutation API boundary — build 1076226

## Newly confirmed API surface

The checked-in EML Lua definitions expose a potentially useful content path:

- `AssetManager.get_content(guid)` returns raw asset content.
- `Content:read_data()` returns a read-only binary buffer.
- `image.decode` and `image.encode` support ordinary image formats.
- `image.decode_texture` and `image.encode_texture` support typed pixel formats.
- `Image:set_pixel` and `Image:set_pixel_packed` can mutate decoded pixels.
- `AssetManager.create_content(data)` can create new raw content.
- `AssetManager.register_resource(value, type, guid, part)` can register a typed resource descriptor.

Source references:

- `H:\enshroudedresearch\external\kfc-parser-source\crates\mod-loader-lua\definitions\assets\manager.lua`
- `H:\enshroudedresearch\external\kfc-parser-source\crates\mod-loader-lua\definitions\assets\content.lua`
- `H:\enshroudedresearch\external\kfc-parser-source\crates\mod-loader-lua\definitions\blob\image.lua`

## What this does and does not prove

This proves that EML has general-purpose raw-image and content primitives. A
prior Blender round-trip runtime record also confirms that custom texture
content can be registered and a custom material can be assigned in a probe.
That record still contains no catalog, item-info, or placed-object screenshot,
so it does not prove that the bed's material graph renders the replacement in
the client.

The existing bed RenderModel references four material GUIDs, but the staged
subset does not contain complete typed material payloads. Direct mutation of
`ItemInfo.color` and direct material assignment have already produced the EML
`panic in a function that cannot unwind` boundary. Therefore this API surface
must remain research-only.

Supporting runtime record:

- `research/probe_sessions/blender_render_model_round_trip_runtime_evidence_20260928.json`

It records `custom_textures_registered` and `custom_material_assigned` as true,
while explicitly leaving client rendering unverified. This distinction is
important: resource creation is now an experimental capability, not yet a
working recolor feature.

## Next bounded probe

Use a disposable external game copy and a fresh EML session to:

1. Read one known donor content GUID without writing it.
2. Decode only if the content is a supported image payload.
3. Change one pixel in memory and encode a new content blob.
4. Register the new content without changing any vanilla descriptor.
5. Attach it only through a donor-preserving visual candidate, if a complete
   typed material/texture descriptor is available.
6. Stop on any panic, remove the probe transactionally, and retain the stable
   profile.

No catalog, placement, persistence, or material-rendering claim may be made
until screenshots and a fresh log prove those behaviors independently.
