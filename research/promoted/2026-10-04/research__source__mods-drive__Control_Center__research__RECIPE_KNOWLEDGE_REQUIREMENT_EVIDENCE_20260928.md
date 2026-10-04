# Knowledge-requirement evidence — 2026-09-28

The first result was a helper omission: `knowledgeRequirement` was not included in the bounded clone field list. After correcting that, the same furniture donor’s cloned recipe accepted a guarded `knowledgeRequirement = nil` edit. Duration, input, output, workshop, and required-property edits continued to succeed in the same session.

The follow-up replacement probe then copied the populated query from recipe
`1335314663` onto clone recipe `3987654822`. The fresh session logged
`knowledgeRequirement_replace|ok=true|value=1335314663`, and the clone reached
registration without a panic. This proves assignment acceptance, not catalog
unlock behavior or craftability.

Catalog unlock behavior, crafting completion, and save persistence remain
unverified.
