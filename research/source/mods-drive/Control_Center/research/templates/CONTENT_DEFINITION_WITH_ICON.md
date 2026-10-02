# Structured content definition with an icon

Copy `content_definition_with_icon.json`, place the PNG at the path named by
`icon`, and compile it from Content Studio with **Compile Definition**.

The compiler creates a research-only project, assigns a stable content identity,
imports and hashes the PNG under `assets/icons/`, and validates the resulting
package. The icon is not automatically promoted to a live game resource:
runtime `UiTextureResource` registration and visible catalog rendering still
require the build-specific EML research workflow.

When `icon_resource_type`, `icon_field`, and optionally `icon_resource_id` are
present, the compiler also records the intended asset consumer in
`assets.json`. This is a reference plan, not an assertion that the game has
accepted the field assignment.
