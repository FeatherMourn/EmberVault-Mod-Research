# EML/KFC4 Research Probe Program

This directory defines read-only probe contracts and collection plans. It does
not contain a launcher and does not authorize runtime execution.

## Collection rules

- Every probe targets one collection purpose and one output schema.
- Every output records game build, EML version, probe version, timestamps, and
  SHA-256 hashes.
- Probes may inspect and export data only; they must not patch, create, delete,
  persist, or modify saves, registries, or game files.
- Unknown types, missing fields, and exceptions are recorded as evidence gaps;
  they must not abort the complete collection run.
- Runtime observations remain build-scoped and are never promoted to static
  or universal claims.

## Execution order

1. Platform/type/API inventory.
2. Resource registry sweep.
3. Resource relationships and references.
4. Mod Research deep dives: KFC4 resources, items, recipes, RenderModels,
   packages, and export behavior.
5. Content Creator donors, recipes, categories, and compatibility metadata.
6. Game Tuning values, progression, costs, and settings.
7. Character Tools progression, equipment, appearance, and restrictions.
8. Mod Manager manifests, capabilities, dependencies, ordering, and conflicts.
9. Save Manager format/version/migration signals (read-only only).
10. Troubleshooter diagnostics, errors, missing resources, and loader state.
11. Control Center module health, permissions, manifests, and integration state.

The broad inventory must complete before targeted probes are authored so probe
queries are based on observed types rather than guesses.

`targeted-probe-plan-20261015.json` defines the downstream module probes and
their evidence boundaries. These are plans, not runtime claims.

`platform_inventory_probe.lua` is the first documented probe template. It uses
only the documented EML resource-type and resource-list APIs and exports a
bounded text inventory under the configured EML export directory. It is not
installed or executed by the research repository.
