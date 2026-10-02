# Custom icon import route — research result

The EML source tree contains the missing primitives for a real custom icon:

1. `io.read(path)` loads PNG bytes.
2. `image.decode(buffer)` creates an RGBA image.
3. `image.encode_texture(image, "R8G8B8A8_unorm")` creates GPU texture bytes.
4. `game.assets.create_content(buffer)` creates immutable content with a new content hash.
5. A cloned `keen::UiTextureResource` receives that content, dimensions, format, and type.
6. The cloned `ItemInfo.iconImage` receives the new texture resource GUID.

The reusable Lua helper now exposes this as `import_png_icon`. It is deliberately
research-only: the source and API route are verified, but the game still needs a
live fixture proving that a generated icon is rendered in the catalog and remains
stable after restart. The donor-only icon path remains the rollback baseline.

## Build-specific cautions

- The reflected resource uses `size.x` and `size.y`; it does not use the stale
  `width`/`height` names shown in older EML documentation examples.
- `R8G8B8A8_unorm` is the first target because it avoids BC7 compression while
  validating the complete content-reference path.
- Content assets are immutable. Replacing an imported icon requires a new
  content asset and a new resource reference.
- The helper must not be enabled in a production package until live rendering,
  restart behavior, and rollback are verified.
