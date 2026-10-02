# Research probe manifest safety — 2026-09-27

All Control Center generators that produce EML research probes now emit an
explicit `feature_state: "research-only"` manifest field:

- behavior probes;
- KFC read probes;
- reversible KFC write probes;
- visual candidate probes;
- ItemInfo visual-reference probes.

This is enforced by `tests/test_probe_manifest_safety.py`, preventing future
probe generators from being classified as stable or unclassified by the live
loader preflight. The historical release gate passed with 388 tests; the
current gate passes 456 tests and includes explicit localization-session and installer-source gates.
