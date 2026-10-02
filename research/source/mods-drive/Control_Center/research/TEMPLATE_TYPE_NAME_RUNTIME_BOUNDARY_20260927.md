# TemplateResource runtime type boundary — 2026-09-27

A minimal read-only probe tested `game.assets.get_resources_by_type` with the
unqualified type name `TemplateResource`.

Observed log sequence:

```text
BEGIN|TemplateResource
```

No `CALL`, `SCAN`, `END`, or error marker followed. The game remained
responsive during observation and the isolated profile was restored afterward.

Combined with the earlier qualified-name attempt, this shows that both
`keen::TemplateResource` and `TemplateResource` currently cross a runtime API
boundary that does not return to Lua on this build. It does not prove that
TemplateResource resources are absent or impossible to patch; it means the
current enumeration API is unsuitable for this family. Static graph planning
remains valid, while runtime placed-model substitution is unsupported by the
current probe route and remains research-only.
