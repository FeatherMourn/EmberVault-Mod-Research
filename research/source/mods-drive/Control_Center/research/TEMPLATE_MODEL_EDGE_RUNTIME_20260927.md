# Template model-edge runtime probe — 2026-09-27

The minimal `template_model_edge_probe_159b_1076226` was launched through
Steam in the isolated research profile.

Result:

- EML announced the probe as running.
- No `GRAPH_SCAN`, `TEMPLATE`, assignment, or error marker was emitted during
  two observation windows.
- The game process remained responsive and was then closed cleanly.
- The profile was restored and the probe was moved out of the live mods
  directory.

Classification: `inconclusive`.

This does not prove that `keen::TemplateResource` is unavailable. It indicates
that this resource family or the current Lua access pattern needs a narrower
runtime harness, an EML-compatible typed lookup, or a different runtime
identity before a placed-model substitution can be tested. The static
donor-preserving graph candidate remains valid, but runtime placed appearance
is still unverified.
