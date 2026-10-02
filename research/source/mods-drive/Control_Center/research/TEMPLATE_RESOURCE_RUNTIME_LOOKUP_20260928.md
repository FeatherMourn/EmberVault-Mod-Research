# TemplateResource runtime lookup boundary

Date: 2026-09-28  
Build: `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`

A fresh read-only single-resource probe queried:

- type: `keen::TemplateResource`
- GUID: `9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5`

The loader announced the module and the game remained running, but no
`[CC-SINGLE-RESOURCE]` result marker was emitted. No panic or loader error was
observed. The probe was removed after the session.

## Interpretation

This is **inconclusive**, not proof that the resource is absent. The extracted
KFC identifier may not equal the runtime resource identity, or this resource
family may not be exposed through `get_resources_by_type` on this build. The
next viable routes are a runtime identity trace from a known `ItemInfo` graph
or a loader-side API that exposes dependency metadata without requiring direct
TemplateResource enumeration.
