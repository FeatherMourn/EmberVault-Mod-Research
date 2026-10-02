# Visual candidate Steam-path probe evidence — 2026-09-27

The candidate probe was launched through Steam App ID `1203620` under the
reversible isolated research profile.

Observed EML evidence:

- The mod loader ran `visual_candidate_159b_1076226`.
- All five direct dependency checks returned `true`:
  - candidate RenderModel `159b5f47-aa61-4db9-8e64-06db850de6f6`;
  - four referenced material GUIDs.
- The runtime indexed `12,713` `keen::RenderModel` resources.
- The probe reached `ACTION|read_only_no_visual_mutation`.
- No visual resource was changed and no item assignment was attempted.

This upgrades the candidate from archive-only evidence to runtime discovery
evidence. It still does not prove that EML can register a new RenderModel,
that all packed mesh/texture dependencies are usable for substitution, or
that the candidate renders when assigned to the cloned bed. The profile was
restored after the run and the staged probe was moved out of the live mods
directory.

Classification: `experimental` discovery / `research-only` substitution.
