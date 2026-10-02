# Visual candidate search — 2026-09-27

The read-only candidate search scanned the extracted RenderModel archive
against the staged bed donor:

research/staging/bed_clone_kfc_subset_1076226/RenderModel/4c7f1c3a-b448-4460-ad5e-a79b3859d2c1_177394c7_0.json

Results:

- 12,713 RenderModel resources inspected.
- 6 candidates matched the donor's observed schema and array lengths exactly.
- The top exact-shape candidates were GUIDs 159b5f47-aa61-4db9-8e64-06db850de6f6,
  4dda7b1d-422a-473c-b9a3-f1a1d9a51716, 84be8359-a38b-4b3d-82b9-33bf486035d1,
  and d54841b4-b165-4558-9907-b528a3d57ab2.

This is structural compatibility only. It does not prove that the candidate's
mesh buffers, materials, textures, registration path, or in-game appearance
are usable. Each candidate must still undergo dependency resolution, typed
resource construction, isolated runtime probing, and fresh-session visual
inspection. The search tool therefore does not authorize live mutation.

The reusable tool is tools/find_visual_candidates.py; it emits the
control_center.visual_candidate_search.v1 report and ranks incomplete graphs
below exact-shape matches.
