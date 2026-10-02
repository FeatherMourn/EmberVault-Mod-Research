# Interaction probe contract — 2026-09-27

The Control Center now generates `control_center.interaction_probe.v1`
contracts through `tools/report_gameplay_feasibility.py`.

## Scope

The contract is a read-only observation plan for an existing donor interaction:

- resolve the donor interaction resource;
- confirm the interaction key appears in the donor graph;
- observe a single-player invocation and read back its effect;
- record the persistence boundary;
- keep multiplayer authority as a separate unknown.

Every generated contract sets `runtime_mutation: false` and `state:
research-only`. It does not claim that a new interaction can be authored, that
the effect persists, or that a client can control server-owned behavior.

## Promotion requirements

An interaction cannot move beyond research-only until a same-build result
records donor preservation, single-player behavior, persistence behavior, and a
separate authority assessment. A multiplayer result must not be inferred from
single-player readback.

## Reproduction

```text
python tools/report_gameplay_feasibility.py \
  --interaction-guid <donor-resource-guid> \
  --interaction-key <existing-key> \
  --expected-effect <description>
```

The implementation is covered by `tests/test_gameplay_feasibility.py` and the
full 364-test milestone gate.
