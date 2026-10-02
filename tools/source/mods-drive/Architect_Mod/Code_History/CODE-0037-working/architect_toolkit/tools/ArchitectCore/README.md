# ArchitectCore (offline)

`ArchitectCore` validates and queries the machine-readable vanilla adapter
map and feature dependency graph. It has no process, Enshrouded, DLL, bridge
command, or mutation dependency.

```python
from tools.ArchitectCore import ArchitectCoreQuery
q = ArchitectCoreQuery.from_files(
    "bridge/vanilla_capability_map.json",
    "bridge/feature_dependency_graph.json",
)
proven = q.proven()
blocked = q.features_blocked_by("build.resolve_blueprint")
```

The validator rejects duplicate IDs, invalid status values, unknown
dependencies, cycles, unknown capability references, and use of a disproven
capability without an explicit override.

`ArchitectTargetObservation` and `TargetProvenance` provide the optional,
game-independent target contract. They carry explicit provenance and bounded
confidence; they do not acquire targets or access process memory.
