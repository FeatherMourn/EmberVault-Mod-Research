# TemplateResource GUID lookup boundary — 2026-09-27

The EML documentation-supported exact lookup was tested:

`game.assets.get_resource("9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5", "keen::TemplateResource", 0)`

Observed output stopped after:

```text
BEGIN|9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5
```

No return, missing result, or error marker followed. Combined with the two
`get_resources_by_type` tests, both documented resource-access routes are
currently non-returning for TemplateResource on build `1076226`.

The test was isolated, read-only, and fully rolled back. This is evidence of
an EML/runtime boundary, not proof that the static resource or graph is absent.
Placed-model substitution therefore remains research-only pending a loader
API fix, alternate typed access path, or a different runtime identity.
