# Visual candidate generation evidence — 2026-09-27

The hardened visual-candidate generator processed the descriptive template
fixture `research/staging/visual_candidate_159b_template_variant_1076226.json`.

Output:

- `research/probes/visual_candidate_159b_generated_20260927`
- target build: `1076226`
- embedded candidate GUID: `9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5`
- dependency count: `1`
- runtime mutation: `false`
- feature state: `research-only`

The generator validates the embedded resource GUID, records the candidate
SHA-256, and emits a read-only probe manifest. This proves safe offline
candidate packaging only; it does not prove engine-side import or rendered
in-game substitution.
