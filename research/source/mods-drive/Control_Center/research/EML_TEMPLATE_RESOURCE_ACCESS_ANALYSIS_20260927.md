# EML TemplateResource access analysis — 2026-09-27

Source inspection of the EML Lua asset layer shows:

1. `get_resource` resolves the type through the type registry, constructs a
   `ResourceId`, and calls `AppState::get_resource_info`.
2. `get_resources_by_type` resolves the type, iterates the KFC resource index,
   and creates `Resource` wrappers for each matching entry.
3. Neither path has a timeout, unsupported-descriptor guard, or Lua-visible
   fallback around resource decoding.

Runtime probes show both paths stop after entering the API for the donor
TemplateResource, while ordinary RenderModel and ItemInfo access works. The
current evidence therefore points to a resource-family decoding or reflection
boundary in the loader rather than an incorrect GUID alone.

Recommended loader-side investigation:

- add timing and structured error logging around `get_resource_info` and
  Resource data materialization;
- add a metadata-only lookup that returns GUID/type/part without decoding the
  descriptor;
- make unsupported descriptor decoding return a Lua error instead of blocking
  the mod coroutine;
- test TemplateResource through metadata first, then add typed field access;
- preserve the existing fail-closed behavior for mutation until the read path
  is proven stable.

Status: loader research boundary; no live mutation was performed.
