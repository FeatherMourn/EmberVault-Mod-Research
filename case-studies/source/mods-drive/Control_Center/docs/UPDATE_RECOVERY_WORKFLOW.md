# Update recovery workflow

Control Center treats a changed game or EML build as a migration event. The
recovery planner is deterministic and non-mutating: it first preserves the
stable backup, quarantines research and unknown modules, revalidates resource
schemas, marks old runtime evidence stale, generates migration guidance, and
restores only modules whose declared build constraint matches the observed
build. Fresh runtime evidence is required before previously experimental or
research-only features can be enabled again.

The planner does not claim that a module is compatible merely because its
manifest exists. Missing build constraints are quarantined after an update.
