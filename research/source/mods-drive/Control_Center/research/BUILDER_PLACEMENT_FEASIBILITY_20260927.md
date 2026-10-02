# Builder placement feasibility — 2026-09-27

The Control Center builder is verified for offline catalog search, favorites,
material totals, and portable build plans. In-game placement assistance is a
separate research capability.

The reusable contract is emitted by:

```text
python tools/report_gameplay_feasibility.py --builder-item-id 2940001508 --builder-plan "castle beds"
```

The contract is `control_center.builder_placement_probe.v1` and is explicitly:

- `research-only`;
- `runtime_mutation: false`;
- authority: `unknown`.

It permits research into catalog resolution, placement templates, snap data,
and offline preview transforms. It does not claim that EML can place objects,
persist placements, or satisfy server authority. Promotion requires same-build
preview evidence, an authority-boundary record, persistence evidence, and
rollback verification.
