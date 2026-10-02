# Experiment index

Experiments are evidence-producing activities. A canonical finding should link to the experiment records that support it, and an experiment should state whether it was offline/static, synthetic/staging, or live/runtime.

## Experiment classes

- **Offline/static** — reads on-disk executables, reflection caches, KFC/data bundles, or source. No game process access.
- **Synthetic/staging** — tests planners, validators, byte transactions, or disabled packages against controlled fixtures. Not game evidence.
- **Live/runtime** — attaches to or changes a running game/server. Requires exact build identity, explicit safety gates, and a reversible test plan.

## Current evidence posture

The corpus contains extensive offline/static work and synthetic/staging infrastructure. Runtime conclusions are much narrower and must not be inferred from static maps or harness tests. The current hook-safety record documents why several apparently promising sites remain disqualified.

## Required experiment metadata

Every new experiment should record:

- exact game/build and executable or bundle hash
- class: offline/static, synthetic/staging, or live/runtime
- safety actions and what was explicitly not touched
- input artifacts and tool version
- expected result and observed result
- produced artifacts and hashes
- conclusion, confidence, and next experiment
